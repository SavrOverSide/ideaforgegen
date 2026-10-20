"""Runs the IdeaForge bot; every evening posts an idea to CHANNEL and to DM subscribers."""
import asyncio
import logging
import random

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from common.config import env
from common.daily import every_day
from common.growth import broadcast, promo, ref_link, share_url
from ideas.bot import T, router, store
from ideas.card import render
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


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(env("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await asyncio.gather(
        dp.start_polling(bot),
        every_day(env("POST_TIME", "19:00"), lambda: post_idea(bot)),
    )


if __name__ == "__main__":
    asyncio.run(main())
