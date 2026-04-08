"""
Kingdom Treasury — Infernal Identity Card Generator
900 × 600 px  |  Vertical AAA Layout  |  Pillow
"""

import io
import math
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Asset paths ──────────────────────────────────────────────────────────────
_CINZEL = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Card geometry ────────────────────────────────────────────────────────────
W, H     = 900, 600
RADIUS   = 28
PAD      = 32

# Row / zone boundaries (y)
HEADER_H  = 46    # header strip height
ID_Y      = HEADER_H + 14          # identity zone top
ID_H      = 158                    # identity zone height
DIV1_Y    = ID_Y + ID_H            # divider after identity
WEALTH_Y  = DIV1_Y + 10            # wealth zone top
WEALTH_H  = 190                    # wealth zone height
DIV2_Y    = WEALTH_Y + WEALTH_H    # divider after wealth
STATS_Y   = DIV2_Y + 12            # stats zone top
STATS_H   = 108                    # stats zone height
DIV3_Y    = STATS_Y + STATS_H      # divider before footer
FOOTER_Y  = DIV3_Y + 10            # footer zone top

# Avatar
AV_X, AV_Y = PAD, ID_Y + 10
AV_SZ       = 116

# ─── Skin themes ──────────────────────────────────────────────────────────────
THEMES = {
    "default": dict(
        bg1=(8, 3, 3),   bg2=(22, 7, 7),
        border=(110, 0, 0),   accent=(185, 22, 22),
        gold=(215, 168, 42),  text1=(232, 212, 212),
        text2=(148, 102, 102), glow=(150, 0, 0),
        sigil="star",
    ),
    "blood_crown": dict(
        bg1=(14, 0, 0),  bg2=(32, 4, 4),
        border=(165, 0, 0),   accent=(225, 12, 12),
        gold=(225, 162, 28),  text1=(248, 218, 218),
        text2=(172, 116, 116), glow=(210, 0, 0),
        sigil="crown",
    ),
    "abyss_smoke": dict(
        bg1=(6, 3, 18),  bg2=(16, 7, 38),
        border=(58, 18, 118),  accent=(135, 62, 225),
        gold=(168, 128, 255),  text1=(212, 202, 242),
        text2=(128, 108, 178),  glow=(105, 42, 205),
        sigil="eye",
    ),
    "infernal_gold": dict(
        bg1=(14, 9, 0),  bg2=(30, 18, 4),
        border=(158, 118, 0), accent=(205, 162, 0),
        gold=(255, 212, 38),  text1=(252, 238, 202),
        text2=(178, 142, 78),  glow=(205, 162, 0),
        sigil="sun",
    ),
    "royal_dark": dict(
        bg1=(4, 4, 18),  bg2=(8, 8, 36),
        border=(38, 38, 138),  accent=(82, 82, 205),
        gold=(202, 182, 255),  text1=(222, 222, 255),
        text2=(128, 128, 198),  glow=(62, 62, 182),
        sigil="fleur",
    ),
    "black_throne": dict(
        bg1=(5, 5, 5),   bg2=(14, 14, 14),
        border=(52, 52, 52),  accent=(138, 138, 138),
        gold=(202, 202, 202),  text1=(232, 232, 232),
        text2=(138, 138, 138),  glow=(98, 98, 98),
        sigil="throne",
    ),
    "crimson_sigil": dict(
        bg1=(12, 2, 2),  bg2=(28, 6, 6),
        border=(175, 32, 32),  accent=(212, 42, 42),
        gold=(242, 182, 58),  text1=(248, 218, 218),
        text2=(178, 118, 118),  glow=(192, 22, 22),
        sigil="sigil",
    ),
}


def _t(skin_id: Optional[str]) -> dict:
    return THEMES.get(skin_id or "default", THEMES["default"])


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


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        return len(text) * (font.size // 2 if hasattr(font, "size") else 8)


def _fit_font(draw, text: str, max_w: int,
              start: int, stop: int, bold=False, cinzel=False) -> ImageFont.FreeTypeFont:
    """Return the largest font size where text fits within max_w."""
    for sz in range(start, stop - 1, -1):
        f = _font(sz, bold=bold, cinzel=cinzel)
        if _text_w(draw, text, f) <= max_w:
            return f
    return _font(stop, bold=bold, cinzel=cinzel)


# ─── Gradient background ──────────────────────────────────────────────────────

def _gradient(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return img


# ─── Rounded-rect mask ────────────────────────────────────────────────────────

def _card_mask(w: int, h: int, r: int) -> Image.Image:
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=r, fill=255)
    return m


# ─── Avatar ───────────────────────────────────────────────────────────────────

def _paste_avatar(card: Image.Image, av_bytes: Optional[bytes], theme: dict):
    sz = AV_SZ
    if av_bytes:
        try:
            av = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((sz, sz), Image.LANCZOS)
        except Exception:
            av = _placeholder_avatar(sz, theme)
    else:
        av = _placeholder_avatar(sz, theme)

    mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)], radius=14, fill=255)
    av.putalpha(mask)

    # Glow border layer
    bsz = sz + 8
    border = Image.new("RGBA", (bsz, bsz), (0, 0, 0, 0))
    bc = (*theme["accent"][:3], 190)
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (bsz - 1, bsz - 1)], radius=17, outline=bc, width=3
    )
    card.alpha_composite(border, (AV_X - 4, AV_Y - 4))
    card.alpha_composite(av, (AV_X, AV_Y))


def _placeholder_avatar(sz: int, theme: dict) -> Image.Image:
    av = Image.new("RGBA", (sz, sz), (*theme["bg2"][:3], 255))
    d = ImageDraw.Draw(av)
    c = (*theme["accent"][:3], 160)
    m = sz // 2
    # simple silhouette
    d.ellipse([(m - 18, 14), (m + 18, 50)], fill=c)
    d.ellipse([(m - 30, 52), (m + 30, sz - 4)], fill=c)
    return av


# ─── Glow text ────────────────────────────────────────────────────────────────

def _glow(card: Image.Image, xy: tuple, text: str, font,
          color: tuple, glow_col: tuple, blur: int = 10, spread: int = 3):
    layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    gc = (*glow_col[:3], 130)
    for dx in range(-spread, spread + 1):
        for dy in range(-spread, spread + 1):
            ld.text((xy[0] + dx, xy[1] + dy), text, font=font, fill=gc)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    card.alpha_composite(layer)
    ImageDraw.Draw(card).text(xy, text, font=font, fill=color)


# ─── Divider line ─────────────────────────────────────────────────────────────

def _line(draw: ImageDraw.ImageDraw, y: int, theme: dict, alpha: int = 65,
          x1: int = PAD, x2: int = W - PAD):
    c = (*theme["border"][:3], alpha)
    draw.line([(x1, y), (x2, y)], fill=c, width=1)


# ─── Background sigil (large, blurred, semi-transparent) ─────────────────────

def _bg_sigil(card: Image.Image, theme: dict):
    sig_cx = 710
    sig_cy = 320
    r = 200

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = (*theme["glow"][:3], 55)   # very subtle

    stype = theme["sigil"]
    if stype == "star":
        _sig_star(d, sig_cx, sig_cy, r, col, inner=0.40)
    elif stype == "crown":
        _sig_crown(d, sig_cx, sig_cy, r, col)
    elif stype == "eye":
        _sig_eye(d, sig_cx, sig_cy, r, col)
    elif stype == "sun":
        _sig_sun(d, sig_cx, sig_cy, r, col)
    elif stype == "fleur":
        _sig_fleur(d, sig_cx, sig_cy, r, col)
    elif stype == "throne":
        _sig_throne(d, sig_cx, sig_cy, r, col)
    elif stype == "sigil":
        _sig_cross(d, sig_cx, sig_cy, r, col)

    blurred = layer.filter(ImageFilter.GaussianBlur(28))
    card.alpha_composite(blurred)

    # Second pass — slightly sharper, even lower alpha
    layer2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    col2 = (*theme["glow"][:3], 30)
    if stype == "star":
        _sig_star(d2, sig_cx, sig_cy, r, col2, inner=0.40)
    elif stype == "crown":
        _sig_crown(d2, sig_cx, sig_cy, r, col2)
    elif stype == "eye":
        _sig_eye(d2, sig_cx, sig_cy, r, col2)
    elif stype == "sun":
        _sig_sun(d2, sig_cx, sig_cy, r, col2)
    elif stype == "fleur":
        _sig_fleur(d2, sig_cx, sig_cy, r, col2)
    elif stype == "throne":
        _sig_throne(d2, sig_cx, sig_cy, r, col2)
    elif stype == "sigil":
        _sig_cross(d2, sig_cx, sig_cy, r, col2)
    layer2 = layer2.filter(ImageFilter.GaussianBlur(6))
    card.alpha_composite(layer2)


# ─── Sigil primitives ─────────────────────────────────────────────────────────

def _sig_star(draw, cx, cy, r, col, n=5, inner=0.38):
    pts = []
    for i in range(n * 2):
        ang = math.pi * i / n - math.pi / 2
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, outline=col, width=3)
    draw.ellipse([(cx - r * 0.18, cy - r * 0.18), (cx + r * 0.18, cy + r * 0.18)], outline=col, width=2)
    draw.ellipse([(cx - r - 14, cy - r - 14), (cx + r + 14, cy + r + 14)], outline=(*col[:3], col[3] // 2), width=2)


def _sig_crown(draw, cx, cy, r, col):
    s = r
    by = cy + s * 0.22
    bh = s * 0.28
    draw.rectangle([(cx - s * 0.56, by), (cx + s * 0.56, by + bh)], outline=col, width=3)
    for (ox, height) in [(-s * 0.38, s * 0.38), (0, s * 0.62), (s * 0.38, s * 0.38)]:
        draw.polygon([
            (cx + ox - s * 0.10, by),
            (cx + ox, by - height),
            (cx + ox + s * 0.10, by),
        ], outline=col, width=2)
    for ox, height in [(-s * 0.38, s * 0.38), (0, s * 0.62), (s * 0.38, s * 0.38)]:
        gx, gy = cx + ox, by - height
        draw.ellipse([(gx - 8, gy - 8), (gx + 8, gy + 8)], fill=col)
    draw.ellipse([(cx - s * 0.72, cy - s * 0.72), (cx + s * 0.72, cy + s * 0.72)],
                 outline=(*col[:3], col[3] // 2), width=2)


def _sig_eye(draw, cx, cy, r, col):
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=3)
    ir = r * 0.52
    draw.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)], outline=col, width=2)
    pr = r * 0.22
    draw.ellipse([(cx - pr, cy - pr), (cx + pr, cy + pr)], outline=col, width=2)
    for i in range(8):
        ang = math.pi * 2 * i / 8
        x1, y1 = cx + (r + 6) * math.cos(ang), cy + (r + 6) * math.sin(ang)
        x2, y2 = cx + (r + 22) * math.cos(ang), cy + (r + 22) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=col, width=2)
    # almond outer shape
    pts = (
        [(cx - r, cy)]
        + [(cx + r * math.cos(math.pi - math.pi * i / 10),
            cy - r * 0.42 * math.sin(math.pi * i / 10)) for i in range(11)]
        + [(cx + r, cy)]
        + [(cx + r * math.cos(math.pi * i / 10),
            cy + r * 0.42 * math.sin(math.pi * i / 10)) for i in range(11)]
    )
    draw.polygon(pts, outline=(*col[:3], col[3] // 2), width=2)


def _sig_sun(draw, cx, cy, r, col):
    n = 12
    for i in range(n):
        ang = math.pi * 2 * i / n
        r_in = r + 4
        r_out = r + 34 if i % 2 == 0 else r + 18
        draw.line([(cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)),
                   (cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))],
                  fill=col, width=3 if i % 2 == 0 else 1)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=3)
    ir = r * 0.48
    draw.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)], outline=col, width=2)
    draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=col)


def _sig_fleur(draw, cx, cy, r, col):
    s = r
    def petal(ox, oy, rw, rh):
        draw.ellipse([(cx + ox - rw, cy + oy - rh), (cx + ox + rw, cy + oy + rh)],
                     outline=col, width=2)
    draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=col)
    petal(0, -s * 0.40, s * 0.16, s * 0.38)
    petal(-s * 0.38, -s * 0.16, s * 0.32, s * 0.15)
    petal(s * 0.38, -s * 0.16, s * 0.32, s * 0.15)
    draw.rectangle([(cx - s * 0.07, cy + 6), (cx + s * 0.07, cy + s * 0.48)], outline=col, width=2)
    draw.rectangle([(cx - s * 0.24, cy + s * 0.34), (cx + s * 0.24, cy + s * 0.52)], outline=col, width=2)
    draw.ellipse([(cx - s * 0.72, cy - s * 0.72), (cx + s * 0.72, cy + s * 0.72)],
                 outline=(*col[:3], col[3] // 2), width=2)


def _sig_throne(draw, cx, cy, r, col):
    s = r
    draw.rectangle([(cx - s * 0.40, cy - s * 0.58), (cx + s * 0.40, cy + s * 0.48)], outline=col, width=3)
    draw.rectangle([(cx - s * 0.46, cy + s * 0.10), (cx + s * 0.46, cy + s * 0.28)], outline=col, width=2)
    for side in [-1, 1]:
        lx = cx + min(side * s * 0.40, side * s * 0.55)
        rx = cx + max(side * s * 0.40, side * s * 0.55)
        draw.rectangle([(lx, cy - s * 0.05), (rx, cy + s * 0.28)], outline=col, width=2)
    lw = s * 0.08
    for lx in [cx - s * 0.36, cx + s * 0.36 - lw]:
        draw.rectangle([(lx, cy + s * 0.28), (lx + lw, cy + s * 0.58)], outline=col, width=2)
    top_y = cy - s * 0.58
    for fx in [cx - s * 0.22, cx, cx + s * 0.22]:
        draw.polygon([(fx - 6, top_y), (fx, top_y - 16), (fx + 6, top_y)], fill=col)
    draw.ellipse([(cx - s * 0.75, cy - s * 0.75), (cx + s * 0.75, cy + s * 0.75)],
                 outline=(*col[:3], col[3] // 2), width=2)


def _sig_cross(draw, cx, cy, r, col):
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=3)
    draw.ellipse([(cx - r + 12, cy - r + 12), (cx + r - 12, cy + r - 12)],
                 outline=(*col[:3], col[3] // 2), width=1)
    arm, thick = r - 5, 8
    draw.rectangle([(cx - thick, cy - arm), (cx + thick, cy + arm)], fill=col)
    draw.rectangle([(cx - arm, cy - thick), (cx + arm, cy + thick)], fill=col)
    for ex, ey in [(cx, cy - arm), (cx, cy + arm), (cx - arm, cy), (cx + arm, cy)]:
        draw.ellipse([(ex - 8, ey - 8), (ex + 8, ey + 8)], fill=col)
    draw.ellipse([(cx - r - 14, cy - r - 14), (cx + r + 14, cy + r + 14)],
                 outline=(*col[:3], col[3] // 3), width=2)


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_card(
    username: str,
    display_name: str,
    equipped_title: str,
    rank: str,
    balance: int,
    kingdom_rank: int,
    taxes_paid: int,
    risk_score: int,
    skin_id: Optional[str],
    avatar_bytes: Optional[bytes],
    footer_flavor: str,
) -> io.BytesIO:
    from .formatting import format_dc
    from bot.services.rank_service import RANK_DICT

    t = _t(skin_id)

    # ── Canvas ──────────────────────────────────────────────────────────
    card = _gradient(W, H, t["bg1"], t["bg2"])

    # ── Background sigil (behind everything) ────────────────────────────
    _bg_sigil(card, t)

    draw = ImageDraw.Draw(card)

    # ── Card border ─────────────────────────────────────────────────────
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*t["border"][:3], 210), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*t["border"][:3], 50), width=1)

    # ── Header strip ────────────────────────────────────────────────────
    hf = _font(10, cinzel=True)
    htxt = "KINGDOM  OF  HELL    ·    INFERNAL  IDENTITY  CARD"
    hw = _text_w(draw, htxt, hf)
    draw.text(((W - hw) // 2, 14), htxt,
              font=hf, fill=(*t["text2"][:3], 140))

    _line(draw, HEADER_H, t, alpha=70)

    # ── Kingdom Rank badge (top-right) ──────────────────────────────────
    kr_badge = f"#{kingdom_rank}"
    krf = _font(26, bold=True, cinzel=True)
    krw = _text_w(draw, kr_badge, krf)
    _glow(card, (W - PAD - krw, 11), kr_badge, krf,
          (*t["gold"][:3], 245), t["glow"], blur=12, spread=3)
    draw = ImageDraw.Draw(card)

    krl = _font(8, cinzel=True)
    krlw = _text_w(draw, "KINGDOM RANK", krl)
    draw.text((W - PAD - krlw, 40), "KINGDOM RANK",
              font=krl, fill=(*t["text2"][:3], 130))

    # ── Avatar ──────────────────────────────────────────────────────────
    _paste_avatar(card, avatar_bytes, t)
    draw = ImageDraw.Draw(card)

    # ── Display name (large, dominant) ──────────────────────────────────
    name_x = AV_X + AV_SZ + 22
    max_name_w = W - name_x - PAD - 80     # leave room for potential rank badge

    dn = display_name or username
    name_font = _fit_font(draw, dn, max_name_w, 52, 26, bold=True)
    name_y = AV_Y + 6
    _glow(card, (name_x, name_y), dn, name_font,
          t["text1"], t["glow"], blur=8, spread=2)
    draw = ImageDraw.Draw(card)

    # ── Secondary line: Rank — Title  OR  Rank — Kingdom of Hell ────────
    has_title = equipped_title and equipped_title.lower() != "unmarked"
    secondary = f"{rank}  —  {equipped_title}" if has_title else f"{rank}  —  Kingdom of Hell"
    sec_font = _font(17)
    name_h = name_font.size if hasattr(name_font, "size") else 42
    sec_y = name_y + name_h + 8

    # Rank word in gold, rest in text2
    rank_part = f"{rank}  —  "
    rp_font = _font(17, bold=True)
    rp_w = _text_w(draw, rank_part, rp_font)
    _glow(card, (name_x, sec_y), rank_part, rp_font,
          (*t["gold"][:3], 230), t["glow"], blur=5, spread=1)
    draw = ImageDraw.Draw(card)
    title_part = equipped_title if has_title else "Kingdom of Hell"
    draw.text((name_x + rp_w, sec_y), title_part,
              font=sec_font, fill=(*t["accent"][:3], 210))

    # ── Tax bracket (small, under secondary line) ─────────────────────
    re = RANK_DICT.get(rank, {})
    tax_rate = re.get("tax_rate", 0.12)
    tax_str = "TAX EXEMPT" if tax_rate == 0 else f"TAX BRACKET  {int(tax_rate * 100)}%"
    tbf = _font(11)
    draw.text((name_x, sec_y + 26), tax_str,
              font=tbf, fill=(*t["text2"][:3], 150))

    _line(draw, DIV1_Y, t, alpha=65)

    # ── WEALTH section ──────────────────────────────────────────────────
    bal_str = format_dc(balance)
    wlabel_f = _font(11, cinzel=True)
    wlw = _text_w(draw, "WEALTH", wlabel_f)
    draw.text(((W - wlw) // 2, WEALTH_Y + 14), "WEALTH",
              font=wlabel_f, fill=(*t["text2"][:3], 175))

    # Balance — VERY LARGE — auto-fit to card width
    bal_font = _fit_font(draw, bal_str, W - 100, 72, 42, bold=True)
    bal_w = _text_w(draw, bal_str, bal_font)
    bal_x = (W - bal_w) // 2
    bal_y = WEALTH_Y + 32

    _glow(card, (bal_x, bal_y), bal_str, bal_font,
          (*t["gold"][:3], 250), t["glow"], blur=18, spread=4)
    draw = ImageDraw.Draw(card)

    # Subtle accent line above/below balance
    bal_h = bal_font.size if hasattr(bal_font, "size") else 60
    _line(draw, bal_y + bal_h + 16, t, alpha=45,
          x1=W // 4, x2=3 * W // 4)

    _line(draw, DIV2_Y, t, alpha=65)

    # ── STATS section ────────────────────────────────────────────────────
    lbl_f  = _font(9, cinzel=True)
    val_f  = _font(20, bold=True)
    val_f2 = _font(14, bold=True)

    # Three stat blocks, evenly spaced across full width
    stat_cols = [W // 6, W // 2, 5 * W // 6]

    def _stat(cx_: int, label: str, value: str, large: bool = True):
        lw_ = _text_w(draw, label, lbl_f)
        draw.text((cx_ - lw_ // 2, STATS_Y + 8), label,
                  font=lbl_f, fill=(*t["text2"][:3], 175))
        vf = val_f if large else val_f2
        vw_ = _text_w(draw, value, vf)
        _glow(card, (cx_ - vw_ // 2, STATS_Y + 26), value, vf,
              (*t["accent"][:3], 225), t["glow"], blur=6, spread=1)

    _stat(stat_cols[0], "KINGDOM RANK", f"#{kingdom_rank}")
    _stat(stat_cols[1], "TAXES FILED", format_dc(taxes_paid))
    if risk_score > 0:
        rc = (220, 75, 75, 220) if risk_score >= 50 else (*t["accent"][:3], 220)
        _stat(stat_cols[2], "RISK SCORE", f"{risk_score} / 100", large=False)
    else:
        skin_labels = {
            "default": "INFERNAL STD", "blood_crown": "BLOOD CROWN",
            "abyss_smoke": "ABYSS SMOKE", "infernal_gold": "INFERNAL GOLD",
            "royal_dark": "ROYAL DARK",  "black_throne": "BLACK THRONE",
            "crimson_sigil": "CRIMSON SIGIL",
        }
        sk_name = skin_labels.get(skin_id or "default", "INFERNAL STD")
        _stat(stat_cols[2], "CARD SKIN", sk_name, large=False)

    draw = ImageDraw.Draw(card)

    _line(draw, DIV3_Y, t, alpha=65)

    # ── Footer flavor text ───────────────────────────────────────────────
    ff = _font(11)
    fw_ = _text_w(draw, footer_flavor, ff)
    draw.text(((W - fw_) // 2, FOOTER_Y + 10), footer_flavor,
              font=ff, fill=(*t["text2"][:3], 150))

    # ── Rounded mask (clip card) ─────────────────────────────────────────
    card.putalpha(_card_mask(W, H, RADIUS))

    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


# ─── Avatar fetch ─────────────────────────────────────────────────────────────

async def fetch_avatar(url: Optional[str]) -> Optional[bytes]:
    if not url:
        return None
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception:
        pass
    return None
