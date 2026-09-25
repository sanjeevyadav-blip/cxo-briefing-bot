"""
Visual design for the story slides.

The palette rotates per story so consecutive cards look distinct. Each
slide gets a big story number, an accent bar, a left-aligned headline, a
source chip and a divider above the caption -- drawn with ASS vector and
override tags, so the video is still one ffmpeg pass with no image files.

ASS colours are &HBBGGRR& (blue-green-red), not RGB.
"""

ACCENTS = [
    "&H3AB0FF&",   # amber
    "&HE0A04F&",   # steel blue
    "&H8AD85A&",   # green
    "&H6A6AFF&",   # coral red
    "&HE0C85A&",   # teal
    "&HD07AC8&",   # violet
]
PAPER = "&HF3EDE6&"
DIM = "&H8A8A8A&"
RULE = "&H3A332C&"


def accent(i):
    return ACCENTS[i % len(ACCENTS)]


def rect(x, y, w, h, colour):
    """Filled rectangle, as the text of an ASS dialogue event."""
    return (f"{{\\an7\\pos({x},{y})\\c{colour}\\bord0\\shad0\\p1}}"
            f"m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")


def text_at(x, y, body, colour, size, bold=1, align=7):
    return (f"{{\\an{align}\\pos({x},{y})\\c{colour}\\fs{size}\\b{bold}"
            f"\\bord0\\shad0}}{body}")
