"""
Slide layouts rendered as PNG images, YouTube-explainer style.

story_slide(): category banner, headline card, key-number tile, and up to
three numbered point cards -- rendered once per reveal stage so the points
build up while the story is discussed. intro_slide(): title plus an
"in this episode" agenda of the first few headlines.
"""
import slide_draw as sd

CATEGORIES = [
    ("MARKETS", ["sensex", "nifty", "stock", "shares", "market", "ipo",
                 "index", "investor", "equity"]),
    ("ECONOMY", ["gdp", "inflation", "rbi", "rate", "fiscal", "growth",
                 "economy", "recession", "deficit"]),
    ("TRADE & POLICY", ["tariff", "trade", "sanction", "policy", "tax",
                        "gst", "regulat", "sebi", "government", "minister"]),
    ("TECH & AI", ["ai", "artificial", "tech", "chip", "software",
                   "digital", "data", "cloud"]),
    ("STARTUPS", ["startup", "funding", "raises", "venture", "unicorn"]),
    ("BANKING", ["bank", "loan", "credit", "lender", "nbfc"]),
    ("ENERGY", ["oil", "crude", "energy", "fuel", "gas", "power"]),
    ("GEOPOLITICS", ["war", "iran", "russia", "china", "ukraine",
                     "military", "attack", "brics"]),
]


def category(title):
    words = title.lower().replace(",", " ").replace(":", " ").split()
    for name, keys in CATEGORIES:
        if any(any(w.startswith(k) for w in words) for k in keys):
            return name
    return "CORPORATE"


def _top_bar(d, show, date):
    d.text((60, 30), show, font=sd.font(24), fill=sd.WHITE)
    f = sd.font(22, False)
    d.text((sd.W - 60 - f.getlength(date), 32), date, font=f, fill=sd.MUTED)


def _band(d, idx, total, col, source):
    d.rectangle((0, 640, sd.W, sd.H), fill=sd.BAND)
    d.rounded_rectangle((60, 626, sd.W - 60, 632), 3, fill=sd.CARD_HI)
    done = int((sd.W - 120) * (idx + 1) / max(total, 1))
    d.rounded_rectangle((60, 626, 60 + done, 632), 3, fill=col)


def story_slide(path, slide, idx, total, stage, show, date, region=""):
    col = sd.accent(idx)
    img, d = sd.canvas(col)
    _top_bar(d, show, date)

    label = category(slide["title"])
    if region:
        label = f"{region.upper()}  |  {label}"
    f = sd.font(20)
    pw = int(f.getlength(label)) + 36
    d.rounded_rectangle((60, 90, 60 + pw, 126), 18, fill=col)
    d.text((78, 97), label, font=f, fill=sd.BG_BOT)
    meta = f"Story {idx + 1} of {total}"
    if slide.get("source"):
        meta += f"   |   {slide['source']}"
    d.text((80 + pw, 97), meta, font=sd.font(20, False), fill=sd.MUTED)

    stat = slide.get("stat")
    head_w = 740 if stat else 1160
    hf = sd.font(36)
    lines = sd.wrap(slide["title"], hf, head_w - 48, 3)
    hb = 150 + 36 + len(lines) * (hf.size + 10)
    sd.card(sd.ImageDraw.Draw(img), (60, 150, 60 + head_w, hb))
    d.rectangle((60, 170, 66, hb - 20), fill=col)
    sd.text_block(d, (90, 168), lines, hf, sd.WHITE, 10)

    if stat:
        sd.card(d, (840, 150, 1220, 330), fill=sd.CARD_HI, outline=col)
        d.text((868, 172), "KEY NUMBER", font=sd.font(18), fill=sd.MUTED)
        sf = sd.fit_font(stat, 330, 60)
        d.text((868, 214), stat, font=sf, fill=col)

    y = max(hb, 330 if stat else hb) + 22
    bf = sd.font(21, False)
    for n, pt in enumerate((slide.get("bullets") or [])[:stage]):
        pl = sd.wrap(pt, bf, 1040, 2)
        h = 22 + len(pl) * (bf.size + 7)
        if y + h > 612:
            break
        sd.card(d, (60, y, 1220, y + h), r=16)
        d.ellipse((76, y + 8, 108, y + 40), fill=col)
        num = str(n + 1)
        nf = sd.font(18)
        d.text((92 - nf.getlength(num) / 2, y + 13), num, font=nf,
               fill=sd.BG_BOT)
        sd.text_block(d, (128, y + 11), pl, bf, sd.WHITE, 7)
        y += h + 10

    _band(d, idx, total, col, slide.get("source", ""))
    img.save(path)


def intro_slide(path, show, date, slides):
    img, d = sd.canvas(sd.accent(0))
    _top_bar(d, show, date)
    d.text((60, 110), "TODAY'S BRIEFING", font=sd.font(24), fill=sd.accent(0))
    d.text((60, 148), show, font=sd.fit_font(show, 1100, 72), fill=sd.WHITE)
    d.rounded_rectangle((60, 250, 200, 258), 4, fill=sd.accent(0))
    d.text((60, 276), f"{len(slides)} stories", font=sd.font(26, False),
           fill=sd.MUTED)
    d.text((60, 336), "IN THIS EPISODE", font=sd.font(20), fill=sd.MUTED)
    y, af = 372, sd.font(22, False)
    for i, s in enumerate(slides[:4]):
        col = sd.accent(i)
        sd.card(d, (60, y, 1220, y + 50), r=14)
        d.rectangle((60, y + 10, 66, y + 40), fill=col)
        t = sd.wrap(s["title"], af, 1080, 1)[0]
        d.text((88, y + 13), t, font=af, fill=sd.WHITE)
        y += 60
    d.rectangle((0, 640, sd.W, sd.H), fill=sd.BAND)
    img.save(path)
