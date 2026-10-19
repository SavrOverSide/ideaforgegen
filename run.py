"""Runs the Lore Forge bot and posts a free idea to CHANNEL every evening."""
import asyncio
import logging
import random

from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common.config import env
from common.daily import every_day
from ideas.bot import router
from ideas.tables import GENERATORS


async def post_idea(bot: Bot) -> None:
    channel = env("CHANNEL")
    if not channel:
        return
    me = await bot.get_me()
    kind = random.choice(list(GENERATORS))
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎲 Сгенерировать ещё / More", url=f"https://t.me/{me.username}")
    ]])
    text = f"{GENERATORS[kind]('ru')}\n\n—\n\n{GENERATORS[kind]('en')}"
    await bot.send_message(channel, text, parse_mode="HTML", reply_markup=kb)


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
