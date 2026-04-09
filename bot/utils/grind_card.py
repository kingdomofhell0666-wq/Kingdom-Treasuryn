"""
Kingdom Treasury — Infernal Mines Extraction Report Card
900 × 440 px  |  Landscape  |  Pillow
Used as the final /grind result image.
"""

import io
import math
from typing import Optional
from PIL import Image, ImageDraw, ImageFilter

from .card_generator import (
    _font, _tw, _glow, _gradient, _card_mask, fetch_avatar,
    _CINZEL, _DEJA_B, _DEJA_R,
)

# ─── Card geometry ─────────────────────────────────────────────────────────────
W, H   = 900, 440
RADIUS = 22
PAD    = 20

LEFT_W  = 230           # avatar + identity column
RIGHT_X = LEFT_W + 24   # right panel start
INNER_W = W - RIGHT_X - PAD   # right panel usable width

# ─── Outcome palette ───────────────────────────────────────────────────────────
_OUTCOME_META = {
    "failure": dict(
        label="NO YIELD",
        accent=(80,  40,  40),
        glow  =(55,  15,  15),
        value =(145, 95,  95),
    ),
    "meager": dict(
        label="MEAGER VEIN",
        accent=(140, 55,  55),
        glow  =(100, 20,  20),
        value =(195, 130, 130),
    ),
    "common": dict(
        label="STANDARD YIELD",
        accent=(178, 34,  34),
        glow  =(130, 10,  10),
        value =(215, 160, 160),
    ),
    "rich": dict(
        label="RICH VEIN",
        accent=(195, 118, 0),
        glow  =(150, 85,  0),
        value =(235, 178, 60),
    ),
    "jackpot": dict(
        label="ABYSS STRIKE",
        accent=(215, 168, 42),
        glow  =(165, 118, 0),
        value =(255, 212, 80),
    ),
}

_BG1 = (8,  3,  3)
_BG2 = (20, 7,  7)
_BORDER   = (110, 0,  0)
_TEXT1    = (232, 210, 210)
_TEXT2    = (148, 100, 100)
_DIVIDER  = (90,  18,  18)


def _fmt_dc(n: int) -> str:
    return f"{n:,} DC"


def _line(draw: ImageDraw.ImageDraw, y: int, alpha: int = 55,
          x1: int = PAD, x2: int = W - PAD):
    draw.line([(x1, y), (x2, y)], fill=(*_DIVIDER, alpha), width=1)


def _double_line(draw: ImageDraw.ImageDraw, y: int):
    draw.line([(PAD, y), (W - PAD, y)], fill=(*_DIVIDER, 80), width=1)
    draw.line([(PAD, y + 3), (W - PAD, y + 3)], fill=(*_DIVIDER, 25), width=1)


def _bg_sigil(card: Image.Image):
    """Faint infernal cross sigil in the right background."""
    cx, cy, r = 690, 220, 180
    for alpha, blur in [(40, 28), (20, 8)]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        col = (*_BORDER, alpha)
        # Circle
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=2)
        d.ellipse([(cx - r + 14, cy - r + 14), (cx + r - 14, cy + r - 14)],
                  outline=(*_BORDER, alpha // 2), width=1)
        # Cross arms
        arm = r - 6
        thick = 7
        d.rectangle([(cx - thick, cy - arm), (cx + thick, cy + arm)], fill=col)
        d.rectangle([(cx - arm, cy - thick), (cx + arm, cy + thick)], fill=col)
        # End circles
        for ex_, ey_ in [(cx, cy - arm), (cx, cy + arm),
                         (cx - arm, cy), (cx + arm, cy)]:
            d.ellipse([(ex_ - 7, ey_ - 7), (ex_ + 7, ey_ + 7)], fill=col)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        card.alpha_composite(layer)


def _paste_avatar(card: Image.Image, av_bytes: Optional[bytes], sz: int,
                  x: int, y: int, accent: tuple):
    """Paste rounded avatar with accent glow border."""
    if av_bytes:
        try:
            av = Image.open(io.BytesIO(av_bytes)).convert("RGBA")
            av = av.resize((sz, sz), Image.LANCZOS)
        except Exception:
            av = _make_placeholder(sz, accent)
    else:
        av = _make_placeholder(sz, accent)

    mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)],
                                            radius=14, fill=255)
    av.putalpha(mask)

    # Glow border
    bsz = sz + 10
    border = Image.new("RGBA", (bsz, bsz), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (bsz - 1, bsz - 1)], radius=17,
        outline=(*accent[:3], 200), width=3,
    )
    blurred = border.filter(ImageFilter.GaussianBlur(6))
    card.alpha_composite(blurred, (x - 5, y - 5))
    card.alpha_composite(border,  (x - 5, y - 5))
    card.alpha_composite(av,       (x,     y))


def _make_placeholder(sz: int, accent: tuple) -> Image.Image:
    av = Image.new("RGBA", (sz, sz), (*_BG2, 255))
    d  = ImageDraw.Draw(av)
    c  = (*accent[:3], 155)
    m  = sz // 2
    d.ellipse([(m - 18, 12), (m + 18, 50)], fill=c)
    d.ellipse([(m - 30, 54), (m + 30, sz - 4)], fill=c)
    return av


def _stat_row(card: Image.Image, draw: ImageDraw.ImageDraw,
              label: str, value: str,
              y: int, value_color: tuple,
              highlighted: bool = False,
              accent: Optional[tuple] = None):
    """Draw one stat row: label left, value right."""
    lf = _font(13, bold=False)
    vf = _font(22, bold=True)

    if highlighted and accent:
        # Subtle highlight box
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hl)
        hd.rounded_rectangle(
            [(RIGHT_X - 4, y - 8), (W - PAD, y + 36)],
            radius=8, fill=(*accent[:3], 28),
        )
        card.alpha_composite(hl)
        draw = ImageDraw.Draw(card)

    draw.text((RIGHT_X, y + 2), label, font=lf, fill=(*_TEXT2, 190))
    vw = _tw(draw, value, vf)
    if highlighted and accent:
        _glow(card, (W - PAD - vw, y - 3), value, vf,
              (*value_color[:3], 255), (*accent[:3], 255),
              blur=12, spread=2)
        draw = ImageDraw.Draw(card)
    else:
        draw.text((W - PAD - vw, y - 3), value, font=vf,
                  fill=(*value_color[:3], 255))


# ─── Main generator ────────────────────────────────────────────────────────────

def generate_grind_card(
    username:   str,
    rank:       str,
    outcome:    str,
    extraction: int,
    flat_bonus: int,
    tax:        int,
    eff_rate:   float,
    net:        int,
    balance:    int,
    avatar_bytes: Optional[bytes] = None,
) -> io.BytesIO:

    meta = _OUTCOME_META.get(outcome, _OUTCOME_META["common"])
    accent = meta["accent"]
    glow_c = meta["glow"]
    val_c  = meta["value"]

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = _gradient(W, H, _BG1, _BG2)
    _bg_sigil(card)
    draw = ImageDraw.Draw(card)

    # ── Card border ─────────────────────────────────────────────────────────
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*_BORDER, 220), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*_BORDER, 38), width=1)

    # ── HEADER ──────────────────────────────────────────────────────────────
    hf   = _font(9, cinzel=True)
    htxt = "KINGDOM  OF  HELL    ·    INFERNAL  MINES  —  EXTRACTION  REPORT"
    draw.text(((W - _tw(draw, htxt, hf)) // 2, 14),
              htxt, font=hf, fill=(*_TEXT2, 145))

    # Outcome badge — top right
    badge_f = _font(11, bold=True, cinzel=True)
    badge_w = _tw(draw, meta["label"], badge_f)
    _glow(card, (W - PAD - badge_w, 10), meta["label"], badge_f,
          (*accent[:3], 255), (*glow_c[:3], 255), blur=10, spread=2)
    draw = ImageDraw.Draw(card)

    _double_line(draw, 44)

    # ── LEFT — Avatar + Identity ─────────────────────────────────────────────
    av_sz = 134
    av_x  = (LEFT_W - av_sz) // 2
    av_y  = 58
    _paste_avatar(card, avatar_bytes, av_sz, av_x, av_y, accent)
    draw = ImageDraw.Draw(card)

    # Vertical divider between columns
    draw.line([(LEFT_W, 44), (LEFT_W, H - PAD)], fill=(*_DIVIDER, 45), width=1)

    # Username
    uf = _font(16, bold=True)
    uw = _tw(draw, username, uf)
    draw.text(((LEFT_W - uw) // 2, av_y + av_sz + 12),
              username, font=uf, fill=(*_TEXT1, 230))

    # Rank
    rf  = _font(11)
    draw.text(((LEFT_W - _tw(draw, rank, rf)) // 2, av_y + av_sz + 35),
              rank, font=rf, fill=(*_TEXT2, 175))

    # ── RIGHT — Stats panel ──────────────────────────────────────────────────
    section_f = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "EXTRACTION  REPORT",
              font=section_f, fill=(*_TEXT2, 110))

    _line(draw, 84, alpha=40, x1=RIGHT_X, x2=W - PAD)

    # Build stat values
    raw = extraction - flat_bonus
    if flat_bonus:
        ex_str = f"+{_fmt_dc(raw)}  +{_fmt_dc(flat_bonus)} bonus"
    else:
        ex_str = f"+{_fmt_dc(raw)}"

    if tax == 0 or eff_rate == 0:
        tax_str = "Exempt"
    else:
        pct     = int(round(eff_rate * 100))
        tax_str = f"−{_fmt_dc(tax)}  ({pct}%)"

    net_str = f"+{_fmt_dc(net)}"
    bal_str = _fmt_dc(balance)

    # Stat rows
    ROW_H = 68
    rows = [
        ("🪨  Extraction",  ex_str,  _TEXT1,  False),
        ("⚖  Tax Applied",  tax_str, _TEXT2,  False),
        ("🔥  Net Gain",     net_str, val_c,   True),
        ("💼  Wallet After", bal_str, _TEXT1,  False),
    ]

    for i, (label, value, vcol, highlighted) in enumerate(rows):
        y = 96 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol,
                  highlighted=highlighted, accent=accent)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _line(draw, y + 54, alpha=28, x1=RIGHT_X, x2=W - PAD)

    # ── FOOTER ──────────────────────────────────────────────────────────────
    _double_line(draw, H - 38)
    ff  = _font(9)
    ftxt = "Recorded by the Kingdom Treasury  ·  Kingdom of Hell"
    fw   = _tw(draw, ftxt, ff)
    draw.text((W - PAD - fw, H - 26), ftxt,
              font=ff, fill=(*_TEXT2, 115))

    # ── Clip to rounded rect ─────────────────────────────────────────────────
    card.putalpha(_card_mask(W, H, RADIUS))

    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
