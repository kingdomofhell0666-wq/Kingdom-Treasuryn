"""
Kingdom Treasury — Leaderboard Image Generator
900 × 940 px  |  Vertical premium table  |  Pillow

Layout (top → bottom):
  ┌─────────────────────────────────────┐
  │  HEADER  — crest + title + subtitle │  120 px
  ├─────────────────────────────────────┤
  │  ROW ×10  — pos │ avatar │ name+rank│  72 px each = 720 px
  ├─────────────────────────────────────┤
  │  FOOTER  — date + watermark         │  60 px
  └─────────────────────────────────────┘

Usage (synchronous — run in thread executor):
    buf = generate_leaderboard_image(rows, currency_name, currency_icon, title)
"""

import io
import math
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Assets ───────────────────────────────────────────────────────────────────
_CINZEL = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Dimensions ───────────────────────────────────────────────────────────────
W         = 900
HEADER_H  = 128
ROW_H     = 72
MAX_ROWS  = 10
FOOTER_H  = 60
H         = HEADER_H + ROW_H * MAX_ROWS + FOOTER_H   # = 908

PAD       = 28    # left/right page margin
RADIUS    = 20    # card corner radius
AV_SZ     = 48   # avatar circle diameter
ROW_PAD   = 14   # vertical padding inside a row

# ─── Colours ──────────────────────────────────────────────────────────────────
BG_TOP    = (6,  2,  2)
BG_BOT    = (18, 5,  5)
ACCENT    = (168, 16, 16)
GOLD      = (205, 158, 32)
GOLD_DIM  = (140, 108, 22)
TEXT1     = (232, 210, 210)   # name
TEXT2     = (148, 100, 100)   # rank subtitle
MUTED     = (80, 48, 48)      # separator line
ROW_A     = (14, 4, 4, 255)   # alternating row bg
ROW_B     = (10, 2, 2, 255)

MEDAL_COLORS = [
    (215, 168, 32),   # gold
    (172, 178, 185),  # silver
    (168, 102, 58),   # bronze
]

RANK_FLAVOR = {
    "Forsaken":    "the damned",
    "Vermin":      "a crawling wretch",
    "Corrupted":   "a tainted soul",
    "Mythology":   "a legend in shadow",
    "Folklore":    "a whispered name",
    "Eschatology": "a herald of endings",
    "Demonology":  "a student of darkness",
    "Archangel":   "a fallen light",
    "Archdemon":   "a lord of the abyss",
    "Knight":      "a blade of the realm",
    "Baron":       "a lord of the pit",
    "Viscount":    "a noble of shadow",
    "Count":       "a lord of many souls",
    "Marquis":     "a marquis of ruin",
    "Duke":        "a duke of hell",
    "Chancellor":  "the hand of the Kingdom",
}

# ─── Font helpers ─────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False, cinzel: bool = False) -> ImageFont.FreeTypeFont:
    paths = []
    if cinzel:
        paths.append(_CINZEL)
    if bold:
        paths.append(_DEJA_B)
    paths.append(_DEJA_R)
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        return len(text) * max(8, getattr(font, "size", 8) // 2)


# ─── Background ───────────────────────────────────────────────────────────────

def _draw_background(img: Image.Image):
    """Vertical dark gradient with subtle vignette."""
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


# ─── Avatar helpers ────────────────────────────────────────────────────────────

def _make_avatar_circle(avatar_bytes: Optional[bytes], size: int) -> Image.Image:
    """Return a circular RGBA avatar. Falls back to a gradient placeholder."""
    circle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask   = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)

    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((size, size), Image.LANCZOS)
            circle.paste(av, (0, 0), mask)
            return circle
        except Exception:
            pass

    # Placeholder — dark red gradient circle
    placeholder = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(placeholder)
    d.ellipse([0, 0, size - 1, size - 1], fill=(50, 10, 10))
    d.ellipse([size // 4, size // 4, size * 3 // 4, size * 3 // 4], fill=(90, 20, 20))
    placeholder.putalpha(mask)
    return placeholder


# ─── Header ───────────────────────────────────────────────────────────────────

def _draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str):
    # Decorative top bar
    draw.rectangle([0, 0, W, 3], fill=ACCENT)

    # Ornamental side lines
    for xoff in [PAD, W - PAD]:
        draw.rectangle([xoff - 1, 8, xoff + 1, HEADER_H - 8], fill=(80, 20, 20))

    # Title
    f_title = _font(30, cinzel=True)
    tw = _tw(draw, title, f_title)
    draw.text(
        ((W - tw) // 2, 22),
        title,
        font=f_title,
        fill=GOLD,
    )

    # Decorative separator under title
    line_y = 62
    draw.rectangle([PAD, line_y, W - PAD, line_y + 1], fill=(80, 24, 24))
    draw.rectangle([PAD + 60, line_y - 1, W - PAD - 60, line_y + 2], fill=ACCENT)

    # Subtitle
    f_sub = _font(14)
    tw2 = _tw(draw, subtitle, f_sub)
    draw.text(
        ((W - tw2) // 2, 72),
        subtitle,
        font=f_sub,
        fill=TEXT2,
    )

    # Bottom separator
    draw.rectangle([PAD, HEADER_H - 2, W - PAD, HEADER_H], fill=MUTED)


# ─── Single row ───────────────────────────────────────────────────────────────

def _draw_row(img: Image.Image, draw: ImageDraw.ImageDraw,
              position: int, row: dict, avatar_bytes: Optional[bytes]):
    """Draw one leaderboard row."""
    y_top = HEADER_H + (position - 1) * ROW_H
    y_bot = y_top + ROW_H

    # Alternating row background
    bg = ROW_A if position % 2 == 0 else ROW_B
    draw.rectangle([0, y_top, W, y_bot - 1], fill=bg)

    # Highlight top-3 row with a thin left accent bar
    if position <= 3:
        bar_color = MEDAL_COLORS[position - 1]
        draw.rectangle([0, y_top, 4, y_bot - 1], fill=bar_color)

    # ── Position badge ──────────────────────────────────────────────────────
    badge_cx = PAD + 22
    badge_cy = y_top + ROW_H // 2

    if position <= 3:
        bc = MEDAL_COLORS[position - 1]
        # Glowing medal circle
        draw.ellipse(
            [badge_cx - 18, badge_cy - 18, badge_cx + 18, badge_cy + 18],
            fill=(bc[0] // 4, bc[1] // 4, bc[2] // 4),
            outline=bc,
            width=2,
        )
        medals = ["1", "2", "3"]
        f_medal = _font(15, bold=True)
        lbl = medals[position - 1]
        tw = _tw(draw, lbl, f_medal)
        draw.text(
            (badge_cx - tw // 2, badge_cy - 10),
            lbl,
            font=f_medal,
            fill=bc,
        )
    else:
        f_pos = _font(14, bold=True)
        lbl = f"#{position}"
        tw = _tw(draw, lbl, f_pos)
        draw.text(
            (badge_cx - tw // 2, badge_cy - 9),
            lbl,
            font=f_pos,
            fill=TEXT2,
        )

    # ── Avatar ──────────────────────────────────────────────────────────────
    av_x = PAD + 54
    av_y = y_top + (ROW_H - AV_SZ) // 2
    av_circle = _make_avatar_circle(avatar_bytes, AV_SZ)

    # Thin ring around avatar (gold for top 3, muted otherwise)
    ring_color = MEDAL_COLORS[position - 1] if position <= 3 else MUTED
    ring = Image.new("RGBA", (AV_SZ + 4, AV_SZ + 4), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, AV_SZ + 3, AV_SZ + 3], outline=ring_color, width=2)
    img.paste(ring, (av_x - 2, av_y - 2), ring)
    img.paste(av_circle, (av_x, av_y), av_circle)

    # ── Name + Rank subtitle ────────────────────────────────────────────────
    text_x = av_x + AV_SZ + 14
    name    = row.get("username", "Unknown Soul")[:22]
    rank    = row.get("rank", "Forsaken")
    flavor  = RANK_FLAVOR.get(rank, rank)

    f_name = _font(16, bold=True)
    f_rank = _font(12)

    name_color = GOLD if position <= 3 else TEXT1
    draw.text((text_x, y_top + ROW_PAD - 1), name, font=f_name, fill=name_color)
    draw.text((text_x, y_top + ROW_PAD + 21), rank, font=f_rank, fill=ACCENT)
    draw.text(
        (text_x + _tw(draw, rank + "  ", f_rank), y_top + ROW_PAD + 21),
        f"· {flavor}",
        font=f_rank,
        fill=TEXT2,
    )

    # ── Balance (right-aligned) ─────────────────────────────────────────────
    bal = int(row.get("balance", 0))
    bal_str = f"{bal:,}"

    f_bal   = _font(14, bold=True)
    f_cur   = _font(11)
    currency_name = row.get("_currency_name", "")
    currency_icon = row.get("_currency_icon", "🪙")

    bal_w = _tw(draw, bal_str, f_bal)
    cur_w = _tw(draw, currency_name, f_cur)

    right_x = W - PAD
    draw.text((right_x - bal_w, y_top + ROW_PAD - 1), bal_str, font=f_bal, fill=GOLD_DIM)
    draw.text((right_x - cur_w, y_top + ROW_PAD + 21), currency_name, font=f_cur, fill=TEXT2)

    # Thin separator line
    if position < MAX_ROWS:
        draw.rectangle([PAD, y_bot - 1, W - PAD, y_bot], fill=MUTED)


# ─── Footer ───────────────────────────────────────────────────────────────────

def _draw_footer(draw: ImageDraw.ImageDraw, date_str: str):
    fy = HEADER_H + ROW_H * MAX_ROWS
    draw.rectangle([0, fy, W, fy + 2], fill=MUTED)
    draw.rectangle([PAD, fy + 1, W - PAD, fy + 2], fill=ACCENT)

    f_foot = _font(12)
    left_text  = f"Kingdom of Hell  ·  Kingdom Treasury"
    right_text = date_str

    draw.text((PAD, fy + 18), left_text, font=f_foot, fill=TEXT2)
    rw = _tw(draw, right_text, f_foot)
    draw.text((W - PAD - rw, fy + 18), right_text, font=f_foot, fill=TEXT2)

    draw.rectangle([0, H - 3, W, H], fill=ACCENT)


# ─── Rounded card frame ───────────────────────────────────────────────────────

def _apply_frame(img: Image.Image) -> Image.Image:
    """Mask image to rounded rectangle and add a thin border glow."""
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=255)

    result = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    result.paste(img.convert("RGBA"), (0, 0), mask)

    # Border overlay
    border_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(border_img).rounded_rectangle(
        [0, 0, W - 1, H - 1], radius=RADIUS,
        outline=(100, 12, 12, 220), width=2,
    )
    result = Image.alpha_composite(result, border_img)
    return result


# ─── Public entry point ───────────────────────────────────────────────────────

def generate_leaderboard_image(
    rows: List[dict],
    currency_name: str = "DevilCoins",
    currency_icon: str = "🪙",
    title: str = "KINGDOM LEADERBOARD",
    subtitle: str = "Top 10 · Ranked by Hierarchy & Balance",
    date_str: str = "",
    avatar_data: Optional[List[Optional[bytes]]] = None,
) -> io.BytesIO:
    """
    Generate the leaderboard image and return a BytesIO PNG.

    Args:
        rows:          List of user dicts from get_leaderboard() — up to 10 entries.
        currency_name: Server currency name (e.g. "DevilCoins").
        currency_icon: Server currency icon emoji.
        title:         Header title text.
        subtitle:      Header subtitle text.
        date_str:      Footer date string.
        avatar_data:   Parallel list of raw avatar PNG/JPG bytes (or None per slot).
    """
    if not date_str:
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    if avatar_data is None:
        avatar_data = [None] * len(rows)

    # Pad / trim
    rows        = rows[:MAX_ROWS]
    avatar_data = (list(avatar_data) + [None] * MAX_ROWS)[:MAX_ROWS]

    img  = Image.new("RGB", (W, H), BG_TOP)
    _draw_background(img)
    draw = ImageDraw.Draw(img)

    _draw_header(draw, title, subtitle)

    # Inject currency into rows for the row renderer
    enriched = [{**r, "_currency_name": currency_name, "_currency_icon": currency_icon} for r in rows]
    for i, (row, av_bytes) in enumerate(zip(enriched, avatar_data), start=1):
        _draw_row(img, draw, i, row, av_bytes)

    # Fill empty rows if fewer than 10
    for i in range(len(rows) + 1, MAX_ROWS + 1):
        fy = HEADER_H + (i - 1) * ROW_H
        col = ROW_A if i % 2 == 0 else ROW_B
        draw.rectangle([0, fy, W, fy + ROW_H - 1], fill=col)
        f_empty = _font(13)
        draw.text((PAD + 54 + AV_SZ + 14, fy + 24), "—  empty slot", font=f_empty, fill=MUTED)

    _draw_footer(draw, date_str)

    result = _apply_frame(img)

    buf = io.BytesIO()
    result.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
