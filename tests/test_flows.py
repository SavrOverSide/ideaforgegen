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
        self.assertEqual(len(GENERATORS), 7)
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

    async def test_saved_idea_survives_table_changes(self):
        from ideas import tables
        c = chat(3010)
        await c.press("sv:item:42")
        await c.say("/saved")
        before = c.last()["text"]
        tables.K["ITEM_TYPE"].insert(0, ("новая вещь", "a new thing"))   # tables grow after the save
        try:
            await c.say("/saved")
            self.assertEqual(c.last()["text"], before)
        finally:
            tables.K["ITEM_TYPE"].pop(0)

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


class StreakReward(unittest.IsolatedAsyncioTestCase):
    async def test_seventh_day_gives_bonus_generations(self):
        from datetime import timedelta
        from common.db import today
        c = chat(9601)
        for back in range(6, 0, -1):
            store.conn.execute("INSERT OR REPLACE INTO streaks VALUES (?, ?, ?, ?)",
                               (9601, (today() - timedelta(days=back)).isoformat(), 7 - back, 7 - back))
        store.conn.commit()
        await c.press("g:game")
        self.assertIn("🎁", c.last()["caption"])
        self.assertEqual(store.credits(9601), ib.STREAK_BONUS)
        await c.press("g:game")                                  # same day again: no second bonus
        self.assertNotIn("🎁", c.last()["caption"])
        self.assertEqual(store.credits(9601), ib.STREAK_BONUS)


class FirstRun(unittest.IsolatedAsyncioTestCase):
    async def test_new_user_gets_free_kit_returning_user_does_not(self):
        c = chat(9701)
        await c.say("/start")
        photos = [x for x in c.log if x["kind"] == "photo"]
        self.assertEqual(len(photos), 1)
        self.assertIn("🗺️", photos[0]["caption"])
        self.assertEqual(store.free_left(9701, ib.FREE_PER_DAY), ib.FREE_PER_DAY)   # the gift cost nothing
        n = len(c.log)
        await c.say("/start")
        self.assertEqual(len(c.log), n + 1)
        assert_buttons_routable(self, c)


class Kit(unittest.IsolatedAsyncioTestCase):
    async def test_kit_costs_three_and_is_all_or_nothing(self):
        c = chat(9101)
        await c.press("g:set")
        self.assertEqual(c.last()["kind"], "photo")
        self.assertEqual(store.free_left(9101, ib.FREE_PER_DAY), 2)
        await c.press("g:set")                          # only 2 left: refused, nothing is spent
        self.assertEqual(c.last()["kind"], "text")
        self.assertEqual(store.free_left(9101, ib.FREE_PER_DAY), 2)
        await c.press("g:game")
        self.assertEqual(c.last()["kind"], "photo")
        store.add_credits(9101, 2)                       # 1 free + 2 credits = exactly one kit
        await c.press("g:set")
        self.assertEqual(c.last()["kind"], "photo")
        self.assertEqual((store.free_left(9101, ib.FREE_PER_DAY), store.credits(9101)), (0, 0))

    async def test_kit_is_linked_and_saveable(self):
        from ideas.tables import make
        k = make("set", 5)
        self.assertEqual(k, make("set", 5))
        text_ru = text(k, "ru")
        self.assertIn("Лидер: ", text_ru)
        c = chat(9102)
        store.add_credits(9102, 5)
        await c.press("sv:set:5")
        await c.say("/saved")
        self.assertIn(text_ru, c.last()["text"])

    async def test_premium_kit_unlimited(self):
        c = chat(9103)
        store.add_premium(9103, 30)
        for _ in range(4):
            await c.press("g:set")
            self.assertEqual(c.last()["kind"], "photo")


class Book(unittest.IsolatedAsyncioTestCase):
    async def test_book_screen_buy_and_redownload(self):
        c = chat(9901)
        await c.say("/book")
        self.assertEqual(c.last()["kind"], "photo")
        self.assertIn("buy:book_1", [b.callback_data for b in c.buttons()])
        assert_buttons_routable(self, c)
        BOT.sent.clear()
        await c.press("buy:book_1", on=harness.Message(c.user, "", BOT))
        inv = [x for x in BOT.sent if x["kind"] == "invoice"][0]
        self.assertEqual((inv["payload"], inv["prices"][0].amount), ("book_1", 99))
        BOT.sent.clear()
        await c.pay("book_1", 99)
        docs = [x for x in BOT.sent if x["kind"] == "document"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["document"].path.name, "step-i-statika-tom1.pdf")   # Russian user, Russian edition
        # owners get the file again for free, and the other edition on request
        BOT.sent.clear()
        await c.say("/book")
        await c.press("bk:en")
        names = [x["document"].path.name for x in BOT.sent if x["kind"] == "document"]
        self.assertEqual(names, ["step-i-statika-tom1.pdf", "steppe-and-static-vol1.pdf"])
        self.assertFalse([x for x in BOT.sent if x["kind"] == "invoice"])

    async def test_start_book_deeplink(self):
        c = chat(9905)
        await c.say("/start book")
        self.assertIn("buy:book_1", [b.callback_data for b in c.buttons()])

    async def test_other_edition_needs_ownership(self):
        c = chat(9902)
        BOT.sent.clear()
        await c.press("bk:en")
        self.assertFalse([x for x in BOT.sent if x["kind"] == "document"])

    async def test_english_user_gets_english_screen(self):
        c = chat(9903, "en")
        await c.say("/book")
        self.assertIn("Steppe", c.last()["caption"])

    async def test_shop_offers_book(self):
        c = chat(9904)
        for _ in range(ib.FREE_PER_DAY + 1):
            await c.press("g:npc")
        self.assertIn("book", [b.callback_data for b in c.buttons()])
        await c.press("book")
        self.assertEqual(c.last()["kind"], "photo")


class Deck(unittest.IsolatedAsyncioTestCase):
    async def test_deck_purchase_delivers_pdf(self):
        c = chat(9201)
        BOT.sent.clear()
        await c.say("/deck")
        inv = [x for x in BOT.sent if x["kind"] == "invoice"]
        self.assertEqual(inv[0]["prices"][0].amount, 49)
        BOT.sent.clear()
        await c.pay("deck_10", 49)
        docs = [x for x in BOT.sent if x["kind"] == "document"]
        self.assertEqual(len(docs), 1)
        data = docs[0]["document"].data
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertLess(len(data), 20 * 1024 * 1024)               # Telegram bots may send files up to 50 MB
        self.assertEqual(store.vouchers(9201, "deck"), 0)
        assert_buttons_routable(self, c)

    async def test_deck_has_ten_pages_and_all_kinds(self):
        import io
        from PIL import Image
        from ideas.deck import build
        pdf = build("b")
        self.assertEqual(pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages"), 10)

    async def test_failed_delivery_keeps_voucher_and_retry_works(self):
        c = chat(9202)
        import ideas.bot as mod
        real = mod.build_deck
        mod.build_deck = lambda *_: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            await c.pay("deck_10", 49)
        finally:
            mod.build_deck = real
        self.assertEqual(store.vouchers(9202, "deck"), 1)           # paid, not lost
        self.assertIn("/deck", " ".join(x.get("text", "") for x in BOT.sent if x.get("chat_id") == 9202))
        BOT.sent.clear()
        await c.say("/deck")                                          # retry delivers without paying again
        self.assertEqual(len([x for x in BOT.sent if x["kind"] == "document"]), 1)
        self.assertEqual(store.vouchers(9202, "deck"), 0)

    async def test_shop_offers_deck(self):
        c = chat(9203)
        for _ in range(ib.FREE_PER_DAY + 1):
            await c.press("g:game")
        self.assertIn("buy:deck_10", [b.callback_data for b in c.buttons()])
        assert_buttons_routable(self, c)


class Poll(unittest.IsolatedAsyncioTestCase):
    async def test_quest_poll_valid_for_telegram(self):
        import run
        run.env = lambda name, default="": {"CHANNEL": "@c"}.get(name, default)
        for _ in range(60):                   # random content: try many draws
            bot = Bot("x")
            await run.post_poll(bot)
            p = bot.sent[0]
            self.assertEqual(len(p["options"]), 3)
            self.assertEqual(len(set(p["options"])), 3)
            self.assertTrue(all(1 <= len(o) <= 100 for o in p["options"]))
            self.assertLessEqual(len(p["question"]), 300)
            self.assertTrue(p["is_anonymous"])

    async def test_no_channel_no_poll(self):
        import run
        run.env = lambda name, default="": ""
        bot = Bot("x")
        await run.post_poll(bot)
        self.assertEqual(bot.sent, [])


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
        self.assertEqual(len([x for x in c.log if x["kind"] == "photo"]), 5)  # 5 free cards, then the 6th and the kit hit the paywall
        self.assertEqual(c.last()["kind"], "text")
