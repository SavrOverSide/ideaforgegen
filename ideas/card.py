"""Picture cards for generated ideas: a unique procedural sigil per name, glass panel, bilingual labels."""
import hashlib
import io
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
W, H = 1080, 1350
PAD = 84

# kind -> (base top, base bottom, accent, glow1, glow2)
THEMES = {
    "game": ((10, 8, 30), (22, 12, 54), (120, 240, 255), (110, 60, 255), (255, 70, 170)),
    "npc": ((26, 10, 10), (50, 18, 16), (255, 188, 92), (230, 80, 40), (160, 40, 120)),
    "faction": ((6, 22, 24), (10, 40, 40), (232, 214, 128), (30, 170, 150), (60, 100, 220)),
}
TITLES = {"game": "ИДЕЯ ИГРЫ · GAME IDEA", "npc": "ПЕРСОНАЖ · CHARACTER", "faction": "ФРАКЦИЯ · FACTION"}


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"Inter-{name}.otf"), size)


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def over(img, layer):
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def background(theme, rnd):
    top, bottom, _, g1, g2 = theme
    strip = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        strip.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    img = strip.resize((W, H))
    blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blobs)
    for color, (cx, cy, r, a) in ((g1, (540, 400, 520, 150)), (g2, (rnd.randint(-100, 300), rnd.randint(900, 1350), 480, 110)),
                                  (g1, (rnd.randint(800, 1150), rnd.randint(900, 1300), 380, 80))):
        bd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (a,))
    img = over(img, blobs.filter(ImageFilter.GaussianBlur(130)))
    grain = Image.effect_noise((W, H), 48).convert("RGB")
    return Image.blend(img, ImageChops.overlay(img, grain), 0.22)


def sigil(name: str, accent, rnd, size=400):
    """A one-of-a-kind emblem: rings, nested polygons, ticks and orbiting dots. Same name -> same sigil."""
    S = size * 2  # draw at 2x and downsample for smooth lines
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = S // 2
    col = lambda a: accent + (a,)  # noqa: E731
    d.ellipse((6, 6, S - 6, S - 6), outline=col(255), width=11)
    d.ellipse((40, 40, S - 40, S - 40), outline=col(120), width=4)
    ticks = rnd.choice([12, 16, 24, 36])
    for k in range(ticks):
        a = 2 * math.pi * k / ticks
        r0, r1 = c - 34, c - (62 if k % 2 else 82)
        d.line((c + r0 * math.cos(a), c + r0 * math.sin(a), c + r1 * math.cos(a), c + r1 * math.sin(a)), fill=col(200), width=7)
    base = rnd.uniform(0, math.pi)
    sides = rnd.choice([3, 4, 5, 6, 7, 8])
    radius = c - 120
    for layer_i in range(rnd.randint(2, 4)):
        n = sides if layer_i % 2 == 0 else rnd.choice([3, 5, 6, 8])
        rot = base + layer_i * rnd.uniform(0.15, 0.6)
        pts = [(c + radius * math.cos(rot + 2 * math.pi * k / n), c + radius * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]
        d.polygon(pts, fill=col(26), outline=col(255 - layer_i * 35), width=9)
        if rnd.random() < 0.6:  # star-like chords
            step = 2 if n > 4 else 1
            for k in range(n):
                d.line(pts[k] + pts[(k + step) % n], fill=col(150), width=4)
        radius = int(radius * rnd.uniform(0.66, 0.8))
    for k in range(rnd.randint(3, 7)):  # orbiting dots
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.choice([c - 6, c - 34])
        x, y = c + r * math.cos(a), c + r * math.sin(a)
        d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=col(255))
    d.ellipse((c - 78, c - 78, c + 78, c + 78), fill=(0, 0, 0, 150), outline=col(255), width=7)
    d.text((c, c - 4), name[:1].upper(), font=font("ExtraBold", 104), fill=col(255), anchor="mm")
    return layer.resize((size, size), Image.LANCZOS)


def glass(img, box, radius=44):
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius, fill=255)
    img = Image.composite(img.filter(ImageFilter.GaussianBlur(28)), img, mask)
    tint = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    ImageDraw.Draw(tint).rounded_rectangle(box, radius, fill=(255, 255, 255, 22), outline=(255, 255, 255, 70), width=2)
    return over(img, tint)


def render(idea: dict, bot_username: str = "", handle: str = "@ideaforges") -> bytes:
    kind = idea["kind"]
    theme = THEMES[kind]
    accent = theme[2]
    key = idea["name"] + idea.get("name_en", "")
    rnd = random.Random(int(hashlib.md5(key.encode()).hexdigest(), 16))
    img = background(theme, rnd)
    A = accent + (255,)
    white = (255, 255, 255, 255)

    # sigil with a soft glow, centred in the upper half
    s = sigil(idea.get("name_en") or idea["name"], accent, rnd)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow.paste(s, ((W - s.width) // 2, 150), s)
    img = over(img, glow.filter(ImageFilter.GaussianBlur(30)))
    img = over(img, glow.filter(ImageFilter.GaussianBlur(8)))
    img = over(img, glow)

    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((PAD, 80, PAD + 64, 144), 18, fill=A)
    d.text((PAD + 32, 112), "I", font=font("ExtraBold", 40), fill=theme[0] + (255,), anchor="mm")
    d.text((PAD + 86, 112), "IDEAFORGE", font=font("Bold", 30), fill=white, anchor="lm")
    f = font("SemiBold", 24)
    tag = TITLES[kind]
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle((W - PAD - tw - 48, 82, W - PAD, 142), 30, fill=accent + (36,), outline=accent + (150,), width=2)
    d.text((W - PAD - 24, 112), tag, font=f, fill=A, anchor="rm")

    # title (shrinks to fit; bilingual for factions, where the name differs by language)
    title = idea["name"]
    size = 84
    while size > 44 and d.textlength(title, font=font("ExtraBold", size)) > W - 2 * PAD:
        size -= 4
    y = 612
    d.text((W // 2, y), title, font=font("ExtraBold", size), fill=white, anchor="mm")
    if "name_en" in idea:
        d.text((W // 2, y + size // 2 + 30), idea["name_en"], font=font("Medium", 32), fill=(255, 255, 255, 150), anchor="mm")
        y += 40

    # rows
    rows = idea["rows"]
    fr, fe, fl = font("Medium", 32), font("Regular", 26), font("Bold", 21)
    top = y + 60
    blocks = []
    for label, value in rows:
        ru_lines = wrap(d, value[0], fr, W - 2 * PAD - 40)
        en_lines = [] if value[0] == value[1] else wrap(d, value[1], fe, W - 2 * PAD - 40)
        blocks.append((label, ru_lines, en_lines))
    total = sum(28 + len(r) * 40 + len(e) * 34 + 22 for _, r, e in blocks) + 34
    if top + total > H - 138:  # drop the English line first if it won't fit
        blocks = [(label, r, []) for label, r, _ in blocks]
        total = sum(28 + len(r) * 40 + 22 for _, r, _ in blocks) + 34
    img = glass(img, (PAD - 24, top, W - PAD + 24, top + total))
    d = ImageDraw.Draw(img, "RGBA")
    cy = top + 28
    for label, ru_lines, en_lines in blocks:
        d.text((PAD + 20, cy), f"{label[0].upper()} · {label[1].upper()}", font=fl, fill=A)
        cy += 28
        for line in ru_lines:
            d.text((PAD + 20, cy), line, font=fr, fill=(255, 255, 255, 245))
            cy += 40
        for line in en_lines:
            d.text((PAD + 20, cy), line, font=fe, fill=(255, 255, 255, 150))
            cy += 34
        cy += 22

    d.line((PAD, H - 140, W - PAD, H - 140), fill=(255, 255, 255, 40), width=2)
    d.text((PAD, H - 90), handle, font=font("Bold", 36), fill=A, anchor="lm")
    if bot_username:
        d.text((W - PAD, H - 90), f"t.me/{bot_username}", font=font("Medium", 28), fill=(255, 255, 255, 150), anchor="rm")

    out = io.BytesIO()
    img.save(out, "JPEG", quality=92, optimize=True)
    return out.getvalue()
