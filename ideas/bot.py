"""IdeaForge bot: ideas, characters, factions, artifacts, quests and locations for game devs and tabletop GMs.

Growth: invite links (+credits both sides), daily streak, saved ideas, daily DM subscription, share button.
Money: Telegram Stars (generation packs, 30-day unlimited).
"""
import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from common.config import lang_of
from common.db import Store
from common.growth import parse_ref, ref_link, share_url, start_arg
from common.stars import payments_router, send_invoice
from .card import render
from .tables import GENERATORS, ICONS, make, text

FREE_PER_DAY = 5
FREE_SAVED = 5
INVITER_BONUS = 5
INVITEE_BONUS = 5
PRODUCTS = {"pack_50": 25, "premium_30": 149}  # payload -> Stars

store = Store("ideas")
router = Router()

T = {
    "ru": {
        "welcome": ("🔥 <b>IdeaForge</b> — кузница идей для геймдева и НРИ.\n\n"
                    "Одно нажатие — и готовая карточка: идея игры, персонаж, фракция, артефакт, квест или локация.\n"
                    "Бесплатно {free} в день. Приведи друга — оба получите +{bonus} генераций.\n\n"
                    "Что куём?"),
        "kinds": {"game": "Игра", "npc": "Персонаж", "faction": "Фракция", "item": "Артефакт", "quest": "Квест", "place": "Локация"},
        "again": "🔄 Ещё", "save": "❤️ В избранное", "share": "📤 Поделиться", "saved_ok": "Сохранено ❤️",
        "saved_dup": "Уже в избранном", "saved_full": "В избранном {n} — это лимит бесплатного тарифа. Премиум снимает его.",
        "streak": "🔥 Серия: {n} дн.",
        "limit": "На сегодня бесплатные генерации закончились.\n\n👥 Пригласи друга — вы оба получите +{bonus}.\n⭐ Или возьми безлимит.",
        "btn_invite": "👥 Пригласить друга", "buy_pack": "+50 генераций · {p} ⭐", "buy_premium": "Безлимит 30 дней · {p} ⭐",
        "pack_title": "50 генераций", "pack_desc": "50 дополнительных генераций без срока",
        "premium_title": "Безлимит на 30 дней", "premium_desc": "Безлимит генераций, безлимитное избранное",
        "paid": "Спасибо! Покупка зачислена ⭐", "balance": "Осталось купленных генераций: {n}\nБесплатных сегодня: {free}",
        "invite": ("👥 <b>Пригласи друзей</b>\n\nЗа каждого друга, который запустит бота по твоей ссылке, "
                   "вы оба получаете +{bonus} генераций.\n\nТвоя ссылка:\n{link}\n\nПриглашено: {n}"),
        "invite_welcome": "🎁 Бонус за приглашение: +{c} генераций!", "invite_notice": "🎉 По твоей ссылке пришёл друг! +{b} генераций.",
        "share_text": "Бот генерирует идеи для игр и НРИ — смотри, что выпало:",
        "saved_title": "❤️ <b>Избранное</b> ({n})", "saved_empty": "Пока пусто. Нажимай «❤️ В избранное» под карточками.",
        "sub_on": "🔔 Готово! Каждый день пришлю свежую идею.", "sub_off": "🔕 Ежедневная идея отключена.",
        "btn_sub_on": "🔔 Идея дня в личку", "btn_sub_off": "🔕 Отключить идею дня", "btn_saved": "❤️ Избранное",
        "btn_lang": "🌐 English", "lang_set": "Язык: русский 🇷🇺", "stale": "Эта кнопка устарела. Нажми /start.",
        "premium_on": "⭐ Премиум до {date}", "m_invite": "👥 Друзья",
    },
    "en": {
        "welcome": ("🔥 <b>IdeaForge</b> — an idea forge for game devs and tabletop GMs.\n\n"
                    "One tap, one finished card: a game idea, character, faction, artifact, quest or location.\n"
                    "{free} free per day. Invite a friend — you both get +{bonus} generations.\n\n"
                    "What shall we forge?"),
        "kinds": {"game": "Game", "npc": "Character", "faction": "Faction", "item": "Artifact", "quest": "Quest", "place": "Location"},
        "again": "🔄 Again", "save": "❤️ Save", "share": "📤 Share", "saved_ok": "Saved ❤️",
        "saved_dup": "Already saved", "saved_full": "You have {n} saved — the free limit. Premium removes it.",
        "streak": "🔥 Streak: {n} days",
        "limit": "You've used today's free generations.\n\n👥 Invite a friend — you both get +{bonus}.\n⭐ Or go unlimited.",
        "btn_invite": "👥 Invite a friend", "buy_pack": "+50 generations · {p} ⭐", "buy_premium": "Unlimited 30 days · {p} ⭐",
        "pack_title": "50 generations", "pack_desc": "50 extra generations, no expiry",
        "premium_title": "Unlimited, 30 days", "premium_desc": "Unlimited generations and unlimited saved ideas",
        "paid": "Thank you! Your purchase is active ⭐", "balance": "Bought generations left: {n}\nFree today: {free}",
        "invite": ("👥 <b>Invite friends</b>\n\nFor every friend who starts the bot from your link "
                   "you both get +{bonus} generations.\n\nYour link:\n{link}\n\nInvited: {n}"),
        "invite_welcome": "🎁 Invite bonus: +{c} generations!", "invite_notice": "🎉 A friend joined via your link! +{b} generations.",
        "share_text": "A bot that generates ideas for games and tabletop RPGs — look what I got:",
        "saved_title": "❤️ <b>Saved</b> ({n})", "saved_empty": "Nothing yet. Tap “❤️ Save” under a card.",
        "sub_on": "🔔 Done! I'll send a fresh idea every day.", "sub_off": "🔕 Daily idea turned off.",
        "btn_sub_on": "🔔 Daily idea in DM", "btn_sub_off": "🔕 Stop daily idea", "btn_saved": "❤️ Saved",
        "btn_lang": "🌐 Русский", "lang_set": "Language: English 🇬🇧", "stale": "This button is outdated. Press /start.",
        "premium_on": "⭐ Premium until {date}", "m_invite": "👥 Friends",
    },
}


def lang(user) -> str:
    return store.get_lang(user.id) or lang_of(user)


def tr(user, key: str, **kw) -> str:
    return T[lang(user)][key].format(**kw) if kw else T[lang(user)][key]


def btn(text: str, data: str = "", url: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url) if url else InlineKeyboardButton(text=text, callback_data=data)


def kb(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


def kinds_rows(user):
    names = T[lang(user)]["kinds"]
    keys = list(GENERATORS)
    return [[btn(f"{ICONS[k]} {names[k]}", f"g:{k}") for k in keys[i:i + 3]] for i in range(0, len(keys), 3)]


def menu(user) -> InlineKeyboardMarkup:
    t = T[lang(user)]
    sub = t["btn_sub_off"] if store.is_sub(user.id) else t["btn_sub_on"]
    return kb(*kinds_rows(user), [btn(t["btn_saved"], "m:saved"), btn(t["m_invite"], "m:invite")],
              [btn(sub, "m:sub"), btn(t["btn_lang"], "m:lang")])


def shop(user) -> InlineKeyboardMarkup:
    t = T[lang(user)]
    return kb([btn(t["btn_invite"], "m:invite")],
              [btn(t["buy_pack"].format(p=PRODUCTS["pack_50"]), "buy:pack_50")],
              [btn(t["buy_premium"].format(p=PRODUCTS["premium_30"]), "buy:premium_30")])


async def idea_keyboard(user, bot, kind: str, seed: int) -> InlineKeyboardMarkup:
    t = T[lang(user)]
    me = await bot.me()
    link = ref_link(me.username, user.id)
    return kb([btn(t["again"], f"g:{kind}"), btn(t["save"], f"sv:{kind}:{seed}")],
              [btn(t["share"], url=share_url(link, t["share_text"]))],
              *kinds_rows(user))


async def send_idea(m: Message, user, kind: str) -> None:
    """Spends one generation (or shows the shop) and sends the card."""
    if not store.take(user.id, FREE_PER_DAY):
        return await m.answer(tr(user, "limit", bonus=INVITER_BONUS), reply_markup=shop(user))
    idea = make(kind)
    me = await m.bot.me()
    data = await asyncio.to_thread(render, idea, me.username)
    caption = text(idea, lang(user))
    streak, _best, grew = store.streak_hit(user.id)
    if streak >= 2:
        caption += "\n\n" + tr(user, "streak", n=streak)
    markup = await idea_keyboard(user, m.bot, kind, idea["seed"])
    await m.answer_photo(BufferedInputFile(data, filename=f"{kind}.jpg"), caption=caption, parse_mode="HTML", reply_markup=markup)


# ---- start & basics ---------------------------------------------------------------------------
@router.message(CommandStart())
async def start(m: Message):
    user = m.from_user
    created = store.ensure_user(user.id)
    if not store.get_lang(user.id):
        store.set_lang(user.id, lang_of(user))
    arg = start_arg(m.text)
    inviter = parse_ref(arg)
    if created and inviter and store.add_referral(user.id, inviter):
        store.add_credits(inviter, INVITER_BONUS)
        store.add_credits(user.id, INVITEE_BONUS)
        await m.answer(tr(user, "invite_welcome", c=INVITEE_BONUS))
        try:
            await m.bot.send_message(inviter, T[store.get_lang(inviter) or "ru"]["invite_notice"].format(b=INVITER_BONUS))
        except Exception:
            pass
    if arg == "sub":
        store.set_sub(user.id, True)
        return await m.answer(tr(user, "sub_on"), reply_markup=menu(user))
    await m.answer(tr(user, "welcome", free=FREE_PER_DAY, bonus=INVITER_BONUS), parse_mode="HTML", reply_markup=menu(user))


@router.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer(tr(m.from_user, "welcome", free=FREE_PER_DAY, bonus=INVITER_BONUS), parse_mode="HTML", reply_markup=menu(m.from_user))


@router.message(Command("lang"))
async def lang_cmd(m: Message):
    await toggle_lang(m, m.from_user)


async def toggle_lang(m: Message, user) -> None:
    store.set_lang(user.id, "en" if lang(user) == "ru" else "ru")
    await m.answer(tr(user, "lang_set"), reply_markup=menu(user))


@router.message(Command("buy"))
async def buy_cmd(m: Message):
    user = m.from_user
    await m.answer(tr(user, "balance", n=store.credits(user.id), free=store.free_left(user.id, FREE_PER_DAY)), reply_markup=shop(user))


@router.message(Command("invite"))
async def invite_cmd(m: Message):
    await show_invite(m, m.from_user)


async def show_invite(m: Message, user) -> None:
    me = await m.bot.me()
    link = ref_link(me.username, user.id)
    t = T[lang(user)]
    await m.answer(tr(user, "invite", bonus=INVITER_BONUS, link=link, n=store.referrals(user.id)), parse_mode="HTML",
                   reply_markup=kb([btn(t["share"], url=share_url(link, t["share_text"]))]))


@router.message(Command("sub"))
async def sub_cmd(m: Message):
    await toggle_sub(m, m.from_user)


async def toggle_sub(m: Message, user) -> None:
    on = not store.is_sub(user.id)
    store.set_sub(user.id, on)
    await m.answer(tr(user, "sub_on" if on else "sub_off"), reply_markup=menu(user))


def _command_for(kind: str):
    async def handler(m: Message):
        store.ensure_user(m.from_user.id)
        await send_idea(m, m.from_user, kind)
    handler.__name__ = f"cmd_{kind}"
    return handler


for _kind in GENERATORS:  # /game /npc /faction /item /quest /place
    router.message(Command(_kind))(_command_for(_kind))


# ---- generation, saving ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("g:"))
async def generate(c: CallbackQuery):
    kind = c.data[2:]
    if kind in GENERATORS:
        store.ensure_user(c.from_user.id)
        await send_idea(c.message, c.from_user, kind)
    await c.answer()


@router.callback_query(F.data.startswith("sv:"))
async def save(c: CallbackQuery):
    user = c.from_user
    try:
        _, kind, seed = c.data.split(":")
        int(seed)
        assert kind in GENERATORS
    except (ValueError, AssertionError):
        return await c.answer()
    key = f"{kind}:{seed}"
    if store.has_saved(user.id, key):
        return await c.answer(tr(user, "saved_dup"))
    if not store.is_premium(user.id) and store.count_saved(user.id) >= FREE_SAVED:
        await c.message.answer(tr(user, "saved_full", n=FREE_SAVED), reply_markup=shop(user))
        return await c.answer()
    store.save_item(user.id, key, key)
    await c.answer(tr(user, "saved_ok"))


@router.message(Command("saved"))
async def saved_cmd(m: Message):
    await show_saved(m, m.from_user)


async def show_saved(m: Message, user) -> None:
    rows = store.list_saved(user.id, 20)
    if not rows:
        return await m.answer(tr(user, "saved_empty"), reply_markup=menu(user))
    lg = lang(user)
    parts = [tr(user, "saved_title", n=store.count_saved(user.id))]
    for key, _ in rows:
        kind, seed = key.split(":")
        parts.append(text(make(kind, int(seed)), lg))
    out, size = [], 0
    for p in parts:  # Telegram's limit is 4096 characters per message
        if size + len(p) > 3800:
            await m.answer("\n\n".join(out), parse_mode="HTML")
            out, size = [], 0
        out.append(p)
        size += len(p) + 2
    await m.answer("\n\n".join(out), parse_mode="HTML", reply_markup=menu(user))


# ---- payments ---------------------------------------------------------------------------------
@router.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    user, key = c.from_user, c.data[4:]
    if key not in PRODUCTS:
        return await c.answer()
    t = T[lang(user)]
    kind = "pack" if key == "pack_50" else "premium"
    await send_invoice(c.bot, c.message.chat.id, t[f"{kind}_title"], t[f"{kind}_desc"], key, PRODUCTS[key])
    await c.answer()


def on_paid(uid: int, payload: str) -> str:
    if payload == "pack_50":
        store.add_credits(uid, 50)
    else:
        store.add_premium(uid, 30)
    return T[store.get_lang(uid) or "ru"]["paid"]


@router.callback_query(F.data.startswith("m:"))
async def menu_action(c: CallbackQuery):
    user, m, action = c.from_user, c.message, c.data[2:]
    if action == "saved":
        await show_saved(m, user)
    elif action == "invite":
        await show_invite(m, user)
    elif action == "sub":
        await toggle_sub(m, user)
    elif action == "lang":
        await toggle_lang(m, user)
    await c.answer()


router.include_router(payments_router(store, PRODUCTS, on_paid))


@router.callback_query()
async def stale_button(c: CallbackQuery):
    await c.answer(tr(c.from_user, "stale"), show_alert=True)
