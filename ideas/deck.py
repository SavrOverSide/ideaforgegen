"""A printable PDF deck of ten idea cards."""
import io
import random

from PIL import Image

from .card import render
from .tables import GENERATORS, make

SINGLES = [k for k in GENERATORS if k != "set"]


def build(bot_username: str = "") -> bytes:
    """Ten cards: every kind at least once, the rest random. Returns the PDF bytes."""
    kinds = SINGLES + random.sample(SINGLES * 2, 10 - len(SINGLES))
    random.shuffle(kinds)
    pages = [Image.open(io.BytesIO(render(make(k), bot_username))).convert("RGB") for k in kinds]
    out = io.BytesIO()
    pages[0].save(out, "PDF", save_all=True, append_images=pages[1:], resolution=150)
    return out.getvalue()
