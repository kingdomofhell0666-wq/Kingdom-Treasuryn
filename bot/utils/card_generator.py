"""
Kingdom Treasury — Infernal Identity Card Generator
Generates a 900×320 image using Pillow for /identity.
"""

import io
import math
import asyncio
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Asset paths ──────────────────────────────────────────────────────────────
_CINZEL   = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R   = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Card constants ───────────────────────────────────────────────────────────
W, H           = 900, 320
RADIUS         = 24
LEFT_END       = 228       # left section ends
CENTER_X       = 252       # center section begins
CENTER_END     = 642
RIGHT_X        = 656       # right section begins
AVATAR_SIZE    = 92
AVATAR_X       = 26
AVATAR_Y       = 48

# ─── Skin theme definitions ───────────────────────────────────────────────────
THEMES = {
    "default": dict(
        bg=(12, 4, 4), bg2=(26, 8, 8),
        border=(110, 0, 0), accent=(180, 20, 20),
        gold=(210, 165, 40), text1=(230, 210, 210),
        text2=(155, 110, 110), glow=(160, 0, 0),
        sigil="star",
    ),
    "blood_crown": dict(
        bg=(18, 0, 0), bg2=(35, 4, 4),
        border=(160, 0, 0), accent=(220, 10, 10),
        gold=(220, 160, 30), text1=(245, 215, 215),
        text2=(175, 120, 120), glow=(200, 0, 0),
        sigil="crown",
    ),
    "abyss_smoke": dict(
        bg=(8, 4, 20), bg2=(18, 8, 40),
        border=(60, 20, 120), accent=(130, 60, 220),
        gold=(160, 120, 255), text1=(210, 200, 240),
        text2=(130, 110, 180), glow=(100, 40, 200),
        sigil="eye",
    ),
    "infernal_gold": dict(
        bg=(16, 10, 0), bg2=(32, 20, 4),
        border=(160, 120, 0), accent=(200, 160, 0),
        gold=(255, 210, 40), text1=(250, 235, 200),
        text2=(180, 145, 80), glow=(200, 160, 0),
        sigil="sun",
    ),
    "royal_dark": dict(
        bg=(4, 4, 20), bg2=(8, 8, 38),
        border=(40, 40, 140), accent=(80, 80, 200),
        gold=(200, 180, 255), text1=(220, 220, 255),
        text2=(130, 130, 200), glow=(60, 60, 180),
        sigil="fleur",
    ),
    "black_throne": dict(
        bg=(6, 6, 6), bg2=(14, 14, 14),
        border=(55, 55, 55), accent=(140, 140, 140),
        gold=(200, 200, 200), text1=(230, 230, 230),
        text2=(140, 140, 140), glow=(100, 100, 100),
        sigil="throne",
    ),
    "crimson_sigil": dict(
        bg=(14, 2, 2), bg2=(30, 6, 6),
        border=(178, 34, 34), accent=(210, 40, 40),
        gold=(240, 180, 60), text1=(245, 215, 215),
        text2=(180, 120, 120), glow=(190, 20, 20),
        sigil="sigil",
    ),
}


def _theme(skin_id: Optional[str]) -> dict:
    return THEMES.get(skin_id or "default", THEMES["default"])


# ─── Font loader ──────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False, cinzel: bool = False) -> ImageFont.FreeTypeFont:
    paths = []
    if cinzel:
        paths.append((_CINZEL, size))
    if bold:
        paths.append((_DEJA_B, size))
    paths.append((_DEJA_R, size))
    for path, sz in paths:
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            continue
    return ImageFont.load_default()


# ─── Gradient background ──────────────────────────────────────────────────────

def _gradient(w: int, h: int, c1: Tuple, c2: Tuple) -> Image.Image:
    base = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return base


# ─── Rounded rectangle mask ───────────────────────────────────────────────────

def _rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    return mask


# ─── Avatar with rounded corners ─────────────────────────────────────────────

def _apply_avatar(card: Image.Image, avatar_bytes: Optional[bytes], theme: dict):
    ax, ay = AVATAR_X, AVATAR_Y
    sz = AVATAR_SIZE

    # Placeholder if no avatar
    if not avatar_bytes:
        av = Image.new("RGBA", (sz, sz), (30, 10, 10, 255))
        draw = ImageDraw.Draw(av)
        draw.ellipse([(sz//4, sz//6), (3*sz//4, sz//2)], fill=theme["accent"])
        draw.ellipse([(sz//6, sz//2), (5*sz//6, sz-2)], fill=theme["accent"])
    else:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((sz, sz), Image.LANCZOS)
        except Exception:
            av = Image.new("RGBA", (sz, sz), (30, 10, 10, 255))

    # Rounded corners mask
    av_mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(av_mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)], radius=12, fill=255)
    av.putalpha(av_mask)

    # Glow border — draw on a slightly larger canvas
    border_sz = sz + 6
    border = Image.new("RGBA", (border_sz, border_sz), (0, 0, 0, 0))
    g = theme["accent"]
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (border_sz - 1, border_sz - 1)],
        radius=15, outline=(*g, 200), width=2, fill=(0, 0, 0, 0),
    )
    card.alpha_composite(border, (ax - 3, ay - 3))
    card.alpha_composite(av, (ax, ay))


# ─── Glow text ────────────────────────────────────────────────────────────────

def _glow_text(card: Image.Image, draw: ImageDraw.ImageDraw,
               xy: Tuple, text: str, font: ImageFont.FreeTypeFont,
               color: Tuple, glow_color: Tuple, radius: int = 8):
    """Render text with a soft glow behind it."""
    glow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gc = (*glow_color[:3], 120)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            gd.text((xy[0] + dx, xy[1] + dy), text, font=font, fill=gc)
    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    card.alpha_composite(glow)
    draw.text(xy, text, font=font, fill=color)


# ─── Divider line ─────────────────────────────────────────────────────────────

def _divider(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, color: Tuple, alpha: int = 80):
    c = (*color[:3], alpha)
    draw.line([(x1, y), (x2, y)], fill=c, width=1)


# ─── Sigils ───────────────────────────────────────────────────────────────────

def _draw_sigil(sigil_layer: Image.Image, cx: int, cy: int, theme: dict):
    sigil_type = theme["sigil"]
    color = theme["glow"]
    draw = ImageDraw.Draw(sigil_layer)

    if sigil_type == "star":
        _sigil_star(draw, cx, cy, 78, color, n=5, inner=0.38)

    elif sigil_type == "crown":
        _sigil_crown(draw, cx, cy, 76, color)

    elif sigil_type == "eye":
        _sigil_eye(draw, cx, cy, 72, color)

    elif sigil_type == "sun":
        _sigil_sun(draw, cx, cy, 72, color)

    elif sigil_type == "fleur":
        _sigil_fleur(draw, cx, cy, 76, color)

    elif sigil_type == "throne":
        _sigil_throne(draw, cx, cy, 76, color)

    elif sigil_type == "sigil":
        _sigil_cross(draw, cx, cy, 76, color)


def _sigil_star(draw, cx, cy, r, color, n=5, inner=0.38):
    pts = []
    for i in range(n * 2):
        angle = math.pi * i / n - math.pi / 2
        radius = r if i % 2 == 0 else r * inner
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    c = (*color, 200)
    draw.polygon(pts, outline=c, fill=(*color[:3], 30), width=2)
    # Inner circle
    draw.ellipse([(cx - 14, cy - 14), (cx + 14, cy + 14)], outline=(*color[:3], 150), width=1)
    # Outer circle
    draw.ellipse([(cx - r - 8, cy - r - 8), (cx + r + 8, cy + r + 8)],
                 outline=(*color[:3], 60), width=1)


def _sigil_crown(draw, cx, cy, size, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 35)
    base_y = cy + size * 0.25
    bh = size * 0.28
    # Base
    draw.rectangle([(cx - size * 0.52, base_y), (cx + size * 0.52, base_y + bh)],
                   outline=c, fill=cf, width=2)
    # Left prong
    draw.polygon([
        (cx - size * 0.52, base_y),
        (cx - size * 0.30, base_y - size * 0.38),
        (cx - size * 0.08, base_y),
    ], outline=c, fill=cf, width=2)
    # Center prong (tallest)
    draw.polygon([
        (cx - size * 0.16, base_y),
        (cx, base_y - size * 0.62),
        (cx + size * 0.16, base_y),
    ], outline=c, fill=cf, width=2)
    # Right prong
    draw.polygon([
        (cx + size * 0.08, base_y),
        (cx + size * 0.30, base_y - size * 0.38),
        (cx + size * 0.52, base_y),
    ], outline=c, fill=cf, width=2)
    # Gems on prongs
    gem = 5
    for gx, gy in [
        (cx - size * 0.30, base_y - size * 0.38),
        (cx, base_y - size * 0.62),
        (cx + size * 0.30, base_y - size * 0.38),
    ]:
        draw.ellipse([(gx - gem, gy - gem), (gx + gem, gy + gem)], fill=(*color[:3], 220))
    # Outer ring
    draw.ellipse([(cx - size * 0.65, cy - size * 0.65), (cx + size * 0.65, cy + size * 0.65)],
                 outline=(*color[:3], 55), width=1)


def _sigil_eye(draw, cx, cy, r, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 30)
    # Outer circle
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=c, fill=cf, width=2)
    # Iris
    ir = r * 0.55
    draw.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)], outline=c, fill=(*color[:3], 60), width=2)
    # Pupil
    pr = r * 0.22
    draw.ellipse([(cx - pr, cy - pr), (cx + pr, cy + pr)], fill=c)
    # Eye shape (almond)
    pts_top = [(cx - r, cy)] + [(cx + r * math.cos(math.pi - math.pi * i / 8),
                                   cy - r * 0.45 * math.sin(math.pi * i / 8)) for i in range(9)] + [(cx + r, cy)]
    pts_bot = [(cx + r, cy)] + [(cx + r * math.cos(math.pi * i / 8),
                                   cy + r * 0.45 * math.sin(math.pi * i / 8)) for i in range(9)] + [(cx - r, cy)]
    all_pts = pts_top + pts_bot
    draw.polygon(all_pts, outline=c, width=2)
    # Radiating lines
    for i in range(8):
        angle = math.pi * 2 * i / 8
        x1 = cx + (r + 4) * math.cos(angle)
        y1 = cy + (r + 4) * math.sin(angle)
        x2 = cx + (r + 16) * math.cos(angle)
        y2 = cy + (r + 16) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=(*color[:3], 100), width=1)


def _sigil_sun(draw, cx, cy, r, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 40)
    # Outer glow ring
    draw.ellipse([(cx - r - 10, cy - r - 10), (cx + r + 10, cy + r + 10)],
                 outline=(*color[:3], 40), width=1)
    # Rays
    n_rays = 12
    for i in range(n_rays):
        angle = math.pi * 2 * i / n_rays
        r_inner = r + 2
        r_outer = r + 22 if i % 2 == 0 else r + 12
        x1 = cx + r_inner * math.cos(angle)
        y1 = cy + r_inner * math.sin(angle)
        x2 = cx + r_outer * math.cos(angle)
        y2 = cy + r_outer * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=(*color[:3], 180 if i % 2 == 0 else 100), width=2 if i % 2 == 0 else 1)
    # Main circle
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=c, fill=cf, width=2)
    # Inner circle
    ir = r * 0.5
    draw.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)], outline=c, fill=(*color[:3], 80), width=1)
    # Center
    draw.ellipse([(cx - 6, cy - 6), (cx + 6, cy + 6)], fill=c)


def _sigil_fleur(draw, cx, cy, size, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 35)
    s = size

    def petal(ox, oy, w, h):
        draw.ellipse([(cx + ox - w, cy + oy - h), (cx + ox + w, cy + oy + h)],
                     outline=c, fill=cf, width=2)

    # Center ball
    draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=c)
    # Top petal (tall center)
    petal(0, -s * 0.38, s * 0.15, s * 0.36)
    # Side petals
    petal(-s * 0.35, -s * 0.15, s * 0.30, s * 0.14)
    petal(s * 0.35, -s * 0.15, s * 0.30, s * 0.14)
    # Bottom stem
    draw.rectangle([(cx - s * 0.06, cy + 4), (cx + s * 0.06, cy + s * 0.45)],
                   outline=c, fill=cf, width=2)
    draw.rectangle([(cx - s * 0.22, cy + s * 0.32), (cx + s * 0.22, cy + s * 0.5)],
                   outline=c, fill=cf, width=2)
    # Outer ring
    draw.ellipse([(cx - s * 0.65, cy - s * 0.65), (cx + s * 0.65, cy + s * 0.65)],
                 outline=(*color[:3], 55), width=1)


def _sigil_throne(draw, cx, cy, size, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 35)
    s = size
    # Seat back (main rectangle)
    draw.rectangle([(cx - s * 0.38, cy - s * 0.55), (cx + s * 0.38, cy + s * 0.48)],
                   outline=c, fill=cf, width=2)
    # Seat
    draw.rectangle([(cx - s * 0.44, cy + s * 0.10), (cx + s * 0.44, cy + s * 0.28)],
                   outline=c, fill=(*c[:3], 80), width=2)
    # Armrests
    draw.rectangle([(cx - s * 0.52, cy - s * 0.05), (cx - s * 0.38, cy + s * 0.28)],
                   outline=c, fill=cf, width=2)
    draw.rectangle([(cx + s * 0.38, cy - s * 0.05), (cx + s * 0.52, cy + s * 0.28)],
                   outline=c, fill=cf, width=2)
    # Legs
    lw = s * 0.07
    lh = s * 0.28
    for lx in [cx - s * 0.36, cx + s * 0.36 - lw]:
        draw.rectangle([(lx, cy + s * 0.28), (lx + lw, cy + s * 0.55)],
                       outline=c, fill=cf, width=1)
    # Crown finial on top
    cy_top = cy - s * 0.55
    for fx in [cx - s * 0.20, cx, cx + s * 0.20]:
        draw.polygon([(fx - 5, cy_top), (fx, cy_top - 14), (fx + 5, cy_top)],
                     outline=c, fill=c, width=1)
    # Outer ring
    draw.ellipse([(cx - s * 0.70, cy - s * 0.70), (cx + s * 0.70, cy + s * 0.70)],
                 outline=(*color[:3], 45), width=1)


def _sigil_cross(draw, cx, cy, r, color):
    c = (*color[:3], 200)
    cf = (*color[:3], 35)
    # Outer circle
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=c, fill=cf, width=2)
    # Second circle
    draw.ellipse([(cx - r + 10, cy - r + 10), (cx + r - 10, cy + r - 10)],
                 outline=(*color[:3], 120), width=1)
    # Cross arms
    arm = r - 4
    thick = 6
    draw.rectangle([(cx - thick, cy - arm), (cx + thick, cy + arm)], fill=c)
    draw.rectangle([(cx - arm, cy - thick), (cx + arm, cy + thick)], fill=c)
    # Ornament circles at cross ends
    for ex, ey in [(cx, cy - arm), (cx, cy + arm), (cx - arm, cy), (cx + arm, cy)]:
        draw.ellipse([(ex - 6, ey - 6), (ex + 6, ey + 6)], fill=c)
    # Center
    draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=cf, outline=c, width=2)
    # Outer decorative ring
    draw.ellipse([(cx - r - 10, cy - r - 10), (cx + r + 10, cy + r + 10)],
                 outline=(*color[:3], 50), width=1)


# ─── Main card generator ──────────────────────────────────────────────────────

def generate_card(
    username: str,
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

    t = _theme(skin_id)
    bg1, bg2 = t["bg"], t["bg2"]

    # ── 1. Base canvas ──────────────────────────────────────────────────
    card = _gradient(W, H, bg1, bg2)
    draw = ImageDraw.Draw(card)

    # ── 2. Card border (rounded) ────────────────────────────────────────
    border_col = (*t["border"][:3], 200)
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)], radius=RADIUS,
                            outline=border_col, width=2)

    # Inner subtle border (depth)
    inner_col = (*t["border"][:3], 55)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)], radius=RADIUS - 3,
                            outline=inner_col, width=1)

    # ── 3. Vertical section dividers ────────────────────────────────────
    div_col = (*t["border"][:3], 55)
    draw.line([(LEFT_END, 28), (LEFT_END, H - 28)], fill=div_col, width=1)
    draw.line([(CENTER_END, 28), (CENTER_END, H - 28)], fill=div_col, width=1)

    # ── 4. Header strip ─────────────────────────────────────────────────
    hdr_font = _font(9, cinzel=True)
    header_text = "KINGDOM  OF  HELL    ·    INFERNAL  IDENTITY  CARD"
    try:
        hdr_w = draw.textlength(header_text, font=hdr_font)
    except AttributeError:
        hdr_w = len(header_text) * 6
    hdr_x = (W - hdr_w) // 2
    draw.text((hdr_x, 12), header_text, font=hdr_font,
              fill=(*t["text2"][:3], 130))

    # ── 5. Header divider line ──────────────────────────────────────────
    _divider(draw, 24, 28, W - 24, t["border"], 60)

    # ── 6. LEFT SECTION ─────────────────────────────────────────────────
    # Avatar
    _apply_avatar(card, avatar_bytes, t)
    draw = ImageDraw.Draw(card)

    # Section center x for left
    lcx = (AVATAR_X + LEFT_END) // 2

    # Username
    user_font = _font(17, bold=True)
    try:
        uw = draw.textlength(username, font=user_font)
    except AttributeError:
        uw = len(username) * 10
    ux = max(AVATAR_X, min(lcx - uw // 2, LEFT_END - int(uw) - 4))
    _glow_text(card, ImageDraw.Draw(card),
               (ux, AVATAR_Y + AVATAR_SIZE + 10),
               username, user_font,
               t["text1"], t["glow"], radius=6)
    draw = ImageDraw.Draw(card)

    # Equipped title
    title_font = _font(11)
    title_color = (*t["accent"][:3], 220)
    try:
        tw = draw.textlength(equipped_title, font=title_font)
    except AttributeError:
        tw = len(equipped_title) * 7
    tx = max(AVATAR_X, lcx - tw // 2)
    draw.text((tx, AVATAR_Y + AVATAR_SIZE + 32), equipped_title,
              font=title_font, fill=title_color)

    # Rank
    rank_font = _font(13, bold=True, cinzel=True)
    rank_color = (*t["gold"][:3], 240)
    try:
        rw = draw.textlength(rank, font=rank_font)
    except AttributeError:
        rw = len(rank) * 9
    rx = max(AVATAR_X, lcx - rw // 2)
    _glow_text(card, ImageDraw.Draw(card),
               (rx, AVATAR_Y + AVATAR_SIZE + 50),
               rank, rank_font,
               rank_color, t["glow"], radius=5)
    draw = ImageDraw.Draw(card)

    # Tax bracket
    from bot.services.rank_service import RANK_DICT
    rank_entry = RANK_DICT.get(rank, {})
    tax_rate = rank_entry.get("tax_rate", 0.12)
    tax_str = "TAX EXEMPT" if tax_rate == 0 else f"TAX  {int(tax_rate * 100)}%"
    tax_font = _font(9)
    try:
        txw = draw.textlength(tax_str, font=tax_font)
    except AttributeError:
        txw = len(tax_str) * 6
    draw.text((max(AVATAR_X, lcx - txw // 2), AVATAR_Y + AVATAR_SIZE + 70),
              tax_str, font=tax_font, fill=(*t["text2"][:3], 160))

    # ── 7. CENTER SECTION ───────────────────────────────────────────────
    cx_section = CENTER_X + 8
    cy_top = 36

    # "WEALTH" label
    lbl_font = _font(9, cinzel=True)
    draw.text((cx_section, cy_top), "WEALTH", font=lbl_font,
              fill=(*t["text2"][:3], 180))

    # Balance — dominant element
    bal_str = format_dc(balance)
    bal_font = _font(38, bold=True)
    try:
        bal_w = draw.textlength(bal_str, font=bal_font)
    except AttributeError:
        bal_w = len(bal_str) * 22
    _glow_text(card, ImageDraw.Draw(card),
               (cx_section, cy_top + 14),
               bal_str, bal_font,
               t["gold"], t["glow"], radius=10)
    draw = ImageDraw.Draw(card)

    # Separator
    _divider(draw, cx_section, cy_top + 62, CENTER_END - 12, t["border"], 70)

    # Kingdom Rank row
    kr_y = cy_top + 72
    draw.text((cx_section, kr_y), "KINGDOM  RANK", font=lbl_font,
              fill=(*t["text2"][:3], 180))
    kr_val = f"#{kingdom_rank}"
    kr_font = _font(22, bold=True, cinzel=True)
    _glow_text(card, ImageDraw.Draw(card),
               (cx_section, kr_y + 14),
               kr_val, kr_font,
               t["accent"], t["glow"], radius=7)
    draw = ImageDraw.Draw(card)

    # Separator
    _divider(draw, cx_section, kr_y + 46, CENTER_END - 12, t["border"], 70)

    # Taxes filed
    tax_y = kr_y + 56
    draw.text((cx_section, tax_y), "TAXES  FILED", font=lbl_font,
              fill=(*t["text2"][:3], 180))
    tx_val_font = _font(14, bold=True)
    draw.text((cx_section, tax_y + 14), format_dc(taxes_paid),
              font=tx_val_font, fill=(*t["text1"][:3], 200))

    # Risk score (if present)
    if risk_score > 0:
        _divider(draw, cx_section, tax_y + 40, CENTER_END - 12, t["border"], 50)
        draw.text((cx_section, tax_y + 50), "RISK  SCORE", font=lbl_font,
                  fill=(*t["text2"][:3], 150))
        risk_col = (220, 80, 80, 220) if risk_score >= 50 else (*t["accent"][:3], 200)
        draw.text((cx_section, tax_y + 63), f"{risk_score} / 100",
                  font=_font(13, bold=True), fill=risk_col)

    # ── 8. RIGHT SECTION (SIGIL) ────────────────────────────────────────
    sig_cx = RIGHT_X + (W - RIGHT_X) // 2 + 4   # ~793
    sig_cy = H // 2 + 5                           # ~165

    # Draw sigil on a dedicated glow layer
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_sigil(glow_layer, sig_cx, sig_cy, t)
    blurred = glow_layer.filter(ImageFilter.GaussianBlur(10))
    card.alpha_composite(blurred)
    card.alpha_composite(glow_layer)
    draw = ImageDraw.Draw(card)

    # Skin name tag at bottom of right section
    skin_name = {
        None: "Infernal Standard",
        "default": "Infernal Standard",
        "blood_crown": "Blood Crown",
        "abyss_smoke": "Abyss Smoke",
        "infernal_gold": "Infernal Gold",
        "royal_dark": "Royal Dark",
        "black_throne": "Black Throne",
        "crimson_sigil": "Crimson Sigil",
    }.get(skin_id, "Infernal Standard")

    sn_font = _font(8)
    try:
        snw = draw.textlength(skin_name, font=sn_font)
    except AttributeError:
        snw = len(skin_name) * 5
    draw.text((sig_cx - snw // 2, H - 38), skin_name,
              font=sn_font, fill=(*t["text2"][:3], 100))

    # ── 9. Footer divider + flavor text ─────────────────────────────────
    _divider(draw, 24, H - 28, W - 24, t["border"], 60)
    foot_font = _font(9)
    try:
        fw = draw.textlength(footer_flavor, font=foot_font)
    except AttributeError:
        fw = len(footer_flavor) * 5
    draw.text(((W - fw) // 2, H - 20), footer_flavor,
              font=foot_font, fill=(*t["text2"][:3], 140))

    # ── 10. Rounded corner mask (clip card) ─────────────────────────────
    mask = _rounded_mask(W, H, RADIUS)
    card.putalpha(mask)

    # ── 11. Serialize ────────────────────────────────────────────────────
    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


# ─── Async avatar fetch ───────────────────────────────────────────────────────

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
