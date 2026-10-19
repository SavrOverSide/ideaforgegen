"""Ideas bot: game ideas, NPCs and factions for devs and tabletop GMs. Extra generations are sold for Stars."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from common.config import lang_of
from common.db import Store
from common.stars import payments_router, send_invoice
from .tables import GENERATORS

FREE_PER_DAY = 5
PRODUCTS = {"pack_50": 25, "premium_30": 149}  # payload -> Stars

store = Store("ideas")
router = Router()

T = {
    "ru": {
        "start": "Генерирую идеи для игр и НРИ. Бесплатно {free} в день.\n\nВыбери, что сгенерировать:",
        "buttons": {"game": "🎮 Игра", "npc": "🧙 Персонаж", "faction": "⚔️ Фракция"},
        "limit": "Бесплатные генерации на сегодня закончились.",
        "buy_pack": "+50 генераций · {p} ⭐", "buy_premium": "Безлимит на 30 дней · {p} ⭐",
        "pack_title": "50 генераций", "pack_desc": "50 дополнительных генераций без срока",
        "premium_title": "Безлимит на 30 дней", "premium_desc": "Неограниченные генерации 30 дней",
        "paid": "Спасибо! Покупка зачислена.", "more": "Ещё",
        "balance": "Осталось купленных генераций: {n}",
    },
    "en": {
        "start": "I generate ideas for games and tabletop RPGs. {free} free per day.\n\nPick a generator:",
        "buttons": {"game": "🎮 Game", "npc": "🧙 Character", "faction": "⚔️ Faction"},
        "limit": "You've used today's free generations.",
        "buy_pack": "+50 generations · {p} ⭐", "buy_premium": "Unlimited 30 days · {p} ⭐",
        "pack_title": "50 generations", "pack_desc": "50 extra generations, no expiry",
        "premium_title": "Unlimited, 30 days", "premium_desc": "Unlimited generations for 30 days",
        "paid": "Thank you! Your purchase is active.", "more": "More",
        "balance": "Bought generations left: {n}",
    },
}


def menu(lang: str) -> InlineKeyboardMarkup:
    b = T[lang]["buttons"]
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=b[k], callback_data=f"g:{k}") for k in b]])


def shop(lang: str) -> InlineKeyboardMarkup:
    t = T[lang]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["buy_pack"].format(p=PRODUCTS["pack_50"]), callback_data="buy:pack_50")],
        [InlineKeyboardButton(text=t["buy_premium"].format(p=PRODUCTS["premium_30"]), callback_data="buy:premium_30")],
    ])


@router.message(CommandStart())
async def start(m: Message):
    lang = lang_of(m.from_user)
    await m.answer(T[lang]["start"].format(free=FREE_PER_DAY), reply_markup=menu(lang))


@router.message(Command("buy"))
async def buy_cmd(m: Message):
    lang = lang_of(m.from_user)
    await m.answer(T[lang]["balance"].format(n=store.credits(m.from_user.id)), reply_markup=shop(lang))


@router.callback_query(F.data.startswith("g:"))
async def generate(c: CallbackQuery):
    lang = lang_of(c.from_user)
    kind = c.data[2:]
    if kind not in GENERATORS:
        return await c.answer()
    if not store.take(c.from_user.id, FREE_PER_DAY):
        await c.message.answer(T[lang]["limit"], reply_markup=shop(lang))
        return await c.answer()
    await c.message.answer(GENERATORS[kind](lang), parse_mode="HTML", reply_markup=menu(lang))
    await c.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    lang, key = lang_of(c.from_user), c.data[4:]
    if key not in PRODUCTS:
        return await c.answer()
    t = T[lang]
    kind = "pack" if key == "pack_50" else "premium"
    await send_invoice(c.bot, c.message.chat.id, t[f"{kind}_title"], t[f"{kind}_desc"], key, PRODUCTS[key])
    await c.answer()


def on_paid(uid: int, payload: str) -> str:
    if payload == "pack_50":
        store.add_credits(uid, 50)
    else:
        store.add_premium(uid, 30)
    return f"{T['ru']['paid']}\n{T['en']['paid']}"


router.include_router(payments_router(store, PRODUCTS, on_paid))
