"""Real-aiogram smoke run for IdeaForge (see tests/real_aiogram.py)."""
import asyncio
import sys

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/tests")

from real_aiogram import Harness  # noqa: E402
from ideas import bot as ib  # noqa: E402

KINDS = ["game", "npc", "faction", "item", "quest", "place", "set"]


async def main():
    h = Harness(ib.router)
    name = lambda calls: [type(c).__name__ for c in calls]
    calls = await h.say(10, "/start")
    for data in [b for b in h.buttons(calls) if b and not b.startswith("http")]:
        if not data.startswith("g:"):
            await h.press(10, data)

    ib.store.add_premium(11, 30)                  # unlimited, so every kind can be tried
    for k in KINDS:
        calls = await h.press(11, f"g:{k}")
        h.expect("SendPhoto" in name(calls), f"{k} card sent")
    save = next(b for b in h.buttons(calls) if b.startswith("sv:"))
    calls = await h.press(11, save)
    h.expect(ib.store.count_saved(11) == 1, "idea saved")
    calls = await h.say(11, "/saved")
    h.expect("SendMessage" in name(calls), "/saved lists ideas")
    for k in KINDS:
        calls = await h.say(11, f"/{k}")
        h.expect("SendPhoto" in name(calls), f"/{k} command")

    # free user: 5 cards, then the shop
    for _ in range(5):
        calls = await h.press(12, "g:npc")
    calls = await h.press(12, "g:npc")
    shop = h.buttons(calls)
    h.expect("buy:pack_50" in shop and "buy:deck_10" in shop and "m:invite" in shop, "limit shows shop and invite")
    calls = await h.press(12, "buy:pack_50")
    h.expect("SendInvoice" in name(calls), "pack invoice")
    calls = await h.pre_checkout(12, "pack_50", 25)
    h.expect(any(type(c).__name__ == "AnswerPreCheckoutQuery" and c.ok for c in calls), "pack pre-checkout ok")
    await h.paid(12, "pack_50", 25)
    h.expect(ib.store.credits(12) == 50, "50 generations granted")

    # PDF deck: buy, the file is built and sent
    calls = await h.say(13, "/deck")
    h.expect("SendInvoice" in name(calls), "deck invoice")
    await h.pre_checkout(13, "deck_10", 49)
    calls = await h.paid(13, "deck_10", 49)
    h.expect("SendDocument" in name(calls), "deck PDF delivered")

    # referral link
    await h.say(20, "/start")
    calls = await h.say(21, "/start ref_20")
    h.expect(ib.store.credits(20) == ib.INVITER_BONUS, "inviter rewarded")
    for cmd in ("/invite", "/sub", "/buy", "/lang", "/help", "/paysupport x"):
        calls = await h.say(22, cmd)
        h.expect(bool(calls), f"{cmd} replies")
    calls = await h.press(22, "old:button")
    h.expect(any(type(c).__name__ == "AnswerCallbackQuery" and c.show_alert for c in calls), "stale button explained")
    h.report()


asyncio.run(main())
