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
        ("🔱  Kingdom Rank",    f"#{kingdom_rank}" if kingdom_rank > 0 else "EXEMPT",  th["text1"]),
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


# ══════════════════════════════════════════════════════════════════════════════
# INVESTMENT CARDS  (/invest  /portfolio  /collect  /withdraw)
# ══════════════════════════════════════════════════════════════════════════════

# Risk palette — badge colours for invest cards
_RISK_META = {
    "safe":   dict(label="SAFE  INVESTMENT", badge_col=(165, 138, 30), badge_glow=(90, 72, 5)),
    "medium": dict(label="MEDIUM  RISK",     badge_col=(195, 118, 0),  badge_glow=(130, 68, 0)),
    "risky":  dict(label="HIGH  RISK",       badge_col=(185, 22,  22), badge_glow=(110, 8,  8)),
}

# ─── Utility: format timedelta ────────────────────────────────────────────────

def _fmt_td(td) -> str:
    total = int(td.total_seconds())
    if total <= 0:
        return "Matured"
    h, rem = divmod(total, 3600)
    m = rem // 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


# ══════════════════════════════════════════════════════════════════════════════
# 5.  INVEST  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_invest_card(
    username:       str,
    rank:           str,
    inv_type:       str,            # "safe" / "medium" / "risky"
    type_label:     str,
    amount:         int,
    maturity_hours: int,
    new_balance:    int,
    avatar_bytes:   Optional[bytes] = None,
    skin_id:        Optional[str]   = None,
) -> io.BytesIO:

    th   = _t(skin_id)
    rm   = _RISK_META.get(inv_type, _RISK_META["safe"])
    gold = th["gold"]

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    INFERNAL  MARKETS",
        badge_txt  = rm["label"],
        badge_col  = rm["badge_col"],
        badge_glow = rm["badge_glow"],
    )

    _avatar_col(card, avatar_bytes, th, username, rank, rm["badge_col"])
    draw = ImageDraw.Draw(card)

    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "INVESTMENT  COMMITTED",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    mat_str  = f"{maturity_hours}h"
    amt_str  = _fmt(amount)
    bal_str  = _fmt(new_balance)

    rows = [
        ("📊  Type",           type_label, th["text1"],         False),
        ("💰  Amount Committed", f"−{amt_str}", rm["badge_col"], False),
        ("⏳  Matures In",     mat_str,    th["text2"],         False),
        ("💼  Wallet After",   bal_str,    gold,                True),
    ]
    ROW_H = 68
    for i, (label, value, vcol, hl) in enumerate(rows):
        y = 94 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, th, highlighted=hl, hl_accent=rm["badge_col"])
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _hline(draw, y + 54, th, alpha=22, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 6.  PORTFOLIO  CARD  (full-width table, no avatar column)
# ══════════════════════════════════════════════════════════════════════════════

def generate_portfolio_card(
    username:    str,
    investments: list,          # from get_portfolio()
    skin_id:     Optional[str] = None,
) -> io.BytesIO:

    th    = _t(skin_id)
    gold  = th["gold"]
    acc   = th["accent"]

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    INFERNAL  MARKETS",
        badge_txt  = "PORTFOLIO",
        badge_col  = gold,
        badge_glow = th["glow"],
    )
    draw = ImageDraw.Draw(card)

    # Owner label
    uf = _font(14, bold=True)
    draw.text((PAD + 8, 56), username, font=uf, fill=(*th["text1"][:3], 200))

    _hline(draw, 84, th, alpha=38)

    if not investments:
        # Empty state
        ef  = _font(16)
        etxt = "No active investments in the infernal markets."
        ew   = _tw(draw, etxt, ef)
        draw.text(((W - ew) // 2, H // 2 - 14), etxt,
                  font=ef, fill=(*th["text2"][:3], 150))
        return _finish(card, draw, th)

    # Table header
    COL_X = [PAD + 8, 230, 450, 620, 760]
    TH_Y  = 95
    hf = _font(9, cinzel=True)
    for txt, x in zip(["TYPE", "PRINCIPAL", "RETURN RANGE", "STATUS", "MATURES IN"], COL_X):
        draw.text((x, TH_Y), txt, font=hf, fill=(*th["text2"][:3], 120))

    _hline(draw, TH_Y + 18, th, alpha=30)

    # Rows — up to 5
    MAX_ROWS = 5
    shown    = investments[:MAX_ROWS]
    ROW_H    = 48
    rf       = _font(13)
    vf_s     = _font(15, bold=True)

    _RISK_LABELS = {"safe": "Safe", "medium": "Medium", "risky": "High Risk"}
    _RISK_RANGE  = {"safe": "5–10%", "medium": "20–35%", "risky": "50–80%"}
    _RISK_COLS   = {
        "safe":   (165, 138, 30),
        "medium": (195, 118, 0),
        "risky":  (185, 22, 22),
    }

    for i, inv in enumerate(shown):
        y      = TH_Y + 24 + i * ROW_H
        itype  = inv.get("inv_type", "safe")
        rc     = _RISK_COLS.get(itype, th["text2"])
        status_col = gold if inv.get("matured") else (*th["text1"][:3], 210)
        status_lbl = "✓  Ready" if inv.get("matured") else "Active"
        rem    = _fmt_td(inv.get("remaining")) if not inv.get("matured") else "—"

        row_data = [
            (_RISK_LABELS.get(itype, itype.title()), rc),
            (_fmt(inv["principal"]), th["text1"]),
            (_RISK_RANGE.get(itype, "—"), th["text2"]),
            (status_lbl, status_col),
            (rem, th["text2"]),
        ]
        for (txt, col), x in zip(row_data, COL_X):
            col3 = col[:3] if len(col) >= 3 else col
            draw.text((x, y + 4), txt, font=vf_s, fill=(*col3, 210))

        if i < len(shown) - 1:
            _hline(draw, y + ROW_H - 6, th, alpha=18)

    if len(investments) > MAX_ROWS:
        extra_f = _font(11)
        extra_t = f"+ {len(investments) - MAX_ROWS} more  ·  use /portfolio for full list"
        extra_y = TH_Y + 24 + MAX_ROWS * ROW_H + 4
        draw.text((PAD + 8, extra_y), extra_t,
                  font=extra_f, fill=(*th["text2"][:3], 120))

    # Summary bar
    matured_count = sum(1 for inv in investments if inv.get("matured"))
    active_count  = len(investments) - matured_count
    total_locked  = sum(inv["principal"] for inv in investments if not inv.get("matured"))

    _dline(draw, H - 56, th)
    sf_sm = _font(10)
    summary = (
        f"Active: {active_count}    "
        f"Ready to Collect: {matured_count}    "
        f"Total Locked: {_fmt(total_locked)}"
    )
    sw = _tw(draw, summary, sf_sm)
    draw.text(((W - sw) // 2, H - 46), summary,
              font=sf_sm, fill=(*th["text2"][:3], 150))

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 7.  COLLECT  CARD
# ══════════════════════════════════════════════════════════════════════════════

def generate_collect_card(
    username:      str,
    rank:          str,
    results:       list,       # list of {inv_type, principal, payout, profit, success}
    total_payout:  int,
    new_balance:   int,
    avatar_bytes:  Optional[bytes] = None,
    skin_id:       Optional[str]   = None,
) -> io.BytesIO:

    th      = _t(skin_id)
    gold    = th["gold"]
    acc     = th["accent"]

    any_success = any(r.get("success", True) for r in results)
    badge_col  = gold if any_success else (140, 55, 55)
    badge_glow = th["glow"] if any_success else (90, 18, 18)

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    INFERNAL  MARKETS",
        badge_txt  = "RETURNS  COLLECTED",
        badge_col  = badge_col,
        badge_glow = badge_glow,
    )

    _avatar_col(card, avatar_bytes, th, username, rank, badge_col)
    draw = ImageDraw.Draw(card)

    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "COLLECTION  REPORT",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    total_invested = sum(r["principal"] for r in results)
    net_profit     = total_payout - total_invested
    count          = len(results)
    wins           = sum(1 for r in results if r.get("success", True))

    profit_str   = (f"+{_fmt(net_profit)}" if net_profit >= 0 else f"−{_fmt(abs(net_profit))}")
    profit_col   = gold if net_profit >= 0 else (200, 60, 60)
    win_str      = f"{wins}/{count}"
    total_str    = f"+{_fmt(total_payout)}"
    bal_str      = _fmt(new_balance)

    rows = [
        ("📦  Investments",    f"{count} matured",    th["text2"],  False),
        ("🎯  Outcomes",       win_str,               th["text1"],  False),
        ("💹  Net Profit",     profit_str,            profit_col,   False),
        ("💰  Total Payout",   total_str,             gold,         True),
        ("💼  Wallet After",   bal_str,               th["text1"],  False),
    ]
    ROW_H = 58
    for i, (label, value, vcol, hl) in enumerate(rows):
        y = 94 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, th, highlighted=hl, hl_accent=badge_col)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _hline(draw, y + 46, th, alpha=22, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 8.  WITHDRAW  CARD  (early withdrawal)
# ══════════════════════════════════════════════════════════════════════════════

def generate_withdraw_card(
    username:     str,
    rank:         str,
    results:      list,       # list of {inv_type, principal, payout, penalty}
    total_payout: int,
    new_balance:  int,
    avatar_bytes: Optional[bytes] = None,
    skin_id:      Optional[str]   = None,
) -> io.BytesIO:

    th   = _t(skin_id)
    gold = th["gold"]
    red  = (185, 40, 40)
    red_glow = (110, 12, 12)

    card, draw = _base_canvas(
        th,
        header_txt = "KINGDOM  OF  HELL    ·    INFERNAL  MARKETS",
        badge_txt  = "EARLY  WITHDRAWAL",
        badge_col  = red,
        badge_glow = red_glow,
    )

    _avatar_col(card, avatar_bytes, th, username, rank, red)
    draw = ImageDraw.Draw(card)

    sf = _font(9, cinzel=True)
    draw.text((RIGHT_X, 56), "WITHDRAWAL  RECEIPT",
              font=sf, fill=(*th["text2"][:3], 108))
    _hline(draw, 84, th, alpha=38, x1=RIGHT_X, x2=W - PAD)

    count          = len(results)
    total_principal = sum(r["principal"] for r in results)
    total_penalty   = sum(r["penalty"] for r in results)

    cnt_str    = f"{count} position{'s' if count != 1 else ''}"
    orig_str   = _fmt(total_principal)
    pen_str    = f"−{_fmt(total_penalty)}  (20%)"
    payout_str = _fmt(total_payout)
    bal_str    = _fmt(new_balance)

    rows = [
        ("📤  Positions Closed",  cnt_str,    th["text2"],   False),
        ("📥  Original Value",    orig_str,   th["text1"],   False),
        ("☠  Penalty Burned",    pen_str,    red,           False),
        ("💰  Returned",          payout_str, gold,          True),
        ("💼  Wallet After",      bal_str,    th["text1"],   False),
    ]
    ROW_H = 58
    for i, (label, value, vcol, hl) in enumerate(rows):
        y = 94 + i * ROW_H
        _stat_row(card, draw, label, value, y, vcol, th, highlighted=hl, hl_accent=red)
        draw = ImageDraw.Draw(card)
        if i < len(rows) - 1:
            _hline(draw, y + 46, th, alpha=22, x1=RIGHT_X, x2=W - PAD)

    return _finish(card, draw, th)


# ══════════════════════════════════════════════════════════════════════════════
# 9.  TREASURY  CARD  (/treasury  —  kingdom-wide reserves, no avatar column)
# ══════════════════════════════════════════════════════════════════════════════

def generate_treasury_card(
    balance:  int,
    skin_id:  Optional[str] = None,
) -> io.BytesIO:

    th   = _t(skin_id)
    gold = th["gold"]

    # Full-width canvas
    card = _gradient(W, H, th["bg1"], th["bg2"])
    _sigil(card, th, cx=450, cy=220, r=200)   # centre sigil — larger, full-width
    draw = ImageDraw.Draw(card)

    # Outer border
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*th["border"][:3], 220), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*th["border"][:3], 38), width=1)

    # Header
    hf   = _font(9, cinzel=True)
    htxt = "KINGDOM  OF  HELL    ·    INFERNAL  TREASURY"
    draw.text(((W - _tw(draw, htxt, hf)) // 2, 14),
              htxt, font=hf, fill=(*th["text2"][:3], 140))

    # Badge
    bf  = _font(11, bold=True, cinzel=True)
    btxt = "RESERVES"
    bw   = _tw(draw, btxt, bf)
    _glow(card, (W - PAD - bw, 10), btxt, bf,
          (*gold[:3], 255), (*th["glow"][:3], 255), blur=10, spread=2)
    draw = ImageDraw.Draw(card)

    _dline(draw, 44, th)

    # Sub-label
    sl  = _font(10, cinzel=True)
    slt = "TOTAL  RESERVES"
    draw.text(((W - _tw(draw, slt, sl)) // 2, 64),
              slt, font=sl, fill=(*th["text2"][:3], 120))

    # Large balance — centrepiece
    bf2 = _font(56, bold=True)
    bval = _fmt(balance)
    bw2  = _tw(draw, bval, bf2)
    _glow(card, ((W - bw2) // 2, 86), bval, bf2,
          (*gold[:3], 255), (*th["glow"][:3], 255), blur=22, spread=4)
    draw = ImageDraw.Draw(card)

    # Horizontal rule
    _dline(draw, 176, th)

    # Atmospheric quote
    qf   = _font(13)
    qtxt = '"All wealth flows through the Kingdom. None escapes its ledger."'
    qw   = _tw(draw, qtxt, qf)
    # Wrap if too wide
    if qw > W - PAD * 4:
        words  = qtxt.split()
        line1  = ' '.join(words[:len(words)//2])
        line2  = ' '.join(words[len(words)//2:])
        lw1    = _tw(draw, line1, qf)
        lw2    = _tw(draw, line2, qf)
        draw.text(((W - lw1) // 2, 192), line1, font=qf, fill=(*th["text2"][:3], 130))
        draw.text(((W - lw2) // 2, 214), line2, font=qf, fill=(*th["text2"][:3], 130))
    else:
        draw.text(((W - qw) // 2, 200), qtxt, font=qf, fill=(*th["text2"][:3], 130))

    # ── DC breakdown decorative rows ────────────────────────────────────────
    ROW_Y = 268
    _hline(draw, ROW_Y - 8, th, alpha=30)

    detail_items = [
        ("Total Reserves", _fmt(balance)),
        ("Status",         "Active"),
    ]
    col_w  = (W - PAD * 2) // len(detail_items)
    vf2    = _font(18, bold=True)
    lf2    = _font(10, cinzel=True)
    for i, (label, value) in enumerate(detail_items):
        cx = PAD + i * col_w + col_w // 2
        lw = _tw(draw, label, lf2)
        vw = _tw(draw, value, vf2)
        draw.text((cx - lw // 2, ROW_Y), label, font=lf2,
                  fill=(*th["text2"][:3], 110))
        draw.text((cx - vw // 2, ROW_Y + 18), value, font=vf2,
                  fill=(*gold[:3], 200))
        if i < len(detail_items) - 1:
            mid_x = PAD + (i + 1) * col_w
            draw.line([(mid_x, ROW_Y - 4), (mid_x, ROW_Y + 46)],
                      fill=(*th["border"][:3], 35), width=1)

    _hline(draw, ROW_Y + 52, th, alpha=30)

    return _finish(card, draw, th)
