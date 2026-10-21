"""Runs the IdeaForge bot; every evening posts an idea to CHANNEL and to DM subscribers."""
import asyncio
import logging
import random

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from common.config import env
from common.daily import every_day
from common.profile import setup_profile
from common.growth import broadcast, promo, ref_link, share_url
from ideas.bot import T, router, store
from ideas.card import render
from ideas.profile import COMMANDS, DESCRIPTION, SHORT
from ideas.tables import GENERATORS, make, text, text_both


async def post_idea(bot: Bot) -> None:
    me = await bot.get_me()
    kind = random.choice(list(GENERATORS))
    idea = make(kind)
    photo = BufferedInputFile(await asyncio.to_thread(render, idea, me.username), filename=f"{kind}.jpg")

    channel = env("CHANNEL")
    if channel:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Сгенерировать ещё / More", url=f"https://t.me/{me.username}")],
            [InlineKeyboardButton(text="🔔 Идея дня в личку / Daily DM", url=f"https://t.me/{me.username}?start=sub")],
        ])
        try:
            await bot.send_photo(channel, photo, caption=f"{text_both(idea)}\n\n{promo('ideas')}"[:1000], parse_mode="HTML", reply_markup=kb)
        except Exception:
            logging.exception("channel post failed")

    async def send_dm(uid: int) -> None:
        lg = store.get_lang(uid) or "ru"
        t = T[lg]
        link = ref_link(me.username, uid)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["again"], callback_data=f"g:{kind}"),
             InlineKeyboardButton(text=t["save"], callback_data=f"sv:{kind}:{idea['seed']}")],
            [InlineKeyboardButton(text=t["share"], url=share_url(link, t["share_text"]))],
        ])
        await bot.send_photo(uid, BufferedInputFile(photo.data, filename=f"{kind}.jpg"), caption=text(idea, lg)[:1000],
                             parse_mode="HTML", reply_markup=kb)

    dead = await broadcast(store.subs(), send_dm)
    for uid in dead:
        store.set_sub(uid, False)
    logging.info("daily DM: %s dropped", len(dead))


def clip(text: str, n: int = 100) -> str:
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


async def post_poll(bot: Bot) -> None:
    """Midday vote in the channel: three quests, which one would you take? Cheap to answer, so people do."""
    channel = env("CHANNEL")
    if not channel:
        return
    me = await bot.get_me()
    quests = [make("quest") for _ in range(3)]
    options = [clip(q["rows"][1][1][0]) for q in quests]  # the task line, Russian
    while len(set(options)) < 3:  # three different tasks, please
        quests = [make("quest") for _ in range(3)]
        options = [clip(q["rows"][1][1][0]) for q in quests]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎲 Сгенерировать свой квест", url=f"https://t.me/{me.username}")]])
    await bot.send_poll(channel, question="Три квеста на выбор. За какой возьмёшься?", options=[o[0].upper() + o[1:] for o in options],
                        is_anonymous=True, reply_markup=kb)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(env("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await setup_profile(bot, COMMANDS, DESCRIPTION, SHORT)
    await asyncio.gather(
        dp.start_polling(bot),
        every_day(env("POST_TIME", "19:00"), lambda: post_idea(bot)),
        every_day(env("POLL_TIME", "13:00"), lambda: post_poll(bot)),
    )


if __name__ == "__main__":
    asyncio.run(main())
