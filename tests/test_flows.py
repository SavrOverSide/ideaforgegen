import time
import unittest

from tests import harness  # noqa: F401  (must come first: it puts the fake aiogram on sys.path)
from tests.harness import Chat, assert_buttons_routable
from aiogram import Bot
from ideas import bot as ib
from ideas.tables import GENERATORS, make, text, text_both

store = ib.store
BOT = Bot("x")


def chat(uid, lang="ru"):
    return Chat(ib.router, BOT, uid, lang)


class IdeaForgeFlows(unittest.IsolatedAsyncioTestCase):
    async def test_start_menu_has_all_six_generators(self):
        c = chat(1001)
        await c.say("/start")
        data = [b.callback_data for b in c.buttons()]
        for k in GENERATORS:
            self.assertIn(f"g:{k}", data)
        self.assertEqual(len(GENERATORS), 6)
        assert_buttons_routable(self, c)

    async def test_every_kind_generates_card_with_working_buttons(self):
        c = chat(1002)
        for k in GENERATORS:
            store.add_credits(1002, 1)
            await c.press(f"g:{k}")
            self.assertEqual(c.last()["kind"], "photo", k)
            self.assertGreater(len(c.last()["photo"].data), 20000)
            self.assertLess(len(c.last()["caption"]), 1000)
        assert_buttons_routable(self, c)

    async def test_free_limit_then_paywall_then_pack(self):
        c = chat(1003)
        for _ in range(ib.FREE_PER_DAY):
            await c.press("g:game")
            self.assertEqual(c.last()["kind"], "photo")
        await c.press("g:game")
        self.assertEqual(c.last()["kind"], "text")
        self.assertIn("+5", c.last()["text"])
        assert_buttons_routable(self, c)
        BOT.sent.clear()
        await c.press("buy:pack_50", on=harness.Message(c.user, "", BOT))
        inv = [s for s in BOT.sent if s["kind"] == "invoice"]
        self.assertEqual(inv[0]["prices"][0].amount, 25)
        await c.pay("pack_50", 25)
        self.assertEqual(store.credits(1003), 50)
        await c.press("g:game")
        self.assertEqual(c.last()["kind"], "photo")

    async def test_premium_unlimited(self):
        c = chat(1004)
        await c.pay("premium_30", 149)
        self.assertTrue(store.is_premium(1004))
        for _ in range(ib.FREE_PER_DAY + 3):
            await c.press("g:npc")
            self.assertEqual(c.last()["kind"], "photo")

    async def test_wrong_price_rejected(self):
        c = chat(1005)
        res = await c.pay("premium_30", 1)
        self.assertFalse(res[0])

    async def test_referral_both_sides_and_no_repeat(self):
        a, b = chat(2001), chat(2002)
        await a.say("/start")
        BOT.sent.clear()
        await b.say("/start ref_2001")
        self.assertEqual(store.credits(2001), ib.INVITER_BONUS)
        self.assertEqual(store.credits(2002), ib.INVITEE_BONUS)
        self.assertTrue(any(s["chat_id"] == 2001 for s in BOT.sent))
        await b.say("/start ref_2001")
        await a.say("/start ref_2001")
        self.assertEqual(store.credits(2001), ib.INVITER_BONUS)
        # the bonus makes the 6th generation possible
        for _ in range(ib.FREE_PER_DAY + ib.INVITEE_BONUS):
            await b.press("g:item")
            self.assertEqual(b.last()["kind"], "photo")
        await b.press("g:item")
        self.assertEqual(b.last()["kind"], "text")

    async def test_invite_screen(self):
        c = chat(2010)
        await c.say("/invite")
        self.assertIn("start=ref_2010", c.last()["text"])
        self.assertTrue(any((x.url or "").startswith("https://t.me/share/url") for x in c.buttons()))

    async def test_save_and_list_roundtrip_is_exact(self):
        c = chat(3001)
        await c.press("g:quest")
        sv = next(b.callback_data for b in c.buttons() if b.callback_data.startswith("sv:"))
        _, kind, seed = sv.split(":")
        shown = c.last()["caption"].split("\n\n🔥")[0]
        await c.press(sv)
        self.assertEqual(store.count_saved(3001), 1)
        await c.press(sv)                       # duplicate does nothing
        self.assertEqual(store.count_saved(3001), 1)
        await c.say("/saved")
        self.assertIn(shown, c.last()["text"])  # the same idea comes back, regenerated from its seed

    async def test_saved_limit_and_premium(self):
        c = chat(3002)
        for s in range(ib.FREE_SAVED):
            await c.press(f"sv:game:{s}")
        await c.press("sv:game:999")
        self.assertEqual(store.count_saved(3002), ib.FREE_SAVED)
        store.add_premium(3002, 30)
        await c.press("sv:game:999")
        self.assertEqual(store.count_saved(3002), ib.FREE_SAVED + 1)

    async def test_saved_many_fit_telegram_limit(self):
        c = chat(3003)
        store.add_premium(3003, 30)
        for s in range(20):
            await c.press(f"sv:place:{s}")
        await c.say("/saved")
        sent = [x for x in c.log if x["kind"] == "text"]
        self.assertTrue(all(len(x["text"]) <= 4096 for x in sent))

    async def test_bad_save_payload_ignored(self):
        c = chat(3004)
        await c.press("sv:evil:1")
        await c.press("sv:game:notanumber")
        await c.press("sv:game")
        self.assertEqual(store.count_saved(3004), 0)

    async def test_same_seed_same_idea_and_bilingual(self):
        for k in GENERATORS:
            self.assertEqual(make(k, 5), make(k, 5))
            self.assertNotEqual(text(make(k, 5), "ru"), text(make(k, 5), "en"))
            self.assertLess(len(text_both(make(k, 5))), 900)

    async def test_streak_shown_from_second_day(self):
        c = chat(4001)
        store.conn.execute("INSERT OR REPLACE INTO streaks VALUES (?, ?, ?, ?)", (4001, "2000-01-01", 1, 1))
        await c.press("g:game")
        self.assertNotIn("🔥", c.last()["caption"])   # a broken streak restarts at 1: nothing to brag about

    async def test_sub_lang_stale(self):
        c = chat(5001)
        await c.say("/sub")
        self.assertTrue(store.is_sub(5001))
        await c.say("/lang")
        self.assertEqual(store.get_lang(5001), "en")
        r = await c.press("zzz")
        self.assertEqual(r.handler.__name__, "stale_button")
        d = chat(5002)
        await d.say("/start sub")
        self.assertTrue(store.is_sub(5002))

    async def test_texts_match_between_languages(self):
        self.assertEqual(set(ib.T["ru"]), set(ib.T["en"]))
        self.assertEqual(set(ib.T["ru"]["kinds"]), set(GENERATORS))


class DailyPost(unittest.IsolatedAsyncioTestCase):
    async def test_post_to_channel_and_dms(self):
        import run
        run.env = lambda name, default="": {"CHANNEL": "@c"}.get(name, default)
        for uid in (6001, 6002, 6003):
            store.ensure_user(uid)
            store.set_sub(uid, True)
        store.set_lang(6002, "en")
        bot = Bot("x")
        bot.fail_for = {6003}
        await run.post_idea(bot)
        targets = [s["chat_id"] for s in bot.sent if s["kind"] == "photo"]
        self.assertIn("@c", targets)
        self.assertIn(6001, targets)
        self.assertNotIn(6003, targets)
        self.assertFalse(store.is_sub(6003))
        chan = next(s for s in bot.sent if s["chat_id"] == "@c")
        self.assertLessEqual(len(chan["caption"]), 1000)
        self.assertIn("@wordlores", chan["caption"])


if __name__ == "__main__":
    unittest.main()


class Profile(unittest.IsolatedAsyncioTestCase):
    async def test_menu_commands_are_real_and_kind_commands_generate(self):
        from common.profile import setup_profile
        from ideas.profile import COMMANDS, DESCRIPTION, SHORT
        bot = Bot("x")
        await setup_profile(bot, COMMANDS, DESCRIPTION, SHORT)
        self.assertEqual({p[1] for p in bot.profile}, {None, "en", "ru"})
        self.assertEqual({c for c, _ in COMMANDS["ru"]}, {c for c, _ in COMMANDS["en"]})
        for c, _ in COMMANDS["ru"]:
            m = harness.Message(harness.User(88), f"/{c}", Bot("x"))
            self.assertIsNotNone(await ib.router.feed("message", m), c)
        c = chat(8801)
        for k in GENERATORS:
            await c.say(f"/{k}")
        self.assertEqual(len([x for x in c.log if x["kind"] == "photo"]), 5)  # 5 free, the 6th hit the paywall
        self.assertEqual(c.last()["kind"], "text")
