"""Builds the itch.io product: a printable PDF of RPG seeds made from IdeaForge's tables, plus store images.

python3 build.py  ->  out/steppe-and-static-vol1.pdf, out/cover-630x500.png, out/shot-*.png
"""
import io
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer)

IF = Path("/home/claude/ideaforgegen")
sys.path.insert(0, str(IF))
from ideas import card, tables as t  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
for w in ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold"):
    pdfmetrics.registerFont(TTFont(f"Inter-{w}", str(HERE / "fonts" / f"Inter-{w}.ttf")))
OTF = lambda w, s: ImageFont.truetype(str(IF / "assets" / "fonts" / f"Inter-{w}.otf"), s)  # noqa: E731

INK, MUTED, PAPER = HexColor("#1b1626"), HexColor("#5d566b"), HexColor("#fbf8f3")
KINDS = [("npc", "npc", "#d9822b"), ("item", "item", "#b8860b"), ("quest", "quest", "#a0662a"), ("place", "place", "#2a8f7b"),
         ("faction", "faction", "#3f7f6e"), ("game", "game", "#5b5bd6"), ("set", "set", "#c2457a")]
TEXT = {
    "en": dict(
        file="steppe-and-static-vol1", title="Steppe & Static", t1="Steppe &", t2="Static", sub="100 Weird Seeds for Any RPG",
        vol="Volume 1", presents="IDEAFORGE PRESENTS", tagline="System-agnostic  ·  Printable  ·  Volume 1",
        store=("100 weird seeds", "for any RPG", "System-agnostic · Printable PDF"), section="SECTION",
        lead="100 Weird Seeds for Any RPG. A pocket of strange, ready-to-use material for game masters, writers and game designers. "
             "Nothing here depends on rules: drop any entry into D&amp;D, Mörk Borg, Cyberpunk RED, Blades in the Dark, "
             "a homebrew system or a novel.",
        flavour_h="The flavour",
        flavour="Steppe & Static mixes the wind-swept open steppe with buzzing cables and dead satellites: yurts next to server "
                "racks, dombras made of bone, oracles with smartphones. Use it straight, or file the serial numbers off for "
                "plain fantasy or plain cyberpunk.",
        howto_h="How to use it",
        howto="<b>Roll.</b> Every section is a numbered table: roll a d20 (or a d10 for the shorter ones) and take that entry. "
              "<b>Mix.</b> Take the character from one roll and the secret from another; the parts are built to swap. "
              "<b>Steal.</b> Read a page before a session and keep whatever sticks.",
        kits="<b>Campaign Kits</b> at the end are already linked: a place, the faction that rules it, its leader and their "
             "secret, a job for the players and the prize. One kit is enough for a whole evening.",
        contents_h="Contents", entries="entries",
        made="Made with IdeaForge, a generator bot for game ideas: t.me/ideaforge_gen_bot. You may use anything in this book in "
             "your games and in published work, commercial or not. Please do not resell the PDF itself.",
        roll="Roll {die} or pick one.",
        sections=[("Characters", "Twenty people worth meeting, each with a habit and a secret."),
                  ("Artifacts", "Twenty strange objects, each with a power, a price and a story."),
                  ("Quests", "Twenty jobs that will not go as planned."),
                  ("Locations", "Twenty places to visit once and remember forever."),
                  ("Factions", "Ten groups that want something badly."),
                  ("Game Pitches", "Ten video-game or board-game pitches for designers."),
                  ("Campaign Kits", "Ten linked kits: a place, who rules it, their secret, a job and a prize.")]),
    "ru": dict(
        file="step-i-statika-tom1", title="Степь и статика", t1="Степь", t2="и статика", sub="100 странных идей для любой НРИ",
        vol="Том 1", presents="IDEAFORGE ПРЕДСТАВЛЯЕТ", tagline="Для любой системы  ·  Для печати  ·  Том 1",
        store=("100 странных идей", "для любой НРИ", "Для любой системы · PDF для печати"), section="РАЗДЕЛ",
        lead="100 странных идей для любой настольной ролевой игры. Карманный запас готового материала для мастеров, авторов "
             "и геймдизайнеров. Ничего не завязано на правила: любую запись можно взять в D&amp;D, «Мёрк Борг», "
             "Cyberpunk RED, Blades in the Dark, свою систему или в рассказ.",
        flavour_h="О чём это",
        flavour="«Степь и статика» смешивает открытую ветреную степь с гудящими проводами и мёртвыми спутниками: юрты рядом с "
                "серверными стойками, домбры из кости, оракулы со смартфонами. Берите как есть или уберите лишнее, и получится "
                "чистое фэнтези или чистый киберпанк.",
        howto_h="Как пользоваться",
        howto="<b>Бросайте.</b> Каждый раздел это пронумерованная таблица: бросьте d20 (или d10 для коротких) и возьмите запись. "
              "<b>Смешивайте.</b> Персонажа из одного броска, секрет из другого: части сделаны так, чтобы их можно было менять. "
              "<b>Заимствуйте.</b> Прочитайте страницу перед игрой и оставьте то, что зацепило.",
        kits="<b>Наборы для кампании</b> в конце уже связаны: место, фракция, которая им правит, её лидер и его тайна, задание "
             "для игроков и награда. Одного набора хватит на целый вечер.",
        contents_h="Содержание", entries="шт.",
        made="Сделано в IdeaForge, боте-генераторе идей для игр: t.me/ideaforge_gen_bot. Всё из этой книги можно использовать "
             "в своих играх и в опубликованных работах, в том числе платных. Пожалуйста, не перепродавайте сам PDF.",
        roll="Бросьте {die} или выберите сами.",
        sections=[("Персонажи", "Двадцать людей, с которыми стоит встретиться, у каждого привычка и секрет."),
                  ("Артефакты", "Двадцать странных вещей, у каждой сила, цена и история."),
                  ("Квесты", "Двадцать заданий, которые пойдут не по плану."),
                  ("Локации", "Двадцать мест, куда приходят один раз и помнят всю жизнь."),
                  ("Фракции", "Десять групп, которым очень чего-то хочется."),
                  ("Идеи игр", "Десять идей для видеоигр и настольных игр, для разработчиков."),
                  ("Наборы для кампании", "Десять связанных наборов: место, кто им правит, его тайна, задание и награда.")]),
}
TITLE = SUB = VOL = ""
SECTIONS: list = []
TX: dict = {}


def set_lang(lang: str) -> None:
    global LANG, TITLE, SUB, VOL, SECTIONS, TX
    LANG, TX = lang, TEXT[lang]
    TITLE, SUB, VOL = TX["title"], TX["sub"], TX["vol"]
    SECTIONS = [(key, title, blurb, kind, accent) for (key, kind, accent), (title, blurb) in zip(KINDS, TX["sections"])]


cap = lambda s: s[:1].upper() + s[1:]  # noqa: E731


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------------------------
# content: every entry used once across the whole book
# ---------------------------------------------------------------------------------------------
LANG = "en"   # set by main(); "ru" builds the Russian edition from the same tables

L = {
    "en": dict(Trait="Trait", Secret="Secret", Power="Power", Cost="Cost", Lore="Lore", Client="Client", Reward="Reward",
               Twist="Twist", Mood="Mood", Danger="Danger", Goal="Goal", Method="Method", Leader="Leader", Setting="Setting",
               Hook="Hook", Location="Location", Ruled="Ruled by", LSecret="Leader's secret", Job="The job", Prize="The prize",
               ruled_prefix="the "),
    "ru": dict(Trait="Черта", Secret="Секрет", Power="Сила", Cost="Цена", Lore="Легенда", Client="Заказчик", Reward="Награда",
               Twist="Поворот", Mood="Атмосфера", Danger="Опасность", Goal="Цель", Method="Метод", Leader="Лидер", Setting="Сеттинг",
               Hook="Фишка", Location="Место", Ruled="Правит", LSecret="Тайна лидера", Job="Задание", Prize="Награда",
               ruled_prefix=""),
}


class Deck:
    def __init__(self, table, rnd):
        self.items = [e[0 if LANG == "ru" else 1] for e in table]
        rnd.shuffle(self.items)

    def take(self):
        return self.items.pop()


def build_content(seed=2026):
    rnd = random.Random(seed)
    random.seed(seed)  # tables.name() uses the global generator
    d = {k: Deck(v, rnd) for k, v in t.K.items()}
    for n in ("GENRE", "SETTING", "MECHANIC", "TWIST", "ROLE", "TRAIT", "SECRET", "GOAL", "METHOD", "FACTION_OF"):
        d[n] = Deck(getattr(t, n), rnd)
    used_names = set()

    def name():
        while True:
            n = t.name()
            if n not in used_names and 4 <= len(n) <= 10:
                used_names.add(n)
                return n

    x = L[LANG]
    c = {}
    c["npc"] = [(f"{name()}, {d['ROLE'].take()}", [(x["Trait"], d["TRAIT"].take()), (x["Secret"], d["SECRET"].take())]) for _ in range(20)]
    c["item"] = [(cap(d["ITEM_TYPE"].take()), [(x["Power"], d["ITEM_POWER"].take()), (x["Cost"], d["ITEM_COST"].take()),
                                               (x["Lore"], d["ITEM_LORE"].take())]) for _ in range(20)]
    c["quest"] = [(cap(d["QUEST_TASK"].take()), [(x["Client"], d["QUEST_CLIENT"].take()), (x["Reward"], d["QUEST_REWARD"].take()),
                                                 (x["Twist"], d["QUEST_TWIST"].take())]) for _ in range(20)]
    c["place"] = [(cap(d["PLACE_TYPE"].take()), [(x["Mood"], d["PLACE_MOOD"].take()), (x["Secret"], d["PLACE_SECRET"].take()),
                                                 (x["Danger"], d["PLACE_DANGER"].take())]) for _ in range(20)]
    words = [w[0 if LANG == "ru" else 1] for w in t.FACTION_WORD]
    c["faction"] = [(f"{rnd.choice(words)} {d['FACTION_OF'].take()}", [(x["Goal"], d["GOAL"].take()), (x["Method"], d["METHOD"].take()),
                                                                     (x["Leader"], name())]) for _ in range(10)]
    c["game"] = [(f"{name()}: {d['GENRE'].take()}", [(x["Setting"], d["SETTING"].take()), (x["Hook"], d["MECHANIC"].take()),
                                                    (x["Twist"], d["TWIST"].take())]) for _ in range(10)]
    c["set"] = []
    for _ in range(10):
        leader = name()
        c["set"].append((f"{name()}", [
            (x["Location"], d["PLACE_TYPE"].take()),
            (x["Ruled"], f"{x['ruled_prefix']}{rnd.choice(words)} {d['FACTION_OF'].take()}"),
            (x["Leader"], f"{leader}, {d['ROLE'].take()}"),
            (x["LSecret"], d["SECRET"].take()),
            (x["Job"], d["QUEST_TASK"].take()),
            (x["Prize"], d["ITEM_TYPE"].take()),
        ]))
    return c


# ---------------------------------------------------------------------------------------------
# art (Pillow): cover, section banners
# ---------------------------------------------------------------------------------------------
def art_background(kind, w, h, seed):
    theme = card.THEMES[kind]
    rnd = random.Random(seed)
    card.W, card.H = w, h  # background() reads the module size
    try:
        img = card.background(theme, rnd)
    finally:
        card.W, card.H = 1080, 1350
    return img, theme, rnd


def make_cover(w=1240, h=1754):
    img, theme, rnd = art_background("set", w, h, 7)
    s = card.sigil("Steppe", theme[2], rnd, size=760)
    img = card.over(img, _place(s, w, h, (w - 760) // 2, 300))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((w // 2, 140), TX["presents"], font=OTF("SemiBold", 34), fill=theme[2] + (255,), anchor="mm")
    d.text((w // 2, 1210), TX["t1"], font=OTF("ExtraBold", 150), fill=(255, 255, 255, 255), anchor="mm")
    d.text((w // 2, 1370), TX["t2"], font=OTF("ExtraBold", 150), fill=theme[2] + (255,), anchor="mm")
    d.text((w // 2, 1500), SUB, font=OTF("SemiBold", 52), fill=(255, 255, 255, 230), anchor="mm")
    d.text((w // 2, 1600), TX["tagline"], font=OTF("Medium", 34), fill=(255, 255, 255, 160), anchor="mm")
    return img


def _place(layer, w, h, x, y):
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(layer, (x, y), layer)
    return canvas


def make_banner(kind, title, n, w=1240, h=330):
    img, theme, rnd = art_background(kind, w, h, hash(title) & 0xffff)
    s = card.sigil(title, theme[2], rnd, size=250)
    img = card.over(img, _place(s, w, h, w - 250 - 70, 40))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((80, 120), f"{TX['section']} {n}", font=OTF("Bold", 30), fill=theme[2] + (255,), anchor="lm")
    size = 96
    while size > 48 and d.textlength(title, font=OTF("ExtraBold", size)) > w - 250 - 70 - 80 - 40:
        size -= 4   # long titles shrink so they never run into the emblem
    d.text((80, 205), title, font=OTF("ExtraBold", size), fill=(255, 255, 255, 255), anchor="lm")
    return img


def store_cover(w=1260, h=1000):
    """itch.io cover (shown at 630x500): emblem on the left, title on the right."""
    img, theme, rnd = art_background("set", w, h, 7)
    s = card.sigil("Steppe", theme[2], rnd, size=640)
    img = card.over(img, _place(s, w, h, 40, (h - 640) // 2))
    d = ImageDraw.Draw(img, "RGBA")
    x = 720
    d.text((x, 300), TX["t1"], font=OTF("ExtraBold", 104), fill=(255, 255, 255, 255), anchor="lm")
    d.text((x, 420), TX["t2"], font=OTF("ExtraBold", 104), fill=theme[2] + (255,), anchor="lm")
    d.text((x, 540), TX["store"][0], font=OTF("SemiBold", 46), fill=(255, 255, 255, 235), anchor="lm")
    d.text((x, 600), TX["store"][1], font=OTF("SemiBold", 46), fill=(255, 255, 255, 235), anchor="lm")
    d.text((x, 700), TX["store"][2], font=OTF("Medium", 30), fill=(255, 255, 255, 160), anchor="lm")
    return img.resize((630, 500), Image.LANCZOS).convert("RGB")


def png(img):
    b = io.BytesIO()
    img.convert("RGB").save(b, "JPEG", quality=90)
    b.seek(0)
    return ImageReader(b)


# ---------------------------------------------------------------------------------------------
# PDF (reportlab)
# ---------------------------------------------------------------------------------------------
def build_pdf(content, path):
    W, H = A4
    M = 16 * mm
    cover = png(make_cover())
    banners = {key: png(make_banner(kind, title, i + 1)) for i, (key, title, _, kind, _) in enumerate(SECTIONS)}

    def on_cover(cv, doc):
        cv.drawImage(cover, 0, 0, W, H)

    def on_page(cv, doc):
        cv.setFillColor(PAPER)
        cv.rect(0, 0, W, H, stroke=0, fill=1)
        cv.setFont("Inter-Medium", 8)
        cv.setFillColor(MUTED)
        cv.drawString(M, 9 * mm, f"{TITLE} · {VOL}")
        cv.drawRightString(W - M, 9 * mm, str(doc.page))

    gap = 8 * mm
    colw = (W - 2 * M - gap) / 2
    body = [Frame(M, 16 * mm, colw, H - 32 * mm, id="l", showBoundary=0),
            Frame(M + colw + gap, 16 * mm, colw, H - 32 * mm, id="r", showBoundary=0)]
    top = 62 * mm + 6 * mm
    opener = [Frame(M, 16 * mm, colw, H - 16 * mm - top, id="ol"),
              Frame(M + colw + gap, 16 * mm, colw, H - 16 * mm - top, id="or")]
    full = [Frame(M, 16 * mm, W - 2 * M, H - 32 * mm, id="full")]
    doc = BaseDocTemplate(str(path), pagesize=A4, title=f"{TITLE}: {SUB}", author="IdeaForge",
                          subject="System-agnostic RPG inspiration", leftMargin=M, rightMargin=M)
    doc.addPageTemplates([
        PageTemplate("cover", [Frame(0, 0, W, H)], onPage=on_cover),
        PageTemplate("full", full, onPage=on_page),
        *[PageTemplate(f"open_{key}", opener, onPage=_opener_painter(on_page, banners[key], W, H, mm))
          for key, *_ in SECTIONS],
        PageTemplate("body", body, onPage=on_page),
    ])

    h1 = ParagraphStyle("h1", fontName="Inter-ExtraBold", fontSize=26, leading=31, textColor=INK, spaceAfter=10)
    h2 = ParagraphStyle("h2", fontName="Inter-Bold", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=4)
    p = ParagraphStyle("p", fontName="Inter-Regular", fontSize=10.5, leading=15.5, textColor=INK, spaceAfter=7)
    lead = ParagraphStyle("lead", parent=p, fontName="Inter-Medium", fontSize=11, textColor=MUTED, spaceAfter=10)

    story = [Paragraph("", p), NextPageTemplate("full"), PageBreak()]
    story += [
        Paragraph(f"{TITLE}", h1),
        Paragraph(TX["lead"], lead),
        Paragraph(TX["flavour_h"], h2),
        Paragraph(TX["flavour"], p),
        Paragraph(TX["howto_h"], h2),
        Paragraph(TX["howto"], p),
        Paragraph(TX["kits"], p),
        Paragraph(TX["contents_h"], h2),
    ]
    for i, (key, title, blurb, _, _) in enumerate(SECTIONS):
        n = len(content[key])
        story.append(Paragraph(f"<b>{i + 1}. {title}</b> · {n} {TX['entries']}. {esc(blurb)}", p))
    story.append(Paragraph(TX["made"], lead))

    for i, (key, title, blurb, _, accent) in enumerate(SECTIONS):
        story += [NextPageTemplate(f"open_{key}"), PageBreak()]
        story.append(Paragraph(esc(blurb), lead))
        die = "d20" if len(content[key]) == 20 else "d10"
        label = ParagraphStyle("lb", parent=p, fontName="Inter-Bold", textColor=HexColor(accent))
        story.append(Paragraph(TX["roll"].format(die=die), label))
        story.append(NextPageTemplate("body"))
        head = ParagraphStyle("eh", fontName="Inter-Bold", fontSize=11.5, leading=15, textColor=INK, spaceBefore=4, spaceAfter=3)
        line = ParagraphStyle("el", fontName="Inter-Regular", fontSize=9.6, leading=13.4, textColor=INK, spaceAfter=1.5)
        for n, (name, rows) in enumerate(content[key], 1):
            block = [Paragraph(f'<font color="{accent}">{n:02d}</font>  {esc(name)}', head)]
            block += [Paragraph(f'<font name="Inter-SemiBold" color="{accent}">{lab}</font>  {esc(cap(val))}', line) for lab, val in rows]
            block.append(Spacer(1, 7))
            story.append(KeepTogether(block))
    doc.build(story)


def _opener_painter(on_page, banner, W, H, mm):
    def paint(cv, doc):
        on_page(cv, doc)
        cv.drawImage(banner, 0, H - 62 * mm, W, 62 * mm)
    return paint


def store_images(pdf):
    sfx = "" if LANG == "en" else f"-{LANG}"
    store_cover().save(OUT / f"cover-630x500{sfx}.png")        # itch.io cover
    for page in (1, 3, 5, 13):                                    # screenshots: rendered PDF pages
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(page), "-l", str(page), str(pdf), str(OUT / f"page{sfx}")], check=True)


if __name__ == "__main__":
    for lang in (sys.argv[1:] or ["en", "ru"]):
        set_lang(lang)
        content = build_content()
        pdf = OUT / f"{TX['file']}.pdf"
        build_pdf(content, pdf)
        store_images(pdf)
        print(pdf, pdf.stat().st_size // 1024, "KB")
