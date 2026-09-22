"""
Kingdom Treasury — Infernal Mines Extraction Report Card
900 × 440 px  |  Landscape  |  Pillow

Skin-aware: visual theme is driven by the user's equipped identity card skin.
Outcome-aware: badge, Net Gain highlight, and avatar border reflect the grind result.
"""

import io
from typing import Optional
from PIL import Image, ImageDraw, ImageFilter

from .card_generator import (
    _font, _tw, _glow, _gradient, _card_mask, _t,
    _sig_star, _sig_crown, _sig_eye, _sig_sun, _sig_fleur, _sig_throne, _sig_cross,
)

# ─── Card geometry ─────────────────────────────────────────────────────────────
W, H   = 900, 440
RADIUS = 22
PAD    = 20

LEFT_W  = 230           # avatar + identity column
RIGHT_X = LEFT_W + 24   # right panel start

# ─── Outcome palette (badge + highlight — skin-independent) ────────────────────
_OUTCOME_META = {
    "failure": dict(label="NO YIELD",       accent=(80,  40,  40), glow=(55,  15, 15),  value=(145, 95,  95)),
    "meager":  dict(label="MEAGER VEIN",    accent=(140, 55,  55), glow=(100, 20, 20),  value=(195, 130, 130)),
    "common":  dict(label="STANDARD YIELD", accent=(178, 34,  34), glow=(130, 10, 10),  value=(215, 160, 160)),
    "rich":    dict(label="RICH VEIN",      accent=(195, 118,  0), glow=(150, 85,  0),  value=(235, 178, 60)),
    "jackpot": dict(label="ABYSS STRIKE",   accent=(215, 168, 42), glow=(165, 118, 0),  value=(255, 212, 80)),
}


def _fmt_dc(n: int) -> str:
    return f"{n:,} DC"


# ─── Skin-aware helpers ────────────────────────────────────────────────────────

def _line(draw: ImageDraw.ImageDraw, y: int, theme: dict,
          alpha: int = 55, x1: int = PAD, x2: int = W - PAD):
    draw.line([(x1, y), (x2, y)], fill=(*theme["border"][:3], alpha), width=1)


def _double_line(draw: ImageDraw.ImageDraw, y: int, theme: dict):
    draw.line([(PAD, y), (W - PAD, y)], fill=(*theme["border"][:3], 80), width=1)
    draw.line([(PAD, y + 3), (W - PAD, y + 3)], fill=(*theme["border"][:3], 25), width=1)


def _bg_sigil(card: Image.Image, theme: dict):
    """Faint background sigil — uses skin's sigil type and glow color."""
    cx, cy, r = 690, 220, 165
    stype = theme.get("sigil", "star")

    _DISPATCH = {
        "star":   _sig_star,
        "crown":  _sig_crown,
        "eye":    _sig_eye,
        "sun":    _sig_sun,
        "fleur":  _sig_fleur,
        "throne": _sig_throne,
        "sigil":  _sig_cross,
    }
    fn = _DISPATCH.get(stype, _sig_star)

    for alpha, blur in [(38, 28), (18, 8)]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        col = (*theme["glow"][:3], alpha)
        fn(d, cx, cy, r, col)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        card.alpha_composite(layer)


def _paste_avatar(card: Image.Image, av_bytes: Optional[bytes], sz: int,
                  x: int, y: int, accent: tuple, theme: dict):
    """Rounded avatar with outcome-accented glow border."""
    if av_bytes:
        try:
            av = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((sz, sz), Image.LANCZOS)
        except Exception:
            av = _make_placeholder(sz, accent, theme)
    else:
        av = _make_placeholder(sz, accent, theme)

    mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)], radius=14, fill=255)
    av.putalpha(mask)

    bsz = sz + 10
    border = Image.new("RGBA", (bsz, bsz), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (bsz - 1, bsz - 1)], radius=17,
        outline=(*accent[:3], 210), width=3,
    )
    card.alpha_composite(border.filter(ImageFilter.GaussianBlur(6)), (x - 5, y - 5))
    card.alpha_composite(border, (x - 5, y - 5))
    card.alpha_composite(av, (x, y))


def _make_placeholder(sz: int, accent: tuple, theme: dict) -> Image.Image:
    av = Image.new("RGBA", (sz, sz), (*theme["bg2"][:3], 255))
    d  = ImageDraw.Draw(av)
    c  = (*accent[:3], 155)
    m  = sz // 2
    d.ellipse([(m - 18, 12), (m + 18, 50)], fill=c)
    d.ellipse([(m - 30, 54), (m + 30, sz - 4)], fill=c)
    return av


def _stat_row(card: Image.Image, draw: ImageDraw.ImageDraw,
              label: str, value: str,
              y: int, value_color: tuple,
              theme: dict,
              highlighted: bool = False,
              outcome_accent: Optional[tuple] = None):
    lf = _font(13)
    vf = _font(22, bold=True)

    if highlighted and outcome_accent:
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(hl).rounded_rectangle(
            [(RIGHT_X - 4, y - 8), (W - PAD, y + 36)],
            radius=8, fill=(*outcome_accent[:3], 28),
        )
        card.alpha_composite(hl)
        draw = ImageDraw.Draw(card)

    draw.text((RIGHT_X, y + 2), label, font=lf, fill=(*theme["text2"][:3], 185))

    vw = _tw(draw, value, vf)
    if highlighted and outcome_accent:
        _glow(card, (W - PAD - vw, y - 3), value, vf,
              (*value_color[:3], 255), (*outcome_accent[:3], 255),
              blur=12, spread=2)
        draw = ImageDraw.Draw(card)
    else:
        draw.text((W - PAD - vw, y - 3), value, font=vf, fill=(*value_color[:3], 255))


# ─── Main generator ────────────────────────────────────────────────────────────

def generate_grind_card(
    username:     str,
    rank:         str,
    outcome:      str,
    extraction:   int,
    flat_bonus:   int,
    tax:          int,
    eff_rate:     float,
    net:          int,
    balance:      int,
    avatar_bytes: Optional[bytes] = None,
    skin_id:      Optional[str]   = None,
) -> io.BytesIO:

    theme  = _t(skin_id)
    meta   = _OUTCOME_META.get(outcome, _OUTCOME_META["common"])
    o_acc  = meta["accent"]   # outcome accent — drives badge + highlight
    o_glow = meta["glow"]
    o_val  = meta["value"]    # Net Gain value color

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = _gradient(W, H, theme["bg1"], theme["bg2"])
    _bg_sigil(card, theme)
    draw = ImageDraw.Draw(card)

    # ── Card border (skin-driven) ────────────────────────────────────────────
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*theme["border"][:3], 220), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*theme["border"][:3], 38), width=1)

    # ── HEADER ──────────────────────────────────────────────────────────────
    hf   = _font(9, cinzel=True)
    htxt = "KINGDOM  OF  HELL    ·    INFERNAL  MINES  —  EXTRACTION  REPORT"
    draw.text(((W - _tw(draw, htxt, hf)) // 2, 14),
              htxt, font=hf, fill=(*theme["text2"][:3], 145))

    # Outcome badge — top right (always outcome-colored for reward clarity)
    badge_f = _font(11, bold=True, cinzel=True)
    badge_w = _tw(draw, meta["label"], badge_f)
    _glow(card, (W - PAD - badge_w, 10), meta["label"], badge_f,
          (*o_acc[:3], 255), (*o_glow[:3], 255), blur=10, spread=2)
    draw = ImageDraw.Draw(card)

    _double_line(draw, 44, theme)

    # ── LEFT — Avatar + Identity ─────────────────────────────────────────────
    av_sz = 134
    av_x  = (LEFT_W - av_sz) // 2
    av_y  = 58
    _paste_avatar(card, avatar_bytes, av_sz, av_x, av_y, o_acc, theme)
    draw = ImageDraw.Draw(card)

    # Column divider
    draw.line([(LEFT_W, 44), (LEFT_W, H - PAD)],
              fill=(*theme["border"][:3], 40), width=1)

    # Username
    uf = _font(16, bold=True)
    uw = _tw(draw, username, uf)
    draw.text(((LEFT_W - uw) // 2, av_y + av_sz + 12),
              username, font=uf, fill=(*theme["text1"][:3], 230))

    # Rank (skin accent color gives it personality)
    rf = _font(11)
    draw.text(((LEFT_W - _tw(draw, rank, rf)) // 2, av_y + av_sz + 35),
              rank, font=rf, fill=(*theme["text2"][:3], 170))

    # ── RIGHT — Stats panel ──────────────────────────────────────────────────
    section_f = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "EXTRACTION  REPORT",
              font=section_f, fill=(*theme["text2"][:3], 110))

    _line(draw, 84, theme, alpha=40, x1=RIGHT_X, x2=W - PAD)

    # ── Build stat strings ───────────────────────────────────────────────────
    raw = extraction - flat_bonus
    ex_str  = f"+{_fmt_dc(raw)}  +{_fmt_dc(flat_bonus)} bonus" if flat_bonus else f"+{_fmt_dc(raw)}"
    tax_str = "Exempt" if (tax == 0 or eff_rate == 0) else f"−{_fmt_dc(tax)}  ({int(round(eff_rate * 100))}%)"
    net_str = f"+{_fmt_dc(net)}"
    bal_str = _fmt_dc(balance)

    # Skin-sourced colors for normal rows
    t1 = theme["text1"]
    t2 = theme["text2"]

    rows = [
        ("🪨  Extraction",  ex_str,  t1,  False),
        ("⚖  Tax Applied",  tax_str, t2,  False),
        ("🔥  Net Gain",     net_str, o_val, True),   # outcome-colored highlight
        ("💼  Wallet After", bal_str, t1,  False),
    ]

    ROW_H = 68
    for i, (label, value, vcol, highlighted) in enumerate(rows):
        y = 96 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, theme,
                  highlighted=highlighted, outcome_accent=o_acc)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _line(draw, y + 54, theme, alpha=25, x1=RIGHT_X, x2=W - PAD)

    # ── FOOTER ──────────────────────────────────────────────────────────────
    _double_line(draw, H - 38, theme)
    ff   = _font(9)
    ftxt = "Recorded by the Kingdom Treasury  ·  Kingdom of Hell"
    fw   = _tw(draw, ftxt, ff)
    draw.text((W - PAD - fw, H - 26), ftxt, font=ff, fill=(*theme["text2"][:3], 110))

    # ── Rounded clip ────────────────────────────────────────────────────────
    card.putalpha(_card_mask(W, H, RADIUS))

    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
