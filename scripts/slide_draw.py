"""
Drawing primitives for the explainer slides: fonts, palette, gradient
background, rounded cards and pixel-accurate text wrapping. Layouts that
use these live in slide_render.py.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

BG_TOP = (14, 20, 38)
BG_BOT = (8, 11, 22)
CARD = (27, 35, 58)
CARD_HI = (36, 46, 74)
WHITE = (243, 245, 250)
MUTED = (150, 160, 185)
BAND = (5, 7, 15)

ACCENTS = [
    (255, 176, 58),   # amber
    (79, 160, 255),   # blue
    (72, 214, 150),   # green
    (255, 107, 107),  # coral
    (90, 200, 224),   # teal
    (200, 122, 255),  # violet
]

_cache = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _cache:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _cache[key] = ImageFont.truetype(FONT_DIR + name, size)
    return _cache[key]


def accent(i):
    return ACCENTS[i % len(ACCENTS)]


def canvas(glow):
    """Vertical gradient with a soft accent glow in the top-right corner."""
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = tuple(int(BG_TOP[k] + (BG_BOT[k] - BG_TOP[k]) * t) for k in range(3))
        d.line([(0, y), (W, y)], fill=c)
    halo = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(halo).ellipse((880, -260, 1500, 360), fill=glow)
    halo = halo.filter(ImageFilter.GaussianBlur(140))
    img = Image.blend(img, Image.composite(halo, img, halo.convert("L")), 0.35)
    return img, ImageDraw.Draw(img)


def card(d, box, fill=CARD, r=22, outline=None):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=2)


def wrap(text, fnt, max_w, max_lines):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and fnt.getlength(trial) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def text_block(d, xy, lines, fnt, fill, gap=8):
    x, y = xy
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


def fit_font(text, max_w, start, floor=22):
    size = start
    while size > floor and font(size).getlength(text) > max_w:
        size -= 2
    return font(size)
