"""
Kingdom Treasury — Result Image Cards
Generated for: /tribute  /wealth  /transfer  /ascend
900 × 440 px  |  Landscape  |  Pillow  |  Skin-aware
"""

import io
import math
from typing import Optional
from PIL import Image, ImageDraw, ImageFilter

from .card_generator import (
    _font, _tw, _glow, _gradient, _card_mask, THEMES, _t, fetch_avatar,
    _sig_star, _sig_crown, _sig_eye, _sig_sun, _sig_fleur, _sig_throne, _sig_cross,
)

# ─── Shared geometry (matches grind_card.py) ──────────────────────────────────
W, H    = 900, 440
RADIUS  = 22
PAD     = 20
LEFT_W  = 230
RIGHT_X = LEFT_W + 24

_SIG_DISPATCH = {
    "star": _sig_star, "crown": _sig_crown, "eye": _sig_eye,
    "sun":  _sig_sun,  "fleur": _sig_fleur, "throne": _sig_throne,
    "sigil": _sig_cross,
}


def _fmt(n: int) -> str:
    return f"{n:,} DC"


# ─── Shared drawing helpers ────────────────────────────────────────────────────

def _hline(draw: ImageDraw.ImageDraw, y: int, th: dict, alpha=55, x1=PAD, x2=W - PAD):
    draw.line([(x1, y), (x2, y)], fill=(*th["border"][:3], alpha), width=1)


def _dline(draw: ImageDraw.ImageDraw, y: int, th: dict):
    draw.line([(PAD, y), (W - PAD, y)], fill=(*th["border"][:3], 80), width=1)
    draw.line([(PAD, y + 3), (W - PAD, y + 3)], fill=(*th["border"][:3], 25), width=1)


def _sigil(card: Image.Image, th: dict, cx=690, cy=220, r=165):
    fn = _SIG_DISPATCH.get(th.get("sigil", "star"), _sig_star)
    for alpha, blur in [(38, 28), (18, 8)]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer), cx, cy, r, (*th["glow"][:3], alpha))
        card.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def _avatar_col(card: Image.Image, av_bytes: Optional[bytes], th: dict,
                username: str, sub: str, accent: tuple):
    """Draw avatar + username + subtitle into the left column."""
    sz = 134
    x  = (LEFT_W - sz) // 2
    y  = 58

    # Placeholder or real avatar
    if av_bytes:
        try:
            av = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((sz, sz), Image.LANCZOS)
        except Exception:
            av = _blank_av(sz, th, accent)
    else:
        av = _blank_av(sz, th, accent)

    mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)], radius=14, fill=255)
    av.putalpha(mask)

    bsz    = sz + 10
    border = Image.new("RGBA", (bsz, bsz), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (bsz - 1, bsz - 1)], radius=17,
        outline=(*accent[:3], 210), width=3,
    )
    card.alpha_composite(border.filter(ImageFilter.GaussianBlur(6)), (x - 5, y - 5))
    card.alpha_composite(border, (x - 5, y - 5))
    card.alpha_composite(av, (x, y))

    draw = ImageDraw.Draw(card)
    # Column divider
    draw.line([(LEFT_W, 44), (LEFT_W, H - PAD)],
              fill=(*th["border"][:3], 40), width=1)
    # Username
    uf = _font(16, bold=True)
    uw = _tw(draw, username, uf)
    draw.text(((LEFT_W - uw) // 2, y + sz + 12),
              username, font=uf, fill=(*th["text1"][:3], 225))
    # Sub-label (rank or descriptor)
    sf = _font(11)
    sw = _tw(draw, sub, sf)
    draw.text(((LEFT_W - sw) // 2, y + sz + 35),
              sub, font=sf, fill=(*th["text2"][:3], 165))


def _blank_av(sz: int, th: dict, accent: tuple) -> Image.Image:
    av = Image.new("RGBA", (sz, sz), (*th["bg2"][:3], 255))
    d  = ImageDraw.Draw(av)
    c  = (*accent[:3], 155)
    m  = sz // 2
    d.ellipse([(m - 18, 12), (m + 18, 50)], fill=c)
    d.ellipse([(m - 30, 54), (m + 30, sz - 4)], fill=c)
    return av


def _base_canvas(th: dict, header_txt: str, badge_txt: str,
                 badge_col: tuple, badge_glow: tuple) -> tuple:
    """Build canvas through the top divider. Returns (card, draw)."""
    card = _gradient(W, H, th["bg1"], th["bg2"])
    _sigil(card, th)
    draw = ImageDraw.Draw(card)

    # Outer border
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*th["border"][:3], 220), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*th["border"][:3], 38), width=1)

    # Header text (centre)
    hf = _font(9, cinzel=True)
    draw.text(((W - _tw(draw, header_txt, hf)) // 2, 14),
              header_txt, font=hf, fill=(*th["text2"][:3], 140))

    # Badge (top-right)
    bf  = _font(11, bold=True, cinzel=True)
    bw  = _tw(draw, badge_txt, bf)
    _glow(card, (W - PAD - bw, 10), badge_txt, bf,
          (*badge_col[:3], 255), (*badge_glow[:3], 255), blur=10, spread=2)
    draw = ImageDraw.Draw(card)

    _dline(draw, 44, th)
    return card, draw


def _stat_row(card: Image.Image, draw: ImageDraw.ImageDraw,
              label: str, value: str, y: int, vcol: tuple, th: dict,
              highlighted=False, hl_accent: Optional[tuple] = None):
    lf = _font(13)
    vf = _font(22, bold=True)

    if highlighted and hl_accent:
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(hl).rounded_rectangle(
            [(RIGHT_X - 4, y - 8), (W - PAD, y + 36)],
            radius=8, fill=(*hl_accent[:3], 28),
        )
        card.alpha_composite(hl)
        draw = ImageDraw.Draw(card)

    draw.text((RIGHT_X, y + 2), label, font=lf, fill=(*th["text2"][:3], 180))
    vw = _tw(draw, value, vf)
    if highlighted and hl_accent:
        _glow(card, (W - PAD - vw, y - 3), value, vf,
              (*vcol[:3], 255), (*hl_accent[:3], 255), blur=12, spread=2)
        draw = ImageDraw.Draw(card)
    else:
        draw.text((W - PAD - vw, y - 3), value, font=vf, fill=(*vcol[:3], 255))


def _finish(card: Image.Image, draw: ImageDraw.ImageDraw, th: dict) -> io.BytesIO:
    _dline(draw, H - 38, th)
    ff   = _font(9)
    ftxt = "Recorded by the Kingdom Treasury  ·  Kingdom of Hell"
    fw   = _tw(draw, ftxt, ff)
    draw.text((W - PAD - fw, H - 26), ftxt, font=ff, fill=(*th["text2"][:3], 108))
    card.putalpha(_card_mask(W, H, RADIUS))
    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
# 1.  TRIBUTE  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_tribute_card(
    username: str,
    rank: str,
    gross: int,
    bonus: int,
    tax: int,
    tax_rate: float,
    net: int,
    balance: int,
    avatar_bytes: Optional[bytes] = None,
    skin_id: Optional[str] = None,
) -> io.BytesIO:

    th     = _t(skin_id)
    accent = th["accent"]
    gold   = th["gold"]

    card, draw = _base_canvas(
        th,
        header_txt  = "KINGDOM  OF  HELL    ·    DAILY  TRIBUTE",
        badge_txt   = "TRIBUTE  RECEIVED",
        badge_col   = gold,
        badge_glow  = th["glow"],
    )

    _avatar_col(card, avatar_bytes, th, username, rank, accent)
    draw = ImageDraw.Draw(card)

    # Section label
    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "TRIBUTE  BREAKDOWN",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    bonus_str  = f"+{_fmt(bonus)}" if bonus else "None"
    tax_str    = f"−{_fmt(tax)}  ({int(round(tax_rate * 100))}%)" if tax else "Exempt"
    net_str    = f"+{_fmt(net)}"
    bal_str    = _fmt(balance)

    rows = [
        ("📜  Base Grant",   f"+{_fmt(gross - bonus)}", th["text1"], False),
        ("⚔  Grind Bonus",   bonus_str,                 th["text2"], False),
        ("⚖  Tax Withheld",  tax_str,                   th["text2"], False),
        ("🔥  Net Received",  net_str,                   gold,        True),
        ("💼  Wallet After",  bal_str,                   th["text1"], False),
    ]

    ROW_H = 54
    for i, (label, value, vcol, hl) in enumerate(rows):
        y = 94 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, th, highlighted=hl, hl_accent=accent)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _hline(draw, y + 44, th, alpha=22, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 2.  WEALTH  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_wealth_card(
    username: str,
    rank: str,
    balance: int,
    taxes_paid: int,
    kingdom_rank: int,
    risk_score: int,
    avatar_bytes: Optional[bytes] = None,
    skin_id: Optional[str] = None,
) -> io.BytesIO:

    th     = _t(skin_id)
    accent = th["accent"]
    gold   = th["gold"]

    # Risk label
    if risk_score >= 51:
        risk_lbl, risk_col = "FLAGGED", (220, 50, 50)
    elif risk_score <= 20 and taxes_paid > 0:
        risk_lbl, risk_col = "CLEARED", (80, 200, 80)
    else:
        risk_lbl, risk_col = "NEUTRAL", th["text2"]

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    BALANCE  STATEMENT",
        badge_txt  = "TREASURY  RECORD",
        badge_col  = gold,
        badge_glow = th["glow"],
    )

    _avatar_col(card, avatar_bytes, th, username, rank, accent)
    draw = ImageDraw.Draw(card)

    # Section label
    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "CURRENT  STANDING",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    # Large balance display (centrepiece of right panel)
    bf   = _font(46, bold=True)
    bval = _fmt(balance)
    bw   = _tw(draw, bval, bf)
    bx   = W - PAD - bw
    _glow(card, (bx, 94), bval, bf,
          (*gold[:3], 255), (*th["glow"][:3], 255), blur=16, spread=3)
    draw = ImageDraw.Draw(card)

    # Balance label
    bl = _font(10, cinzel=True)
    blbl = "WALLET  BALANCE"
    draw.text((RIGHT_X, 100), blbl, font=bl,
              fill=(*th["text2"][:3], 130))

    _hline(draw, 165, th, alpha=30, x1=RIGHT_X, x2=W - PAD)

    # Supporting rows
    rows = [
        ("🏴  Rank",           rank,                th["text1"]),
        ("⚖  Taxes Rendered",  _fmt(taxes_paid),    th["text2"]),
        ("🔱  Kingdom Rank",    f"#{kingdom_rank}",  th["text1"]),
        ("☠  Audit Status",    risk_lbl,            risk_col),
    ]
    ROW_H = 58
    for i, (label, value, vcol) in enumerate(rows):
        y = 174 + i * ROW_H
        lf = _font(12)
        vf = _font(18, bold=True)
        draw.text((RIGHT_X, y + 4), label, font=lf, fill=(*th["text2"][:3], 170))
        vw = _tw(draw, value, vf)
        draw.text((W - PAD - vw, y), value, font=vf, fill=(*vcol[:3], 230))
        if i < len(rows) - 1:
            _hline(draw, y + 46, th, alpha=18, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  TRANSFER  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_transfer_card(
    sender_name: str,
    sender_rank: str,
    recipient_name: str,
    amount: int,
    tax: int,
    net_to_recipient: int,
    sender_balance: int,
    avatar_bytes: Optional[bytes] = None,
    skin_id: Optional[str] = None,
) -> io.BytesIO:

    th     = _t(skin_id)
    accent = th["accent"]
    gold   = th["gold"]

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    TRANSFER  LEDGER",
        badge_txt  = "FUNDS  DISPATCHED",
        badge_col  = accent,
        badge_glow = th["glow"],
    )

    _avatar_col(card, avatar_bytes, th, sender_name, sender_rank, accent)
    draw = ImageDraw.Draw(card)

    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "TRANSACTION  RECORD",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    tax_str = f"−{_fmt(tax)}  (2%)" if tax else "Exempt"
    net_str = f"+{_fmt(net_to_recipient)}"
    bal_str = _fmt(sender_balance)

    rows = [
        ("💸  Amount Sent",        f"{_fmt(amount)}",  th["text1"], False),
        ("⚖  Transfer Tax",        tax_str,            th["text2"], False),
        (f"→  Net to {recipient_name[:14]}", net_str, gold,        True),
        ("💼  Wallet After",        bal_str,            th["text1"], False),
    ]

    ROW_H = 65
    for i, (label, value, vcol, hl) in enumerate(rows):
        y = 94 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, th, highlighted=hl, hl_accent=accent)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _hline(draw, y + 54, th, alpha=22, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 4.  ASCEND  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_ascend_card(
    username: str,
    old_rank: str,
    new_rank: str,
    cost: int,
    balance: int,
    avatar_bytes: Optional[bytes] = None,
    skin_id: Optional[str] = None,
) -> io.BytesIO:

    th     = _t(skin_id)
    accent = th["accent"]
    gold   = th["gold"]

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    RANK  ASCENSION",
        badge_txt  = "ASCENDED",
        badge_col  = gold,
        badge_glow = th["glow"],
    )

    # Avatar column — show new rank as the sub-label
    _avatar_col(card, avatar_bytes, th, username, f"↑  {new_rank}", gold)
    draw = ImageDraw.Draw(card)

    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "ASCENSION  RECORD",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    # New rank — large centrepiece
    rf   = _font(38, bold=True, cinzel=True)
    rw   = _tw(draw, new_rank.upper(), rf)
    rx   = W - PAD - rw
    # Highlight box
    hl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hl_layer).rounded_rectangle(
        [(RIGHT_X - 4, 92), (W - PAD, 155)],
        radius=10, fill=(*gold[:3], 18),
    )
    card.alpha_composite(hl_layer)
    _glow(card, (rx, 94), new_rank.upper(), rf,
          (*gold[:3], 255), (*th["glow"][:3], 255), blur=18, spread=3)
    draw = ImageDraw.Draw(card)

    # Rank sub-label
    rl = _font(9, cinzel=True)
    draw.text((RIGHT_X, 98), "NEW  RANK", font=rl,
              fill=(*th["text2"][:3], 120))

    _hline(draw, 166, th, alpha=30, x1=RIGHT_X, x2=W - PAD)

    # Supporting rows
    rows = [
        ("🔼  Ascended From",  old_rank,        th["text2"]),
        ("💰  Cost Paid",      f"−{_fmt(cost)}", th["text2"]),
        ("💼  Wallet After",   _fmt(balance),    th["text1"]),
    ]
    ROW_H = 68
    for i, (label, value, vcol) in enumerate(rows):
        y = 176 + i * ROW_H
        lf = _font(12)
        vf = _font(20, bold=True)
        draw.text((RIGHT_X, y + 4), label, font=lf, fill=(*th["text2"][:3], 170))
        vw = _tw(draw, value, vf)
        draw.text((W - PAD - vw, y + 2), value, font=vf, fill=(*vcol[:3], 230))
        if i < len(rows) - 1:
            _hline(draw, y + 54, th, alpha=20, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)
