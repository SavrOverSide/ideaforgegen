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

TITLE = "Steppe & Static"
SUB = "100 Weird Seeds for Any RPG"
VOL = "Volume 1"
INK, MUTED, PAPER = HexColor("#1b1626"), HexColor("#5d566b"), HexColor("#fbf8f3")
SECTIONS = [  # key, title, blurb, theme kind for the art, accent hex
    ("npc", "Characters", "Twenty people worth meeting, each with a habit and a secret.", "npc", "#d9822b"),
    ("item", "Artifacts", "Twenty strange objects, each with a power, a price and a story.", "item", "#b8860b"),
    ("quest", "Quests", "Twenty jobs that will not go as planned.", "quest", "#a0662a"),
    ("place", "Locations", "Twenty places to visit once and remember forever.", "place", "#2a8f7b"),
    ("faction", "Factions", "Ten groups that want something badly.", "faction", "#3f7f6e"),
    ("game", "Game Pitches", "Ten video-game or board-game pitches for designers.", "game", "#5b5bd6"),
    ("set", "Campaign Kits", "Ten linked kits: a place, who rules it, their secret, a job and a prize.", "set", "#c2457a"),
]

cap = lambda s: s[:1].upper() + s[1:]  # noqa: E731


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------------------------
# content: every entry used once across the whole book
# ---------------------------------------------------------------------------------------------
class Deck:
    def __init__(self, table, rnd):
        self.items = [e[1] for e in table]
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

    c = {}
    c["npc"] = [(f"{name()}, {d['ROLE'].take()}", [("Trait", d["TRAIT"].take()), ("Secret", d["SECRET"].take())]) for _ in range(20)]
    c["item"] = [(cap(d["ITEM_TYPE"].take()), [("Power", d["ITEM_POWER"].take()), ("Cost", d["ITEM_COST"].take()),
                                               ("Lore", d["ITEM_LORE"].take())]) for _ in range(20)]
    c["quest"] = [(cap(d["QUEST_TASK"].take()), [("Client", d["QUEST_CLIENT"].take()), ("Reward", d["QUEST_REWARD"].take()),
                                                 ("Twist", d["QUEST_TWIST"].take())]) for _ in range(20)]
    c["place"] = [(cap(d["PLACE_TYPE"].take()), [("Mood", d["PLACE_MOOD"].take()), ("Secret", d["PLACE_SECRET"].take()),
                                                 ("Danger", d["PLACE_DANGER"].take())]) for _ in range(20)]
    words = [w[1] for w in t.FACTION_WORD]
    c["faction"] = [(f"{rnd.choice(words)} {d['FACTION_OF'].take()}", [("Goal", d["GOAL"].take()), ("Method", d["METHOD"].take()),
                                                                     ("Leader", name())]) for _ in range(10)]
    c["game"] = [(f"{name()}: {d['GENRE'].take()}", [("Setting", d["SETTING"].take()), ("Hook", d["MECHANIC"].take()),
                                                    ("Twist", d["TWIST"].take())]) for _ in range(10)]
    c["set"] = []
    for _ in range(10):
        leader = name()
        c["set"].append((f"{name()}", [
            ("Location", d["PLACE_TYPE"].take()),
            ("Ruled by", f"the {rnd.choice(words)} {d['FACTION_OF'].take()}"),
            ("Leader", f"{leader}, {d['ROLE'].take()}"),
            ("Leader's secret", d["SECRET"].take()),
            ("The job", d["QUEST_TASK"].take()),
            ("The prize", d["ITEM_TYPE"].take()),
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
    d.text((w // 2, 140), "IDEAFORGE PRESENTS", font=OTF("SemiBold", 34), fill=theme[2] + (255,), anchor="mm")
    d.text((w // 2, 1210), "Steppe &", font=OTF("ExtraBold", 150), fill=(255, 255, 255, 255), anchor="mm")
    d.text((w // 2, 1370), "Static", font=OTF("ExtraBold", 150), fill=theme[2] + (255,), anchor="mm")
    d.text((w // 2, 1500), SUB, font=OTF("SemiBold", 52), fill=(255, 255, 255, 230), anchor="mm")
    d.text((w // 2, 1600), "System-agnostic  ·  Printable  ·  " + VOL, font=OTF("Medium", 34), fill=(255, 255, 255, 160), anchor="mm")
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
    d.text((80, 120), f"SECTION {n}", font=OTF("Bold", 30), fill=theme[2] + (255,), anchor="lm")
    d.text((80, 205), title, font=OTF("ExtraBold", 96), fill=(255, 255, 255, 255), anchor="lm")
    return img


def store_cover(w=1260, h=1000):
    """itch.io cover (shown at 630x500): emblem on the left, title on the right."""
    img, theme, rnd = art_background("set", w, h, 7)
    s = card.sigil("Steppe", theme[2], rnd, size=640)
    img = card.over(img, _place(s, w, h, 40, (h - 640) // 2))
    d = ImageDraw.Draw(img, "RGBA")
    x = 720
    d.text((x, 300), "Steppe &", font=OTF("ExtraBold", 104), fill=(255, 255, 255, 255), anchor="lm")
    d.text((x, 420), "Static", font=OTF("ExtraBold", 104), fill=theme[2] + (255,), anchor="lm")
    d.text((x, 540), "100 weird seeds", font=OTF("SemiBold", 46), fill=(255, 255, 255, 235), anchor="lm")
    d.text((x, 600), "for any RPG", font=OTF("SemiBold", 46), fill=(255, 255, 255, 235), anchor="lm")
    d.text((x, 700), "System-agnostic · Printable PDF", font=OTF("Medium", 30), fill=(255, 255, 255, 160), anchor="lm")
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
        Paragraph(f"{SUB}. A pocket of strange, ready-to-use material for game masters, writers and game designers. "
                  "Nothing here depends on rules: drop any entry into D&amp;D, Mörk Borg, Cyberpunk RED, Blades in the Dark, "
                  "a homebrew system or a novel.", lead),
        Paragraph("The flavour", h2),
        Paragraph("Steppe & Static mixes the wind-swept open steppe with buzzing cables and dead satellites: yurts next to server "
                  "racks, dombras made of bone, oracles with smartphones. Use it straight, or file the serial numbers off for "
                  "plain fantasy or plain cyberpunk.", p),
        Paragraph("How to use it", h2),
        Paragraph("<b>Roll.</b> Every section is a numbered table: roll a d20 (or a d10 for the shorter ones) and take that entry. "
                  "<b>Mix.</b> Take the character from one roll and the secret from another; the parts are built to swap. "
                  "<b>Steal.</b> Read a page before a session and keep whatever sticks.", p),
        Paragraph("<b>Campaign Kits</b> at the end are already linked: a place, the faction that rules it, its leader and their "
                  "secret, a job for the players and the prize. One kit is enough for a whole evening.", p),
        Paragraph("Contents", h2),
    ]
    for i, (key, title, blurb, _, _) in enumerate(SECTIONS):
        n = len(content[key])
        story.append(Paragraph(f"<b>{i + 1}. {title}</b> · {n} entries. {esc(blurb)}", p))
    story.append(Paragraph("Made with IdeaForge, a generator bot for game ideas: t.me/ideaforge_gen_bot. "
                           "You may use anything in this book in your games and in published work, commercial or not. "
                           "Please do not resell the PDF itself.", lead))

    for i, (key, title, blurb, _, accent) in enumerate(SECTIONS):
        story += [NextPageTemplate(f"open_{key}"), PageBreak()]
        story.append(Paragraph(esc(blurb), lead))
        die = "d20" if len(content[key]) == 20 else "d10"
        label = ParagraphStyle("lb", parent=p, fontName="Inter-Bold", textColor=HexColor(accent))
        story.append(Paragraph(f"Roll {die} or pick one.", label))
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
    # itch.io cover: 630x500
    store_cover().save(OUT / "cover-630x500.png")
    # screenshots: rendered PDF pages
    subprocess.run(["pdftoppm", "-png", "-r", "70", "-f", "1", "-l", "6", str(pdf), str(OUT / "shot")], check=True)


if __name__ == "__main__":
    content = build_content()
    pdf = OUT / "steppe-and-static-vol1.pdf"
    build_pdf(content, pdf)
    store_images(pdf)
    print(pdf, pdf.stat().st_size // 1024, "KB")
