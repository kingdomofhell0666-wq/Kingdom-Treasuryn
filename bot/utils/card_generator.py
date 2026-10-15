"""
Kingdom Treasury — Infernal Identity Card Generator
1200 × 720 px  |  Horizontal Government ID  |  Pillow
Layout: Header · [Avatar+Balance | Identity | Sigil] · Artifacts · Footer
"""

import io
import math
import random as _random
import urllib.request
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .identity_variant import EffectiveCardVariant
from .skins import RANK_ORDER, BADGES_CATALOG, RELICS_CATALOG

# ─── Asset paths ──────────────────────────────────────────────────────────────
_CINZEL    = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_LOGO_PATH = "bot/assets/server_logo.png"   # drop file here to use real logo

# ─── Card geometry — 1200×720 spacious horizontal ID ─────────────────────────
W, H      = 1200, 720
RADIUS    = 22
OUT_PAD   = 24               # outer edge padding
IN_PAD    = 18               # inner content padding

# ── Column grid (3-column fixed layout) ───────────────────────────────────────
# Columns never shift — skins only change colours/textures, never layout.
LFT_X     = OUT_PAD          # 24
LFT_W     = 234
LFT_R     = LFT_X + LFT_W   # 258

CTR_X     = 278              # center col starts (gap 20 after LFT_R)
CTR_W     = 688
CTR_R     = CTR_X + CTR_W   # 966

RGT_X     = 986              # right col starts (gap 20 after CTR_R)
RGT_W     = W - RGT_X - OUT_PAD   # 190
RGT_R     = RGT_X + RGT_W   # 1176

# ── Zone boundaries (y) ───────────────────────────────────────────────────────
HEADER_H  = 58               # y =   0 –  58  header strip
HDR_H     = HEADER_H
MAIN_Y    = 58               # y =  58 – 456  three-column main body
MAIN_END  = 456
ART_Y     = 468              # y = 468 – 628  bound artifacts row
ARTS_END  = 628
BADGE_Y   = 638              # y = 638 – 668  circular seals row
FOOTER_Y  = 678              # y = 678 – 720  footer

# ── Avatar fixed position (inside left column) ────────────────────────────────
AV_X      = LFT_X            # 24
AV_Y      = MAIN_Y + 16     # 74
AV_SZ     = 200
AV_RADIUS = 16               # rounded corners

# PAD alias — helpers (_line, _double_line, etc.) still reference it
PAD       = OUT_PAD

# ── Legacy aliases (relic/rank helpers may reference old names) ────────────────
DIV1      = HEADER_H
IDENT_Y   = MAIN_Y
BAL_Y     = MAIN_Y
DIV2      = MAIN_END
STATS_Y   = MAIN_Y
DIV3      = MAIN_END
AUDIT_Y   = ART_Y
DIV4      = MAIN_END
DIV5      = ARTS_END
WEALTH_Y  = MAIN_Y
ID_Y      = MAIN_Y
ID_DATA_X = CTR_X
IDENT_X   = CTR_X
IDENT_R   = CTR_R

# ─── Skin themes ──────────────────────────────────────────────────────────────
THEMES = {
    "default": dict(
        bg1=(8, 3, 3),    bg2=(22, 7, 7),
        border=(110, 0, 0),  accent=(185, 22, 22),
        gold=(215, 168, 42), text1=(232, 212, 212),
        text2=(148, 102, 102), glow=(150, 0, 0),
        wealth_hl=(25, 6, 6),  sigil="star",
    ),
    "blood_crown": dict(
        bg1=(16, 0, 0),   bg2=(38, 3, 3),
        border=(185, 0, 0),  accent=(238, 10, 10),
        gold=(232, 158, 22), text1=(252, 222, 218),
        text2=(178, 112, 112), glow=(222, 0, 0),
        wealth_hl=(40, 4, 4),  sigil="crown",
    ),
    "abyss_smoke": dict(
        bg1=(4, 2, 14),   bg2=(10, 5, 28),
        border=(75, 22, 148), accent=(155, 70, 238),
        gold=(188, 142, 255), text1=(220, 208, 250),
        text2=(132, 108, 190), glow=(122, 50, 220),
        wealth_hl=(12, 6, 40),  sigil="eye",
    ),
    "infernal_gold": dict(
        bg1=(12, 8, 0),   bg2=(28, 16, 2),
        border=(175, 130, 0), accent=(222, 172, 0),
        gold=(255, 220, 42), text1=(255, 242, 205),
        text2=(192, 150, 80), glow=(218, 170, 0),
        wealth_hl=(30, 20, 2),  sigil="sun",
    ),
    "royal_dark": dict(
        bg1=(2, 4, 20),   bg2=(6, 8, 42),
        border=(30, 42, 162), accent=(78, 98, 225),
        gold=(198, 180, 255), text1=(220, 222, 255),
        text2=(128, 130, 205), glow=(58, 68, 195),
        wealth_hl=(8, 10, 48),  sigil="fleur",
    ),
    "black_throne": dict(
        bg1=(6, 4, 4),    bg2=(18, 12, 12),
        border=(68, 50, 50),  accent=(158, 132, 132),
        gold=(212, 198, 188), text1=(242, 230, 230),
        text2=(148, 128, 128), glow=(108, 86, 86),
        wealth_hl=(22, 14, 14),  sigil="throne",
    ),
    "crimson_sigil": dict(
        bg1=(14, 2, 4),   bg2=(32, 5, 8),
        border=(192, 28, 55), accent=(228, 42, 72),
        gold=(250, 180, 55), text1=(252, 218, 222),
        text2=(185, 112, 125), glow=(205, 18, 50),
        wealth_hl=(34, 4, 8),  sigil="sigil",
    ),
    # ── New skins added ────────────────────────────────────────────────────────
    "ember_ash": dict(
        bg1=(10, 5, 2),   bg2=(26, 12, 5),
        border=(132, 72, 32), accent=(198, 108, 45),
        gold=(238, 168, 72), text1=(248, 212, 172),
        text2=(178, 130, 82), glow=(182, 90, 38),
        wealth_hl=(26, 12, 5),  sigil="crown",
    ),
    "bone_pale": dict(
        bg1=(8, 6, 3),    bg2=(20, 16, 10),
        border=(118, 102, 78), accent=(185, 168, 135),
        gold=(218, 195, 152), text1=(242, 232, 210),
        text2=(162, 145, 112), glow=(145, 122, 88),
        wealth_hl=(18, 14, 8),  sigil="star",
    ),
    "phantom_teal": dict(
        bg1=(2, 10, 12),  bg2=(5, 22, 26),
        border=(0, 90, 108), accent=(0, 170, 190),
        gold=(0, 222, 232), text1=(178, 240, 244),
        text2=(80, 170, 182), glow=(0, 142, 158),
        wealth_hl=(4, 20, 26),  sigil="eye",
    ),
    "midnight_azure": dict(
        bg1=(0, 4, 18),   bg2=(2, 10, 40),
        border=(20, 62, 168), accent=(45, 118, 228),
        gold=(138, 190, 255), text1=(200, 222, 255),
        text2=(88, 136, 202), glow=(28, 92, 202),
        wealth_hl=(4, 12, 46),  sigil="star",
    ),
    "magma_core": dict(
        bg1=(8, 2, 0),    bg2=(24, 6, 0),
        border=(168, 55, 0), accent=(228, 88, 0),
        gold=(255, 172, 45), text1=(255, 222, 178),
        text2=(188, 122, 68), glow=(212, 72, 0),
        wealth_hl=(28, 6, 0),  sigil="sigil",
    ),
    "cursed_silver": dict(
        bg1=(4, 4, 6),    bg2=(12, 12, 20),
        border=(88, 88, 118), accent=(178, 178, 215),
        gold=(222, 222, 242), text1=(238, 238, 250),
        text2=(142, 142, 172), glow=(148, 148, 188),
        wealth_hl=(14, 14, 24),  sigil="throne",
    ),
    "verdant_venom": dict(
        bg1=(2, 10, 2),   bg2=(5, 22, 6),
        border=(18, 120, 24), accent=(40, 208, 50),
        gold=(118, 255, 98), text1=(188, 248, 190),
        text2=(78, 180, 84), glow=(28, 178, 38),
        wealth_hl=(6, 22, 6),  sigil="sigil",
    ),
    "abyssal_jade": dict(
        bg1=(2, 8, 6),    bg2=(5, 18, 14),
        border=(14, 100, 72), accent=(28, 188, 138),
        gold=(88, 242, 195), text1=(178, 242, 218),
        text2=(58, 168, 120), glow=(18, 152, 108),
        wealth_hl=(6, 20, 14),  sigil="eye",
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


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        return len(text) * max(8, getattr(font, "size", 8) // 2)


def _fit_font(draw, text: str, max_w: int,
              start: int, stop: int, bold=False, cinzel=False):
    for sz in range(start, stop - 1, -1):
        f = _font(sz, bold=bold, cinzel=cinzel)
        if _tw(draw, text, f) <= max_w:
            return f
    return _font(stop, bold=bold, cinzel=cinzel)


# ─── Gradient + mask ──────────────────────────────────────────────────────────

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


def _card_mask(w: int, h: int, r: int) -> Image.Image:
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=r, fill=255)
    return m


# ─── Glow text ────────────────────────────────────────────────────────────────

def _glow(card: Image.Image, xy: tuple, text: str, font,
          color: tuple, glow_col: tuple, blur: int = 10, spread: int = 3):
    layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    gc = (*glow_col[:3], 130)
    for dx in range(-spread, spread + 1):
        for dy in range(-spread, spread + 1):
            if dx * dx + dy * dy <= spread * spread + 1:
                d.text((xy[0] + dx, xy[1] + dy), text, font=font, fill=gc)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    card.alpha_composite(layer)
    ImageDraw.Draw(card).text(xy, text, font=font, fill=(*color[:3], 255))


# ─── Dividers ─────────────────────────────────────────────────────────────────

def _line(draw, y: int, theme: dict, alpha: int = 65,
          x1: int = PAD, x2: int = W - PAD):
    draw.line([(x1, y), (x2, y)], fill=(*theme["border"][:3], alpha), width=1)


def _double_line(draw, y: int, theme: dict):
    draw.line([(PAD, y), (W - PAD, y)], fill=(*theme["border"][:3], 80), width=1)
    draw.line([(PAD, y + 3), (W - PAD, y + 3)], fill=(*theme["border"][:3], 30), width=1)


# ─── Risk Tier system ─────────────────────────────────────────────────────────

def get_risk_tier(risk: int) -> dict:
    """Return tier metadata for a given risk score (0-100)."""
    if risk <= 20:
        return dict(
            label="LOW",
            color=(80, 200, 120),          # calm green
            border_alpha=0,
            overlay_alpha=0,
            border_color=(0, 0, 0),
            cerberus_line=None,
            glow_boost=0,
        )
    elif risk <= 50:
        return dict(
            label="MEDIUM",
            color=(210, 165, 40),          # amber gold
            border_alpha=40,
            overlay_alpha=18,
            border_color=(180, 100, 0),
            cerberus_line="Cerberus has taken notice.",
            glow_boost=0,
        )
    elif risk <= 80:
        return dict(
            label="HIGH",
            color=(215, 80, 40),           # deep orange-red
            border_alpha=80,
            overlay_alpha=38,
            border_color=(190, 30, 0),
            cerberus_line="Cerberus is watching.",
            glow_boost=1,
        )
    else:
        return dict(
            label="CRITICAL",
            color=(230, 30, 30),           # bright danger red
            border_alpha=130,
            overlay_alpha=62,
            border_color=(220, 0, 0),
            cerberus_line="Your ledger is no longer clean.",
            glow_boost=2,
        )


def _risk_tier_overlay(card: Image.Image, risk: int):
    """Apply a visual overlay to the card that intensifies with risk tier."""
    tier = get_risk_tier(risk)
    if tier["overlay_alpha"] == 0:
        return

    oa = tier["overlay_alpha"]
    bc = tier["border_color"]

    # Corner vignette — dark red bleeds in from all four corners
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)

    # Top edge
    for i in range(80):
        a = int(oa * (1 - i / 80) * 1.4)
        vd.line([(0, i), (W, i)], fill=(*bc, a))
    # Bottom edge
    for i in range(80):
        a = int(oa * (1 - i / 80) * 1.4)
        vd.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(*bc, a))
    # Left edge
    for i in range(60):
        a = int(oa * (1 - i / 60))
        vd.line([(i, 0), (i, H)], fill=(*bc, a))
    # Right edge
    for i in range(60):
        a = int(oa * (1 - i / 60))
        vd.line([(W - 1 - i, 0), (W - 1 - i, H)], fill=(*bc, a))

    card.alpha_composite(vignette)

    # Glowing danger border for HIGH and CRITICAL
    ba = tier["border_alpha"]
    if ba > 0:
        border_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(border_layer)
        bd.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                              radius=RADIUS, outline=(*bc, ba), width=3)
        blurred = border_layer.filter(ImageFilter.GaussianBlur(8))
        card.alpha_composite(blurred)
        bd2 = ImageDraw.Draw(border_layer)
        bd2.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                               radius=RADIUS, outline=(*bc, min(255, ba + 40)), width=2)
        card.alpha_composite(border_layer)


# ─── Right-column authority emblem ────────────────────────────────────────────
# Loads bot/assets/server_logo.png when present; falls back to drawn crest.
# The logo is composited at ~75% opacity, centred in the right column.

def _bg_sigil(card: Image.Image, theme: dict):
    # Centre of right column: RGT_X + RGT_W//2, (MAIN_Y + MAIN_END)//2
    cx = RGT_X + RGT_W // 2   # ≈ 1081
    cy = (MAIN_Y + MAIN_END) // 2  # ≈ 257
    _render_right_logo(card, theme, cx, cy, max_dim=175)


def _render_right_logo(card: Image.Image, theme: dict,
                        cx: int, cy: int, max_dim: int = 160):
    import os

    # ── Try loading the server logo ──────────────────────────────────────────
    logo_loaded = False
    if os.path.isfile(_LOGO_PATH):
        try:
            logo = Image.open(_LOGO_PATH).convert("RGBA")

            # Scale preserving aspect ratio to fit max_dim × max_dim box
            lw, lh = logo.size
            scale  = min(max_dim / lw, max_dim / lh)
            nw, nh = int(lw * scale), int(lh * scale)
            logo   = logo.resize((nw, nh), Image.LANCZOS)

            # Subtle glow behind the logo — blurred tinted ellipse
            glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            gr = max(nw, nh) // 2 + 20
            gd.ellipse([(cx - gr, cy - gr), (cx + gr, cy + gr)],
                       fill=(*theme["glow"][:3], 35))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(28))
            card.alpha_composite(glow_layer)

            # Apply 72% opacity watermark treatment
            logo_data = logo.split()
            if len(logo_data) == 4:
                r_, g_, b_, a_ = logo_data
                new_a = a_.point(lambda v: int(v * 0.72))
                logo.putalpha(new_a)
            else:
                logo = logo.convert("RGBA")
                alpha_ch = logo.split()[3].point(lambda v: int(v * 0.72))
                logo.putalpha(alpha_ch)

            paste_x = cx - nw // 2
            paste_y = cy - nh // 2
            card.alpha_composite(logo, (paste_x, paste_y))
            logo_loaded = True
        except Exception:
            pass   # fall through to drawn crest

    # ── Fallback: clean drawn infernal crest ────────────────────────────────
    if not logo_loaded:
        _draw_infernal_crest(card, theme, cx, cy, max_dim // 2)


# ─── Sigil primitives ─────────────────────────────────────────────────────────

def _sig_star(draw, cx, cy, r, col, n=5):
    inner = r * 0.40
    pts = []
    for i in range(n * 2):
        ang = math.pi * i / n - math.pi / 2
        rad = r if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, outline=col, width=3)
    draw.ellipse([(cx - r * 0.20, cy - r * 0.20), (cx + r * 0.20, cy + r * 0.20)], outline=col, width=2)
    draw.ellipse([(cx - r - 14, cy - r - 14), (cx + r + 14, cy + r + 14)], outline=(*col[:3], col[3] // 2), width=2)


def _sig_crown(draw, cx, cy, r, col):
    s = r
    by = cy + s * 0.20
    bh = s * 0.28
    draw.rectangle([(cx - s * 0.56, by), (cx + s * 0.56, by + bh)], outline=col, width=3)
    for ox, h_ in [(-s * 0.38, s * 0.38), (0, s * 0.62), (s * 0.38, s * 0.38)]:
        draw.polygon([(cx + ox - s * 0.10, by), (cx + ox, by - h_), (cx + ox + s * 0.10, by)], outline=col, width=2)
        gx, gy = cx + ox, by - h_
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
        x2, y2 = cx + (r + 24) * math.cos(ang), cy + (r + 24) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=col, width=2)


def _sig_sun(draw, cx, cy, r, col):
    for i in range(12):
        ang = math.pi * 2 * i / 12
        r_in = r + 4
        r_out = r + 36 if i % 2 == 0 else r + 20
        draw.line([(cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)),
                   (cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))],
                  fill=col, width=3 if i % 2 == 0 else 1)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=3)
    ir = r * 0.48
    draw.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)], outline=col, width=2)
    draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=col)


def _sig_fleur(draw, cx, cy, r, col):
    s = r
    draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=col)
    for ox, oy, rw, rh in [
        (0, -s * 0.40, s * 0.16, s * 0.38),
        (-s * 0.38, -s * 0.16, s * 0.32, s * 0.15),
        (s * 0.38, -s * 0.16, s * 0.32, s * 0.15),
    ]:
        draw.ellipse([(cx + ox - rw, cy + oy - rh), (cx + ox + rw, cy + oy + rh)], outline=col, width=2)
    draw.rectangle([(cx - s * 0.07, cy + 6), (cx + s * 0.07, cy + s * 0.48)], outline=col, width=2)
    draw.rectangle([(cx - s * 0.24, cy + s * 0.34), (cx + s * 0.24, cy + s * 0.52)], outline=col, width=2)
    draw.ellipse([(cx - s * 0.74, cy - s * 0.74), (cx + s * 0.74, cy + s * 0.74)],
                 outline=(*col[:3], col[3] // 2), width=2)


def _sig_throne(draw, cx, cy, r, col):
    s = r
    draw.rectangle([(cx - s * 0.40, cy - s * 0.58), (cx + s * 0.40, cy + s * 0.48)], outline=col, width=3)
    draw.rectangle([(cx - s * 0.46, cy + s * 0.10), (cx + s * 0.46, cy + s * 0.28)], outline=col, width=2)
    for side in [-1, 1]:
        lx_ = cx + min(side * s * 0.40, side * s * 0.55)
        rx_ = cx + max(side * s * 0.40, side * s * 0.55)
        draw.rectangle([(lx_, cy - s * 0.05), (rx_, cy + s * 0.28)], outline=col, width=2)
    lw = s * 0.08
    for lx_ in [cx - s * 0.36, cx + s * 0.36 - lw]:
        draw.rectangle([(lx_, cy + s * 0.28), (lx_ + lw, cy + s * 0.58)], outline=col, width=2)
    top_y = cy - s * 0.58
    for fx in [cx - s * 0.22, cx, cx + s * 0.22]:
        draw.polygon([(fx - 6, top_y), (fx, top_y - 16), (fx + 6, top_y)], fill=col)
    draw.ellipse([(cx - s * 0.78, cy - s * 0.78), (cx + s * 0.78, cy + s * 0.78)],
                 outline=(*col[:3], col[3] // 2), width=2)


def _sig_cross(draw, cx, cy, r, col):
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=3)
    draw.ellipse([(cx - r + 12, cy - r + 12), (cx + r - 12, cy + r - 12)],
                 outline=(*col[:3], col[3] // 2), width=1)
    arm, thick = r - 5, 8
    draw.rectangle([(cx - thick, cy - arm), (cx + thick, cy + arm)], fill=col)
    draw.rectangle([(cx - arm, cy - thick), (cx + arm, cy + thick)], fill=col)
    for ex_, ey_ in [(cx, cy - arm), (cx, cy + arm), (cx - arm, cy), (cx + arm, cy)]:
        draw.ellipse([(ex_ - 8, ey_ - 8), (ex_ + 8, ey_ + 8)], fill=col)
    draw.ellipse([(cx - r - 14, cy - r - 14), (cx + r + 14, cy + r + 14)],
                 outline=(*col[:3], col[3] // 3), width=2)


# ─── Clean infernal crest (logo fallback) ────────────────────────────────────

def _draw_infernal_crest(card: Image.Image, theme: dict,
                          cx: int, cy: int, r: int):
    """
    High-quality drawn crest for the right column when no logo PNG is available.
    Three concentric rings + five-point star + central circle + subtle glow.
    All drawn at low alpha for the watermark treatment.
    """
    col_full  = (*theme["glow"][:3], 58)
    col_half  = (*theme["glow"][:3], 30)
    col_dim   = (*theme["glow"][:3], 18)
    gold_full = (*theme["gold"][:3], 50)
    gold_dim  = (*theme["gold"][:3], 22)

    # ── Glow halo behind crest ─────────────────────────────────────────────
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gld = ImageDraw.Draw(gl)
    gld.ellipse([(cx - r - 30, cy - r - 30), (cx + r + 30, cy + r + 30)],
                fill=(*theme["glow"][:3], 32))
    gl = gl.filter(ImageFilter.GaussianBlur(24))
    card.alpha_composite(gl)

    lyr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(lyr)

    # ── Outer ring ─────────────────────────────────────────────────────────
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
              outline=col_full, width=2)

    # ── Eight tick marks on the outer ring ─────────────────────────────────
    for i in range(8):
        ang   = math.pi * 2 * i / 8 - math.pi / 2
        r_in  = r - 6
        r_out = r + 2
        d.line([(cx + r_in * math.cos(ang),  cy + r_in * math.sin(ang)),
                (cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))],
               fill=col_half, width=1)

    # ── Mid ring ────────────────────────────────────────────────────────────
    mr = int(r * 0.72)
    d.ellipse([(cx - mr, cy - mr), (cx + mr, cy + mr)],
              outline=col_half, width=1)

    # ── Five-point star inside mid ring ────────────────────────────────────
    star_r  = int(r * 0.60)
    star_in = int(star_r * 0.42)
    pts = []
    for i in range(10):
        ang = math.pi * i / 5 - math.pi / 2
        rad = star_r if i % 2 == 0 else star_in
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, outline=gold_full, width=1)

    # ── Inner ring ──────────────────────────────────────────────────────────
    ir = int(r * 0.32)
    d.ellipse([(cx - ir, cy - ir), (cx + ir, cy + ir)],
              outline=gold_full, width=1)

    # ── Central dot ─────────────────────────────────────────────────────────
    cr_ = int(r * 0.10)
    d.ellipse([(cx - cr_, cy - cr_), (cx + cr_, cy + cr_)],
              fill=gold_dim)

    # ── KINGDOM OF HELL arc text (top, tiny, spaced) ───────────────────────
    # We approximate arc text with straight tiny text above center
    arc_lbl   = "KINGDOM  OF  HELL"
    arc_f     = _font(6, cinzel=True)
    arc_w     = _tw(d, arc_lbl, arc_f)
    d.text((cx - arc_w // 2, cy - r - 14), arc_lbl,
           font=arc_f, fill=(*theme["gold"][:3], 42))

    lyr = lyr.filter(ImageFilter.GaussianBlur(0.4))  # light anti-alias
    card.alpha_composite(lyr)


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
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (sz - 1, sz - 1)], radius=16, fill=255)
    av.putalpha(mask)

    # Glow border
    bsz = sz + 10
    border = Image.new("RGBA", (bsz, bsz), (0, 0, 0, 0))
    bc = (*theme["accent"][:3], 200)
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (bsz - 1, bsz - 1)], radius=19, outline=bc, width=3
    )
    # Glow
    glow_layer = border.filter(ImageFilter.GaussianBlur(6))
    card.alpha_composite(glow_layer, (AV_X - 5, AV_Y - 5))
    card.alpha_composite(border, (AV_X - 5, AV_Y - 5))
    card.alpha_composite(av, (AV_X, AV_Y))


def _placeholder_avatar(sz: int, theme: dict) -> Image.Image:
    av = Image.new("RGBA", (sz, sz), (*theme["bg2"][:3], 255))
    d = ImageDraw.Draw(av)
    c = (*theme["accent"][:3], 160)
    m = sz // 2
    d.ellipse([(m - 22, 16), (m + 22, 62)], fill=c)
    d.ellipse([(m - 36, 66), (m + 36, sz - 4)], fill=c)
    return av


def _paste_avatar_square(card: Image.Image, av_bytes: Optional[bytes],
                          theme: dict, x: int, y: int, sz: int, rank_level: int):
    """Passport-style square photo with official document frame."""
    if av_bytes:
        try:
            av = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize(
                (sz, sz), Image.LANCZOS)
        except Exception:
            av = _placeholder_avatar(sz, theme)
    else:
        av = _placeholder_avatar(sz, theme)

    av.putalpha(Image.new("L", (sz, sz), 255))
    card.alpha_composite(av, (x, y))

    d = ImageDraw.Draw(card)
    # Inner frame
    d.rectangle([(x - 1, y - 1), (x + sz, y + sz)],
                outline=(*theme["border"][:3], 200), width=1)
    # Outer frame
    d.rectangle([(x - 4, y - 4), (x + sz + 3, y + sz + 3)],
                outline=(*theme["border"][:3], 110), width=1)


# ─── Wealth zone highlight ────────────────────────────────────────────────────

def _wealth_highlight(card: Image.Image, theme: dict):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hl = (*theme["wealth_hl"][:3], 120)
    d.rounded_rectangle([(PAD, WEALTH_Y + 4), (W - PAD, DIV3 - 4)],
                         radius=14, fill=hl)
    card.alpha_composite(layer)


# ─── Risk bar (for audit FLAGGED state) ───────────────────────────────────────

def _risk_bar(draw: ImageDraw.ImageDraw, risk: int, theme: dict, y: int):
    bar_x, bar_w, bar_h = PAD + 60, W - PAD * 2 - 120, 10
    draw.rounded_rectangle([(bar_x, y), (bar_x + bar_w, y + bar_h)],
                             radius=5, fill=(*theme["bg2"][:3], 180), outline=(80, 0, 0, 160), width=1)
    fill_w = int(bar_w * risk / 100)
    r_col = (220, 38, 38) if risk >= 60 else (200, 130, 30) if risk >= 35 else (80, 180, 80)
    if fill_w > 0:
        draw.rounded_rectangle([(bar_x, y), (bar_x + fill_w, y + bar_h)],
                                 radius=5, fill=(*r_col, 220))


# ─── Main generator ───────────────────────────────────────────────────────────

_COIN_EMOJI_URL   = "https://cdn.discordapp.com/emojis/1492184333392412692.png"
_coin_icon_cache: dict = {}   # size (int) → Image.Image


def _get_coin_icon(size: int) -> Optional[Image.Image]:
    """Fetch the DevilCoin emoji PNG from Discord CDN and cache by size."""
    if size in _coin_icon_cache:
        return _coin_icon_cache[size]
    try:
        req = urllib.request.Request(_COIN_EMOJI_URL, headers={"User-Agent": "KingdomBot/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = resp.read()
        icon = Image.open(io.BytesIO(data)).convert("RGBA")
        icon = icon.resize((size, size), Image.LANCZOS)
        _coin_icon_cache[size] = icon
        return icon
    except Exception:
        return None


def _composite_coin(card: Image.Image, x: int, y: int, size: int,
                    alpha: int = 240) -> None:
    """Paste the DevilCoin icon onto the card at (x, y) with given pixel size."""
    icon = _get_coin_icon(size)
    if icon is None:
        return
    # Apply alpha multiplier so icon blends with card atmosphere
    r, g, b, a = icon.split()
    a = a.point(lambda v: int(v * alpha / 255))
    icon_mod = Image.merge("RGBA", (r, g, b, a))
    card.alpha_composite(icon_mod, dest=(int(x), int(y)))


def _fmt_dc(n: int) -> str:
    """Number string only — coin icon is stamped separately on the card."""
    return f"{n:,}"


def _apply_relic_effect(card: Image.Image, relic_id: Optional[str], theme: dict):
    """Overlay a relic's visual effect onto the identity card (RGBA, 900×1100)."""
    if not relic_id:
        return

    # ── soul_aura — glowing luminescent border ─────────────────────────────
    if relic_id == "soul_aura":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        gc    = (*theme["glow"][:3], 60)
        for offset in range(1, 8):
            d.rounded_rectangle(
                [(offset, offset), (W - 1 - offset, H - 1 - offset)],
                radius=RADIUS, outline=gc, width=1,
            )
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        card.alpha_composite(layer)
        # Sharp bright outer ring
        d2 = ImageDraw.Draw(card)
        d2.rounded_rectangle(
            [(2, 2), (W - 3, H - 3)],
            radius=RADIUS, outline=(*theme["accent"][:3], 140), width=2,
        )
        d2.rounded_rectangle(
            [(6, 6), (W - 7, H - 7)],
            radius=RADIUS - 3, outline=(*theme["accent"][:3], 50), width=1,
        )

    # ── infernal_crown — gold crown above avatar ───────────────────────────
    elif relic_id == "infernal_crown":
        cx  = AV_X + AV_SZ // 2
        cy  = AV_Y + 2
        gold = theme["gold"][:3]

        # Glow layer
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        for spike_x, tip_y in [(cx - 24, cy - 26), (cx, cy - 38), (cx + 24, cy - 26)]:
            d.polygon(
                [(spike_x - 10, cy - 6), (spike_x + 10, cy - 6), (spike_x, tip_y)],
                fill=(*gold, 90),
            )
        d.rectangle([(cx - 42, cy - 9), (cx + 42, cy - 1)], fill=(*gold, 90))
        layer = layer.filter(ImageFilter.GaussianBlur(5))
        card.alpha_composite(layer)

        # Sharp crown
        d2 = ImageDraw.Draw(card)
        for spike_x, tip_y in [(cx - 24, cy - 26), (cx, cy - 38), (cx + 24, cy - 26)]:
            d2.polygon(
                [(spike_x - 10, cy - 6), (spike_x + 10, cy - 6), (spike_x, tip_y)],
                fill=(*gold, 210),
            )
        d2.rectangle([(cx - 42, cy - 9), (cx + 42, cy - 1)], fill=(*gold, 200))
        # Gem dots on crown tips
        for gx, gy in [(cx - 24, cy - 26), (cx, cy - 38), (cx + 24, cy - 26)]:
            d2.ellipse([(gx - 3, gy - 3), (gx + 3, gy + 3)],
                       fill=(*theme["accent"][:3], 230))

    # ── void_drift — scattered void particles ─────────────────────────────
    elif relic_id == "void_drift":
        # Deterministic particle positions based on fixed seeds
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        vc    = (88, 42, 180)  # void purple
        rng   = _random.Random(42)
        for _ in range(22):
            px   = rng.randint(PAD + 10, W - PAD - 10)
            py   = rng.randint(HEADER_H + 10, H - 60)
            r    = rng.randint(1, 4)
            alpha= rng.randint(80, 200)
            d.ellipse([(px - r, py - r), (px + r, py + r)], fill=(*vc, alpha))
        # Some larger faint orbs
        for _ in range(6):
            px   = rng.randint(PAD + 20, W - PAD - 20)
            py   = rng.randint(100, H - 100)
            r    = rng.randint(5, 10)
            d.ellipse([(px - r, py - r), (px + r, py + r)], fill=(*vc, 35))
        layer = layer.filter(ImageFilter.GaussianBlur(1))
        card.alpha_composite(layer)

    # ── crimson_chains — chain links along left/right borders ─────────────
    elif relic_id == "crimson_chains":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        cc    = (185, 0, 0)
        # Left edge chain
        for y in range(60, H - 60, 32):
            d.ellipse([(PAD, y), (PAD + 16, y + 20)],   outline=(*cc, 180), width=2)
            d.ellipse([(PAD + 4, y + 14), (PAD + 20, y + 34)], outline=(*cc, 140), width=2)
        # Right edge chain
        for y in range(60, H - 60, 32):
            d.ellipse([(W - PAD - 16, y), (W - PAD, y + 20)],     outline=(*cc, 180), width=2)
            d.ellipse([(W - PAD - 20, y + 14), (W - PAD - 4, y + 34)], outline=(*cc, 140), width=2)
        layer = layer.filter(ImageFilter.GaussianBlur(0.8))
        card.alpha_composite(layer)

    # ── abyssal_veil — diagonal dark translucent bands ────────────────────
    elif relic_id == "abyssal_veil":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        for i, (y_off, alpha) in enumerate([(100, 28), (350, 20), (650, 24), (900, 18)]):
            offset = 180
            d.polygon(
                [
                    (0, y_off), (W, y_off - offset),
                    (W, y_off - offset + 70), (0, y_off + 70),
                ],
                fill=(0, 0, 0, alpha),
            )
        layer = layer.filter(ImageFilter.GaussianBlur(12))
        card.alpha_composite(layer)

    # ── sanguine_halo — crimson/gold arc above avatar ─────────────────────
    elif relic_id == "sanguine_halo":
        cx = AV_X + AV_SZ // 2
        cy = AV_Y + 8

        # Glow halo
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = ImageDraw.Draw(layer)
        gold  = theme["gold"][:3]
        acc   = theme["accent"][:3]
        rx, ry = 60, 18
        for expand in range(0, 10, 2):
            d.arc(
                [(cx - rx - expand, cy - ry - 30 - expand),
                 (cx + rx + expand, cy - ry - 30 + ry * 2 + expand)],
                start=200, end=340, fill=(*gold, max(0, 80 - expand * 8)), width=2,
            )
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        card.alpha_composite(layer)

        # Sharp halo arc
        d2 = ImageDraw.Draw(card)
        d2.arc(
            [(cx - rx, cy - ry - 30), (cx + rx, cy - ry - 30 + ry * 2)],
            start=200, end=340, fill=(*gold, 220), width=3,
        )
        d2.arc(
            [(cx - rx + 3, cy - ry - 27), (cx + rx - 3, cy - ry - 27 + ry * 2 - 6)],
            start=205, end=335, fill=(*acc, 100), width=1,
        )


# ─── Rank evolution ───────────────────────────────────────────────────────────

# (rank_idx_threshold, aura_rgb, border_alpha, glow_blur, frame_width, corner_alpha)
_RANK_EVOLUTION: List[Tuple] = [
    (0,  (80,  0,   0),   0,   0,  0, 0),   # Forsaken — no aura
    (1,  (90,  10,  0),   0,   0,  0, 0),   # Vermin — no aura
    (2,  (115, 0,   0),   38,  6,  1, 6),   # Corrupted
    (3,  (135, 12,  0),   48,  7,  1, 10),  # Folklore
    (4,  (158, 18,  0),   58,  9,  2, 14),  # Mythology
    (5,  (178, 24,  0),   68,  11, 2, 18),  # Demonology
    (6,  (198, 34,  0),   78,  13, 2, 22),  # Eschatology
    (7,  (218, 50,  5),   88,  15, 2, 27),  # Archangel
    (8,  (235, 65,  8),   98,  17, 3, 32),  # Archdemon
    (9,  (205, 168, 22),  108, 18, 3, 36),  # Knight
    (10, (210, 176, 27),  113, 19, 3, 39),  # Baron
    (11, (215, 182, 32),  118, 20, 3, 41),  # Viscount
    (12, (218, 188, 37),  123, 21, 4, 43),  # Count
    (13, (222, 193, 41),  128, 22, 4, 46),  # Marquis
    (14, (226, 200, 46),  133, 23, 4, 49),  # Duke
    (15, (180, 182, 228), 124, 21, 4, 46),  # Legionnaires
    (16, (190, 192, 236), 134, 22, 4, 49),  # Centurion
    (17, (200, 202, 244), 144, 23, 4, 52),  # Legates
    (18, (210, 212, 255), 154, 25, 5, 56),  # Chancellor
    (19, (248, 215, 52),  158, 26, 5, 62),  # Princesses/Princes
    (20, (255, 218, 56),  166, 27, 5, 66),  # Consorts
    (21, (255, 225, 62),  178, 29, 6, 76),  # Sovereign
]

_RARITY_BADGE_COLOR = {
    "Common":    (148, 102, 102),
    "Uncommon":  (90,  158,  82),
    "Rare":      (62,  108, 200),
    "Epic":      (145,  58, 202),
    "Legendary": (215, 168,  42),
    "Mythic":    (210,  22,  22),
}


def _rank_level_from_name(rank: str) -> int:
    return RANK_ORDER.get(rank, 0)


def _rank_evolution_frame(card: Image.Image, rank_level: int, theme: dict):
    """Apply evolving rank aura border — intensifies with rank."""
    if rank_level < 2:
        return
    tier = _RANK_EVOLUTION[min(rank_level, len(_RANK_EVOLUTION) - 1)]
    color, border_a, blur, fw, corners = tier[1], tier[2], tier[3], tier[4], tier[5]
    if border_a == 0:
        return

    # Blurred outer aura
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                         radius=RADIUS, outline=(*color, border_a), width=fw + 3)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    card.alpha_composite(layer)

    # Sharp inner ring
    d2 = ImageDraw.Draw(card)
    d2.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                          radius=RADIUS, outline=(*color, min(255, border_a + 55)), width=fw)

    # Corner glow spots for mid-to-high ranks
    if corners > 0:
        for cx, cy in [(0, 0), (W, 0), (0, H), (W, H)]:
            cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(cl).ellipse([(cx - 90, cy - 90), (cx + 90, cy + 90)],
                                        fill=(*color, corners))
            cl = cl.filter(ImageFilter.GaussianBlur(38))
            card.alpha_composite(cl)


def _kingdom1_aura(card: Image.Image, theme: dict):
    """Exclusive supreme aura for the current #1 ranked soul."""
    gold = (255, 210, 0)

    # Crown diamond at top-centre
    cx = W // 2
    dy = 5
    for pts, a, b in [
        ([(cx, dy - 18), (cx + 14, dy - 6), (cx, dy + 6), (cx - 14, dy - 6)], 90, 6),
        ([(cx, dy - 14), (cx + 10, dy - 5), (cx, dy + 4), (cx - 10, dy - 5)], 220, 2),
    ]:
        dlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(dlay).polygon(pts, fill=(*gold, a))
        dlay = dlay.filter(ImageFilter.GaussianBlur(b))
        card.alpha_composite(dlay)
    ImageDraw.Draw(card).polygon(
        [(cx, dy - 14), (cx + 10, dy - 5), (cx, dy + 4), (cx - 10, dy - 5)],
        fill=(*gold, 225),
    )

    # Top-corner golden light bursts
    for cx, cy in [(0, 0), (W, 0)]:
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(bl).ellipse([(cx - 100, cy - 100), (cx + 100, cy + 100)],
                                    fill=(*gold, 28))
        bl = bl.filter(ImageFilter.GaussianBlur(44))
        card.alpha_composite(bl)

    # Bottom ambient shimmer
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([(W // 2 - 300, H - 60), (W // 2 + 300, H + 100)],
                                fill=(*gold, 18))
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    card.alpha_composite(sh)


def _grain_texture(card: Image.Image, intensity: int = 8):
    """Subtle analog noise grain — makes the card feel textured and alive."""
    rng = _random.Random(17)
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for _ in range(W * H // 10):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        a = rng.randint(0, intensity)
        bright = rng.randint(190, 255)
        nd.point((x, y), fill=(bright, bright, bright, a))
    card.alpha_composite(noise)


def _scanline_illusion(card: Image.Image, alpha: int = 7):
    """Faint horizontal scanlines — simulates screen-rendered depth."""
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for y in range(0, H, 4):
        sd.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    card.alpha_composite(scan)


def _inner_glow_vignette(card: Image.Image, theme: dict, rank_level: int):
    """Soft inner glow from edges — creates depth and warmth."""
    tier = _RANK_EVOLUTION[min(rank_level, len(_RANK_EVOLUTION) - 1)]
    color = tier[1]
    alpha_boost = min(40, 8 + rank_level * 2)

    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    # Inner light source — center top
    for r, a in [(320, alpha_boost), (200, alpha_boost // 2)]:
        vd.ellipse([(W // 2 - r, -r // 2), (W // 2 + r, r // 2 + 20)],
                   fill=(*color, a))
    vig = vig.filter(ImageFilter.GaussianBlur(50))
    card.alpha_composite(vig)


def _render_badges_card(card: Image.Image, badge_ids: List[str],
                         y_start: int, theme: dict):
    """Render badge seals onto the card in the official record zone."""
    valid = [BADGES_CATALOG[b] for b in badge_ids[:3] if b in BADGES_CATALOG]
    if not valid:
        return

    draw = ImageDraw.Draw(card)

    # Section header
    bl_f = _font(9, cinzel=True)
    bl_str = "MARKS  ·  ACTIVE  INSIGNIA"
    bl_w = _tw(draw, bl_str, bl_f)
    draw.text(((W - bl_w) // 2, y_start),
              bl_str, font=bl_f, fill=(*theme["text2"][:3], 148))

    badge_w, badge_h = 166, 40
    n = len(valid)
    total_w = n * badge_w + (n - 1) * 14
    bx0 = (W - total_w) // 2
    by  = y_start + 18

    for badge in valid:
        col = _RARITY_BADGE_COLOR.get(badge.rarity, theme["text2"][:3])

        # Stamp background + outline
        stamp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        sd.rounded_rectangle(
            [(bx0, by), (bx0 + badge_w, by + badge_h)],
            radius=7, outline=(*col, 170), width=1,
            fill=(*theme["bg2"][:3], 100),
        )
        # Subtle glow on stamp
        stamp_glow = stamp.filter(ImageFilter.GaussianBlur(3))
        card.alpha_composite(stamp_glow)
        card.alpha_composite(stamp)
        draw = ImageDraw.Draw(card)

        # Badge name
        bn_f = _font(13, bold=True)
        bn   = badge.name[:16]
        bn_w = _tw(draw, bn, bn_f)
        draw.text((bx0 + (badge_w - bn_w) // 2, by + 5),
                  bn, font=bn_f, fill=(*col, 218))

        # Rarity label
        rar_f = _font(9)
        rar_w = _tw(draw, badge.rarity.upper(), rar_f)
        draw.text((bx0 + (badge_w - rar_w) // 2, by + 24),
                  badge.rarity.upper(), font=rar_f, fill=(*col, 135))

        bx0 += badge_w + 14


def _low_rank_damage(card: Image.Image, rank_level: int, theme: dict):
    """Worn / damaged document overlay for very low ranks (Forsaken / Vermin)."""
    rng = _random.Random(91827)           # deterministic
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    intensity = max(1, 3 - rank_level)   # 3 for level 0, 2 for 1, 1 for 2

    # Scratch lines
    for _ in range(intensity * 9):
        x1 = rng.randint(0, W)
        y1 = rng.randint(0, H)
        x2 = x1 + rng.randint(-80, 80)
        y2 = y1 + rng.randint(-40, 40)
        a  = rng.randint(18, 48)
        d.line([(x1, y1), (x2, y2)], fill=(0, 0, 0, a), width=1)

    # Worn patches
    for _ in range(intensity * 6):
        px = rng.randint(60, W - 60)
        py = rng.randint(120, H - 120)
        pw = rng.randint(20, 90)
        ph = rng.randint(2, 8)
        a  = rng.randint(12, 35)
        d.rectangle([(px, py), (px + pw, py + ph)], fill=(0, 0, 0, a))

    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    card.alpha_composite(layer)


# ─── Infernal Artifact Icon Renderers ─────────────────────────────────────────

def _draw_relic_icon_art(
    card: Image.Image,
    cx: int, cy: int, R: int,
    relic_id: Optional[str],
    theme: dict,
    slot_idx: int,
    uhash: int,
) -> None:
    """Draw a relic visual icon (filled or dark-empty slot) at (cx, cy)."""
    acc = theme["accent"][:3]
    bg2 = theme["bg2"][:3]
    bdr = theme["border"][:3]
    gld = theme.get("gold", acc)[:3]

    if relic_id and relic_id in RELICS_CATALOG:
        # Glow halo behind icon
        gl = Image.new("RGBA", card.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gd.ellipse([cx-R-8, cy-R-8, cx+R+8, cy+R+8], fill=(*acc, 22))
        gl = gl.filter(ImageFilter.GaussianBlur(10))
        card.alpha_composite(gl)

        draw = ImageDraw.Draw(card)

        if relic_id == "soul_aura":
            # GLOWING EYE
            draw.ellipse([cx-R, cy-R, cx+R, cy+R],
                         fill=(*bg2, 185), outline=(*acc, 175), width=2)
            ew, eh = int(R*0.78), int(R*0.38)
            draw.ellipse([cx-ew, cy-eh, cx+ew, cy+eh],
                         fill=(*bg2, 220), outline=(*acc, 195), width=1)
            ir = int(R*0.26)
            draw.ellipse([cx-ir, cy-ir, cx+ir, cy+ir], fill=(*acc, 245))
            pr = int(R*0.10)
            draw.ellipse([cx-pr, cy-pr, cx+pr, cy+pr], fill=(0, 0, 0, 255))
            for adeg in range(0, 360, 60):
                a = math.radians(adeg)
                x0 = cx + math.cos(a)*R*1.05
                y0 = cy + math.sin(a)*R*1.05
                x1 = cx + math.cos(a)*R*1.40
                y1 = cy + math.sin(a)*R*1.40
                draw.line([(int(x0), int(y0)), (int(x1), int(y1))],
                          fill=(*acc, 130), width=1)

        elif relic_id == "infernal_crown":
            # INFERNAL CROWN — 3 prongs + base + gem
            base_y1 = cy + int(R*0.18)
            base_y2 = cy + int(R*0.78)
            draw.rounded_rectangle(
                [cx-int(R*0.78), base_y1, cx+int(R*0.78), base_y2],
                radius=3, fill=(*gld, 200))
            draw.polygon([(cx, cy-int(R*0.88)),
                           (cx-int(R*0.18), base_y1), (cx+int(R*0.18), base_y1)],
                         fill=(*gld, 225))
            draw.polygon([(cx-int(R*0.52), cy-int(R*0.48)),
                           (cx-int(R*0.70), base_y1), (cx-int(R*0.35), base_y1)],
                         fill=(*gld, 205))
            draw.polygon([(cx+int(R*0.52), cy-int(R*0.48)),
                           (cx+int(R*0.35), base_y1), (cx+int(R*0.70), base_y1)],
                         fill=(*gld, 205))
            gr = max(3, int(R*0.10))
            draw.ellipse([cx-gr, cy-int(R*0.88)-gr, cx+gr, cy-int(R*0.88)+gr],
                         fill=(*acc, 255))
            draw.ellipse([cx-R, cy-R, cx+R, cy+R], outline=(*gld, 65), width=1)

        elif relic_id == "void_drift":
            # VORTEX SPIRAL — concentric arcs with rotation offset
            draw.ellipse([cx-R, cy-R, cx+R, cy+R],
                         fill=(*bg2, 160), outline=(*acc, 70), width=1)
            for i in range(5):
                r_ = int(R*(1.0 - i*0.17))
                sa  = i * 72
                draw.arc([cx-r_, cy-r_, cx+r_, cy+r_], sa, sa+270,
                         fill=(*acc, max(45, 205-i*40)), width=max(1, 3-i//2))
            draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=(*acc, 255))

        elif relic_id == "crimson_chains":
            # CHAIN — two interlocked ovals
            draw.ellipse([cx-R, cy-R, cx+R, cy+R],
                         fill=(*bg2, 130), outline=(*acc, 55), width=1)
            la, lb = int(R*0.42), int(R*0.22)
            for ox, oy in [(-int(R*0.24), -int(R*0.18)),
                            (int(R*0.24),   int(R*0.18))]:
                lx, ly = cx+ox, cy+oy
                draw.arc([lx-la, ly-lb, lx+la, ly+lb],  30, 210,
                         fill=(*acc, 205), width=3)
                draw.arc([lx-la, ly-lb, lx+la, ly+lb], 210, 390,
                         fill=(*acc, 95),  width=3)

        elif relic_id == "abyssal_veil":
            # SHROUD TEARDROP
            draw.ellipse([cx-R, cy-R, cx+R, cy+R],
                         fill=(*bg2, 120), outline=(*acc, 55), width=1)
            pts = [(cx,              cy-int(R*0.90)),
                   (cx+int(R*0.64), cy+int(R*0.24)),
                   (cx+int(R*0.50), cy+int(R*0.82)),
                   (cx,              cy+int(R*0.57)),
                   (cx-int(R*0.50), cy+int(R*0.82)),
                   (cx-int(R*0.64), cy+int(R*0.24))]
            draw.polygon(pts, fill=(*acc, 42), outline=(*acc, 165), width=2)
            ipts = [(cx,              cy-int(R*0.56)),
                    (cx+int(R*0.32), cy+int(R*0.14)),
                    (cx,              cy+int(R*0.40)),
                    (cx-int(R*0.32), cy+int(R*0.14))]
            draw.polygon(ipts, fill=(*acc, 135))

        elif relic_id == "sanguine_halo":
            # HALO RING — thick outer + inner ring + gem dots
            draw.ellipse([cx-R, cy-R, cx+R, cy+R], outline=(*gld, 225), width=4)
            r2 = int(R*0.72)
            draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], outline=(*gld, 75), width=1)
            for i in range(6):
                a = math.radians(i*60 - 30)
                gx = int(cx + math.cos(a)*R*0.87)
                gy = int(cy + math.sin(a)*R*0.87)
                draw.ellipse([gx-4, gy-4, gx+4, gy+4],
                             fill=(*gld, 240), outline=(*acc, 195), width=1)

        else:
            # Generic infernal orb
            draw.ellipse([cx-R, cy-R, cx+R, cy+R],
                         fill=(*bg2, 195), outline=(*acc, 200), width=2)
            r2 = int(R*0.55)
            draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2],
                         fill=(*acc, 55), outline=(*acc, 195), width=1)
            draw.ellipse([cx-int(R*0.22), cy-int(R*0.22),
                          cx+int(R*0.22), cy+int(R*0.22)], fill=(*acc, 255))
    else:
        # Empty slot — dark faint circle with subtle unique pattern
        draw = ImageDraw.Draw(card)
        draw.ellipse([cx-R, cy-R, cx+R, cy+R], fill=(*bg2, 28), outline=(*bdr, 42), width=1)
        pat = (uhash + slot_idx * 7919) % 5
        if pat == 0:
            r2 = int(R*0.45)
            draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], outline=(*bdr, 32), width=1)
        elif pat == 1:
            s = int(R*0.38)
            draw.line([cx-s, cy, cx+s, cy], fill=(*bdr, 35), width=1)
            draw.line([cx, cy-s, cx, cy+s], fill=(*bdr, 35), width=1)
        elif pat == 2:
            d_ = int(R*0.40)
            for ddx, ddy in [(d_, 0), (-d_, 0), (0, d_), (0, -d_)]:
                draw.ellipse([cx+ddx-2, cy+ddy-2, cx+ddx+2, cy+ddy+2], fill=(*bdr, 38))
        elif pat == 3:
            r3 = int(R*0.50)
            for sa in [0, 120, 240]:
                draw.arc([cx-r3, cy-r3, cx+r3, cy+r3], sa, sa+72, fill=(*bdr, 38), width=1)
        else:
            draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(*bdr, 38))


def _draw_badge_icon_art(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int, R: int,
    badge,
    theme: dict,
) -> None:
    """Draw a badge seal icon symbol inside the badge circle."""
    col = _RARITY_BADGE_COLOR.get(badge.rarity, theme["text2"][:3])

    if badge.id == "haunted":
        # SKULL — oval head + hollow eyes + nose
        hw, hh = int(R*0.56), int(R*0.52)
        ey = cy - int(R*0.10)
        draw.ellipse([cx-hw, ey-hh, cx+hw, ey],
                     fill=(*col, 48), outline=(*col, 180), width=1)
        draw.ellipse([cx-int(R*0.30), ey-int(R*0.36),
                      cx-int(R*0.08), ey-int(R*0.14)], fill=(*col, 230))
        draw.ellipse([cx+int(R*0.08), ey-int(R*0.36),
                      cx+int(R*0.30), ey-int(R*0.14)], fill=(*col, 230))
        draw.ellipse([cx-int(R*0.08), ey-int(R*0.06),
                      cx+int(R*0.08), ey+int(R*0.10)], fill=(*col, 130))

    elif badge.id == "void_sworn":
        # EYE IN TRIANGLE
        ty = cy - int(R*0.70)
        draw.polygon([(cx, ty), (cx-int(R*0.62), cy+int(R*0.52)),
                       (cx+int(R*0.62), cy+int(R*0.52))],
                     outline=(*col, 185), width=1)
        draw.ellipse([cx-int(R*0.23), cy-int(R*0.20),
                      cx+int(R*0.23), cy+int(R*0.20)], fill=(*col, 200))
        draw.ellipse([cx-int(R*0.09), cy-int(R*0.09),
                      cx+int(R*0.09), cy+int(R*0.09)], fill=(0, 0, 0, 255))

    elif badge.id == "bloodpact":
        # BLOOD DROPLET
        draw.polygon([
            (cx,              cy-int(R*0.78)),
            (cx+int(R*0.52), cy+int(R*0.20)),
            (cx,              cy+int(R*0.68)),
            (cx-int(R*0.52), cy+int(R*0.20)),
        ], fill=(*col, 200), outline=(*col, 220), width=1)

    elif badge.id == "infernal_mark":
        # PENTAGRAM — proper 5-pointed star
        outer, inner_ = [], []
        for i in range(5):
            a_o = math.radians(-90 + i*72)
            a_i = math.radians(-90 + i*72 + 36)
            outer.append((int(cx+math.cos(a_o)*R*0.75),
                           int(cy+math.sin(a_o)*R*0.75)))
            inner_.append((int(cx+math.cos(a_i)*R*0.30),
                            int(cy+math.sin(a_i)*R*0.30)))
        star = []
        for i in range(5):
            star.append(outer[i]); star.append(inner_[i])
        draw.polygon(star, fill=(*col, 195), outline=(*col, 215), width=1)

    elif badge.id == "wraith_touched":
        # GHOST HEAD + EYES
        gw = int(R*0.52)
        draw.ellipse([cx-gw, cy-int(R*0.68), cx+gw, cy+int(R*0.08)],
                     fill=(*col, 50), outline=(*col, 165), width=1)
        draw.ellipse([cx-int(R*0.28), cy-int(R*0.50),
                      cx-int(R*0.08), cy-int(R*0.28)], fill=(*col, 210))
        draw.ellipse([cx+int(R*0.08), cy-int(R*0.50),
                      cx+int(R*0.28), cy-int(R*0.28)], fill=(*col, 210))

    elif badge.id == "cerberus_marked":
        # THREE OVERLAPPING HEAD CIRCLES
        cr = int(R*0.30)
        draw.ellipse([cx-int(R*0.62)-cr, cy-cr, cx-int(R*0.62)+cr, cy+cr],
                     fill=(*col, 40), outline=(*col, 180), width=1)
        draw.ellipse([cx-cr, cy-int(R*0.48)-cr, cx+cr, cy-int(R*0.48)+cr],
                     fill=(*col, 40), outline=(*col, 180), width=1)
        draw.ellipse([cx+int(R*0.62)-cr, cy-cr, cx+int(R*0.62)+cr, cy+cr],
                     fill=(*col, 40), outline=(*col, 180), width=1)

    elif badge.id == "throne_carved":
        # MINI CROWN
        bty, bby = cy+int(R*0.28), cy+int(R*0.75)
        draw.rectangle([cx-int(R*0.65), bty, cx+int(R*0.65), bby], fill=(*col, 165))
        draw.polygon([(cx, cy-int(R*0.78)),
                       (cx-int(R*0.16), bty), (cx+int(R*0.16), bty)], fill=(*col, 210))
        draw.polygon([(cx-int(R*0.48), cy-int(R*0.42)),
                       (cx-int(R*0.62), bty), (cx-int(R*0.30), bty)], fill=(*col, 188))
        draw.polygon([(cx+int(R*0.48), cy-int(R*0.42)),
                       (cx+int(R*0.30), bty), (cx+int(R*0.62), bty)], fill=(*col, 188))

    elif badge.id == "kingdom_ascendant":
        # 5-POINTED STAR (solid)
        outer, inner_ = [], []
        for i in range(5):
            a_o = math.radians(-90 + i*72)
            a_i = math.radians(-90 + i*72 + 36)
            outer.append((int(cx+math.cos(a_o)*R*0.80),
                           int(cy+math.sin(a_o)*R*0.80)))
            inner_.append((int(cx+math.cos(a_i)*R*0.34),
                            int(cy+math.sin(a_i)*R*0.34)))
        star = []
        for i in range(5):
            star.append(outer[i]); star.append(inner_[i])
        draw.polygon(star, fill=(*col, 200), outline=(*col, 220), width=1)

    else:
        # Generic infernal orb fallback
        draw.ellipse([cx-int(R*0.48), cy-int(R*0.48),
                      cx+int(R*0.48), cy+int(R*0.48)],
                     fill=(*col, 115), outline=(*col, 200), width=1)


def generate_card(
    username: str,
    display_name: str,
    equipped_title: str,
    rank: str,
    balance: int,
    kingdom_rank: int,
    taxes_paid: int,
    skin_id: Optional[str],
    avatar_bytes: Optional[bytes],
    footer_flavor: str,
    card_variant: Optional[EffectiveCardVariant] = None,
    relic_id: Optional[str] = None,
    equipped_badges: Optional[List[str]] = None,
) -> io.BytesIO:

    # ── Skin names ──────────────────────────────────────────────────────────
    _SKIN_NAMES = {
        "default":       "STANDARD ISSUE",
        "blood_crown":   "BLOOD CROWN",
        "abyss_smoke":   "ABYSS SMOKE",
        "infernal_gold": "INFERNAL GOLD",
        "royal_dark":    "ROYAL DARK",
        "black_throne":  "BLACK THRONE",
        "crimson_sigil": "CRIMSON SIGIL",
    }

    # ── Classification table ────────────────────────────────────────────────
    _CLASS = [
        "ENTRY-TIER MEMBER",          # 0  Forsaken
        "LOW-TIER MEMBER",            # 1  Vermin
        "LOWER ENTITY",               # 2  Corrupted
        "LOWER ENTITY",               # 3  Folklore
        "LESSER ENTITY",              # 4  Mythology
        "LESSER ENTITY",              # 5  Demonology
        "INFERNAL ENTITY",            # 6  Eschatology
        "INFERNAL ENTITY",            # 7  Archangel
        "HIGH ENTITY",                # 8  Archdemon
        "HIGH ENTITY",                # 9  Knight
        "NOBLE ENTITY",               # 10 Baron
        "NOBLE ENTITY",               # 11 Viscount
        "MILITARY AUTHORITY",         # 12 Count
        "MILITARY AUTHORITY",         # 13 Marquis
        "COUNCIL AUTHORITY",          # 14 Duke
        "COUNCIL AUTHORITY",          # 15 Legionnaires
        "INFERNAL AUTHORITY",         # 16 Centurion
        "INFERNAL AUTHORITY",         # 17 Legates
        "HIGH AUTHORITY",             # 18 Chancellor
        "HIGH AUTHORITY",             # 19 Prince/Princess
        "SUPREME AUTHORITY",          # 20 Consort
        "SOVEREIGN — SUPREME CLASS",  # 21 Sovereign
    ]

    t = _t(skin_id)

    display_role = card_variant.primary_display_role if card_variant else rank
    economy_rank = card_variant.public_rank if card_variant else rank
    rank_level   = _rank_level_from_name(economy_rank)
    is_kingdom1  = (kingdom_rank == 1)
    badges_list  = list(equipped_badges or [])
    dn           = display_name or username

    # ── Classification: prefer variant's group label, fall back to _CLASS ──
    if card_variant and hasattr(card_variant, "classification") and card_variant.classification:
        classification = card_variant.classification
    else:
        classification = _CLASS[min(rank_level, len(_CLASS) - 1)]

    # ── Kingdom rank eligibility ─────────────────────────────────────────────
    # Non-eligible hierarchy groups (Staff, Council, Royal, Owner) show EXEMPT.
    kr_eligible = True
    if card_variant and hasattr(card_variant, "kingdom_rank_eligible"):
        kr_eligible = card_variant.kingdom_rank_eligible

    # Staff/authority hierarchy flag — Owners, Royal Family, Council, Legion.
    # These groups get no relic border effects and a neutral avatar frame.
    is_staff_hierarchy = not kr_eligible

    # Persistent infernal ID (hash of username — deterministic)
    card_id = f"KH-{abs(hash(username)) % 900000 + 100000:06d}"

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = _gradient(W, H, t["bg1"], t["bg2"])

    # Authority emblem watermark (right column background layer)
    _bg_sigil(card, t)

    # Rank-driven ambient vignette

    draw = ImageDraw.Draw(card)

    # ════════════════════════════════════════════════════════════════════════
    # HEADER STRIP  y = 0 – 32
    # ════════════════════════════════════════════════════════════════════════

    hdr_bg  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hdr_d   = ImageDraw.Draw(hdr_bg)
    hdr_col = tuple(max(0, c - 10) for c in t["bg1"][:3])
    hdr_d.rounded_rectangle([(2, 2), (W - 3, HDR_H)],
                              radius=RADIUS - 2, fill=(*hdr_col, 255))
    card.alpha_composite(hdr_bg)
    draw = ImageDraw.Draw(card)

    # Left micro-code
    draw.text((OUT_PAD, 8), "KOH",
              font=_font(11, cinzel=True), fill=(*t["text2"][:3], 110))
    draw.text((OUT_PAD, 24), "SERIES  MMXXV",
              font=_font(8), fill=(*t["text2"][:3], 72))

    # Center — official header text
    hdr1_f = _font(18, cinzel=True)
    hdr1   = "KINGDOM  OF  HELL"
    hdr1_w = _tw(draw, hdr1, hdr1_f)
    _glow(card, ((W - hdr1_w) // 2, 8), hdr1, hdr1_f,
          (*t["text1"][:3], 220), t["glow"], blur=8, spread=2)
    draw = ImageDraw.Draw(card)
    hdr2_f = _font(10, cinzel=True)
    hdr2   = "INFERNAL  IDENTIFICATION  SYSTEM"
    hdr2_w = _tw(draw, hdr2, hdr2_f)
    draw.text(((W - hdr2_w) // 2, 33), hdr2,
              font=hdr2_f, fill=(*t["text2"][:3], 140))

    # Right micro-code
    draw.text((W - OUT_PAD - 96, 8), "INFERNAL  REG.",
              font=_font(8), fill=(*t["text2"][:3], 72))

    # Header bottom double-rule
    draw.line([(OUT_PAD, HDR_H - 8), (W - OUT_PAD, HDR_H - 8)],
              fill=(*t["gold"][:3], 148), width=2)
    draw.line([(OUT_PAD, HDR_H - 3), (W - OUT_PAD, HDR_H - 3)],
              fill=(*t["border"][:3], 52), width=1)

    # ════════════════════════════════════════════════════════════════════════
    # MAIN BODY  y = 32 – 234      3-column fixed grid
    # ────────────────────────────────────────────────────────────────────────
    #  LEFT    x=20–230   w=210  avatar 128×128 + balance
    #  CENTER  x=250–658  w=408  identity record + stats
    #  RIGHT   x=678–880  w=202  authority emblem (bg sigil already drawn)
    # ════════════════════════════════════════════════════════════════════════

    # ── LEFT COLUMN ──────────────────────────────────────────────────────────
    # Avatar — 128×128 with rounded corners (radius=14) and clean thin frame
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")\
                       .resize((AV_SZ, AV_SZ), Image.LANCZOS)
        except Exception:
            av = _placeholder_avatar(AV_SZ, t)
    else:
        av = _placeholder_avatar(AV_SZ, t)
    av_mask = Image.new("L", (AV_SZ, AV_SZ), 0)
    ImageDraw.Draw(av_mask).rounded_rectangle(
        [(0, 0), (AV_SZ - 1, AV_SZ - 1)], radius=AV_RADIUS, fill=255)
    av.putalpha(av_mask)
    card.alpha_composite(av, (AV_X, AV_Y))
    draw = ImageDraw.Draw(card)
    # Inner frame — neutral dark border for staff/authority, skin border for others
    av_frame_col = (60, 20, 20) if is_staff_hierarchy else t["border"][:3]
    draw.rounded_rectangle([(AV_X - 1, AV_Y - 1), (AV_X + AV_SZ, AV_Y + AV_SZ)],
                             radius=AV_RADIUS + 1,
                             outline=(*av_frame_col, 180), width=1)

    # "IDENTIFICATION PHOTO" caption
    cap_f = _font(8, cinzel=True)
    cap   = "IDENTIFICATION  PHOTO"
    cap_w = _tw(draw, cap, cap_f)
    draw.text((AV_X + (AV_SZ - cap_w) // 2, AV_Y + AV_SZ + 6),
              cap, font=cap_f, fill=(*t["text2"][:3], 85))

    # Separator line under caption
    bal_sep_y = AV_Y + AV_SZ + 22
    draw.line([(AV_X + 8, bal_sep_y), (AV_X + AV_SZ - 8, bal_sep_y)],
              fill=(*t["border"][:3], 50), width=1)

    # Balance panel
    bp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bp).rounded_rectangle(
        [(AV_X - 2, bal_sep_y + 4), (AV_X + AV_SZ + 2, MAIN_END - 12)],
        radius=8, fill=(*t["wealth_hl"][:3], 80),
    )
    card.alpha_composite(bp)
    draw = ImageDraw.Draw(card)

    bal_lbl_f = _font(9, cinzel=True)
    bal_lbl   = "BALANCE"
    bal_lbl_w = _tw(draw, bal_lbl, bal_lbl_f)
    draw.text((AV_X + (AV_SZ - bal_lbl_w) // 2, bal_sep_y + 10),
              bal_lbl, font=bal_lbl_f, fill=(*t["text2"][:3], 145))

    # Balance number + coin icon
    bal_str  = _fmt_dc(balance)
    bal_font = _fit_font(draw, bal_str, AV_SZ - 28, 42, 24, bold=True)
    bal_fh   = getattr(bal_font, "size", 36)
    coin_sz  = max(int(bal_fh * 0.82), 24)
    bal_w    = _tw(draw, bal_str, bal_font)
    tot_bal  = bal_w + 6 + coin_sz
    bal_x    = AV_X + (AV_SZ - tot_bal) // 2
    bal_y_p  = bal_sep_y + 28
    _glow(card, (bal_x, bal_y_p), bal_str, bal_font,
          (*t["gold"][:3], 255), t["glow"], blur=18, spread=4)
    _composite_coin(card, bal_x + bal_w + 6,
                    bal_y_p + (bal_fh - coin_sz) // 2, coin_sz)
    draw = ImageDraw.Draw(card)

    # "D E V I L C O I N S" sublabel
    dc_sub   = "D E V I L C O I N S"
    dc_f     = _font(8, cinzel=True)
    dc_w     = _tw(draw, dc_sub, dc_f)
    draw.text((AV_X + (AV_SZ - dc_w) // 2, bal_y_p + bal_fh + 6),
              dc_sub, font=dc_f, fill=(*t["text2"][:3], 80))

    # Left/center vertical rule
    draw.line([(LFT_R + 9, MAIN_Y + 8), (LFT_R + 9, MAIN_END - 8)],
              fill=(*t["border"][:3], 52), width=1)

    # ── CENTER COLUMN ─────────────────────────────────────────────────────────
    flbl    = _font(9, cinzel=True)    # field label
    fx      = CTR_X
    fy      = AV_Y                     # aligned with avatar top
    fw      = CTR_W
    col_mid = fx + fw // 2

    # ── NAME ──
    draw.text((fx, fy), "NAME", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 14
    name_f = _fit_font(draw, dn, fw - 4, 34, 16, bold=True)
    _glow(card, (fx, fy), dn, name_f,
          t["text1"], t["glow"], blur=8, spread=3)
    draw = ImageDraw.Draw(card)
    fy += getattr(name_f, "size", 30) + 8

    # thin rule
    draw.line([(fx, fy), (CTR_R, fy)], fill=(*t["border"][:3], 32), width=1)
    fy += 12

    # ── RANK (left half) | TITLE (right half) ──
    hw = fw // 2 - 8
    draw.text((fx, fy),         "RANK",  font=flbl, fill=(*t["text2"][:3], 108))
    draw.text((col_mid + 6, fy),"TITLE", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 14
    rank_disp = display_role[:18] if display_role else "—"
    _glow(card, (fx, fy), rank_disp, _font(24, bold=True),
          (*t["accent"][:3], 228), t["glow"], blur=8, spread=2)
    draw = ImageDraw.Draw(card)
    has_title  = bool(equipped_title and equipped_title.lower()
                      not in ("unmarked", ""))
    title_disp = equipped_title if has_title else "—"
    title_vf   = _fit_font(draw, title_disp, hw, 20, 12, bold=True)
    draw.text((col_mid + 6, fy + 2), title_disp, font=title_vf,
              fill=(*t["accent"][:3], 208))
    fy += 34

    # thin rule
    draw.line([(fx, fy), (CTR_R, fy)], fill=(*t["border"][:3], 28), width=1)
    fy += 12

    # ── ID NO. (left) | CLASSIFICATION (right) ──
    draw.text((fx, fy),          "ID NO.",         font=flbl, fill=(*t["text2"][:3], 108))
    draw.text((col_mid + 6, fy), "CLASSIFICATION", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 14
    _glow(card, (fx, fy), card_id, _font(16, bold=True),
          (*t["text1"][:3], 210), t["glow"], blur=5, spread=1)
    draw = ImageDraw.Draw(card)
    cls_f = _fit_font(draw, classification, hw, 16, 10, bold=True)
    draw.text((col_mid + 6, fy + 1), classification, font=cls_f,
              fill=(*t["accent"][:3], 200))
    fy += 24

    # ── Data boundary — heavier double rule ──
    draw.line([(fx, fy),     (CTR_R, fy)],     fill=(*t["border"][:3], 80), width=2)
    draw.line([(fx, fy + 5), (CTR_R, fy + 5)], fill=(*t["gold"][:3], 38),   width=1)
    fy += 22

    # ── KINGDOM RANK | TAXES PAID  (stat cols) ──
    stat_lbl_f = _font(9, cinzel=True)
    stat_val_f = _font(32, bold=True)
    sc_left    = fx + fw // 4
    sc_right   = fx + (fw * 3) // 4

    def _stat_cell(cx_: int, label_: str, val_: str,
                   currency_: bool = False, king_: bool = False):
        lw_ = _tw(draw, label_, stat_lbl_f)
        draw.text((cx_ - lw_ // 2, fy), label_,
                  font=stat_lbl_f, fill=(*t["text2"][:3], 130))
        vfh_  = getattr(stat_val_f, "size", 32)
        csz_  = max(int(vfh_ * 0.74), 24)
        vw_   = _tw(draw, val_, stat_val_f)
        tot_  = vw_ + (csz_ + 6 if currency_ else 0)
        tx_   = cx_ - tot_ // 2
        col_  = (*t["accent"][:3], 255) if king_ else (*t["accent"][:3], 218)
        _glow(card, (tx_, fy + 18), val_, stat_val_f, col_, t["glow"],
              blur=14 if king_ else 7, spread=4 if king_ else 2)
        if currency_:
            _composite_coin(card, tx_ + vw_ + 6,
                            fy + 18 + (vfh_ - csz_) // 2, csz_)

    # Kingdom rank cell — exempt groups show official status instead of a number
    if kr_eligible:
        kr_display = f"#{kingdom_rank}"
        kr_king    = is_kingdom1
    else:
        kr_display = "EXEMPT"
        kr_king    = False
    _stat_cell(sc_left,  "KINGDOM  RANK", kr_display, king_=kr_king)
    _stat_cell(sc_right, "TAXES  PAID",   _fmt_dc(taxes_paid), currency_=True)
    draw = ImageDraw.Draw(card)

    # Thin vertical divider between stat cells
    draw.line([(col_mid, fy + 6), (col_mid, fy + 58)],
              fill=(*t["border"][:3], 42), width=1)

    # ── RIGHT COLUMN separator line ────────────────────────────────────────
    draw.line([(CTR_R + 10, MAIN_Y + 12), (CTR_R + 10, MAIN_END - 12)],
              fill=(*t["border"][:3], 40), width=1)

    # ── RIGHT COLUMN label (small, overlaid on sigil area) ─────────────────
    rgt_lbl_f = _font(9, cinzel=True)
    rgt_lbl   = "AUTHORITY  SEAL"
    rgt_lbl_w = _tw(draw, rgt_lbl, rgt_lbl_f)
    draw.text((RGT_X + (RGT_W - rgt_lbl_w) // 2, MAIN_END - 24),
              rgt_lbl, font=rgt_lbl_f, fill=(*t["text2"][:3], 70))

    # Full-width main-body bottom separator
    draw = ImageDraw.Draw(card)
    draw.line([(OUT_PAD, MAIN_END - 2), (W - OUT_PAD, MAIN_END - 2)],
              fill=(*t["border"][:3], 90), width=2)
    draw.line([(OUT_PAD, MAIN_END + 2), (W - OUT_PAD, MAIN_END + 2)],
              fill=(*t["gold"][:3], 32), width=1)

    # ════════════════════════════════════════════════════════════════════════
    # BOUND ARTIFACTS  ART_Y=468 → ARTS_END=628  (160 px)
    # LEFT : RELICS — 4 icon slots (filled or dark-empty)
    # RIGHT: BADGES — 6 circular seal slots (filled or dark-empty)
    # No placeholder text — purely visual
    # ════════════════════════════════════════════════════════════════════════

    draw = ImageDraw.Draw(card)

    # ── Section header — "BOUND ARTIFACTS" centred with diamond dividers ─
    art_lbl_f = _font(9, cinzel=True)
    art_lbl   = "BOUND  ARTIFACTS"
    art_lbl_w = _tw(draw, art_lbl, art_lbl_f)
    art_cx    = W // 2
    draw.text(((W - art_lbl_w) // 2, ART_Y + 6),
              art_lbl, font=art_lbl_f, fill=(*t["text2"][:3], 125))
    draw.line([(OUT_PAD + 24, ART_Y + 18),
               (art_cx - art_lbl_w // 2 - 12, ART_Y + 18)],
              fill=(*t["border"][:3], 40), width=1)
    draw.line([(art_cx + art_lbl_w // 2 + 12, ART_Y + 18),
               (W - OUT_PAD - 24, ART_Y + 18)],
              fill=(*t["border"][:3], 40), width=1)
    draw.polygon([(art_cx, ART_Y + 12), (art_cx + 6, ART_Y + 18),
                  (art_cx, ART_Y + 24), (art_cx - 6, ART_Y + 18)],
                 fill=(*t["accent"][:3], 140))

    # ── Column geometry ──────────────────────────────────────────────────
    content_y = ART_Y + 30
    content_h = ARTS_END - content_y - 6
    COL_DIV   = W // 2              # x = 600
    L_X1      = OUT_PAD             # 24
    L_X2      = COL_DIV - 10        # 590
    R_X1      = COL_DIV + 10        # 610
    R_X2      = W - OUT_PAD         # 1176

    # Vertical divider
    draw.line([(COL_DIV, content_y + 4), (COL_DIV, ARTS_END - 8)],
              fill=(*t["border"][:3], 35), width=1)

    # Sub-labels (9 px Cinzel, very dim)
    sub_f     = _font(9, cinzel=True)
    draw.text((L_X1, content_y + 2), "RELICS",
              font=sub_f, fill=(*t["text2"][:3], 90))
    bsw = _tw(draw, "BADGES", sub_f)
    draw.text((R_X2 - bsw, content_y + 2), "BADGES",
              font=sub_f, fill=(*t["text2"][:3], 90))

    # Vertical centre for all icons in this zone
    uhash    = abs(hash(username))
    icon_cy  = content_y + 18 + (content_h - 20) // 2

    # ════════════════════════════════════════════════════════════════════════
    # LEFT — RELICS  (4 evenly distributed icon slots)
    # Slot 0 = equipped relic; slots 1-3 = dark empty
    # ════════════════════════════════════════════════════════════════════════
    RELIC_R    = 28
    RELIC_SLOTS = 4
    lw         = L_X2 - L_X1       # 566 px
    for i in range(RELIC_SLOTS):
        icx = L_X1 + int(lw * (i + 0.5) / RELIC_SLOTS)
        rid = relic_id if i == 0 else None
        _draw_relic_icon_art(card, icx, icon_cy, RELIC_R, rid, t, i, uhash)

    # ════════════════════════════════════════════════════════════════════════
    # RIGHT — BADGES  (6 evenly distributed circular seal slots)
    # ════════════════════════════════════════════════════════════════════════
    BADGE_R    = 22
    BADGE_SLOTS = 6
    rw         = R_X2 - R_X1       # 566 px
    valid_badges = [BADGES_CATALOG[b] for b in badges_list[:BADGE_SLOTS]
                    if b in BADGES_CATALOG]

    for i in range(BADGE_SLOTS):
        bcx   = R_X1 + int(rw * (i + 0.5) / BADGE_SLOTS)
        badge = valid_badges[i] if i < len(valid_badges) else None

        if badge:
            col = _RARITY_BADGE_COLOR.get(badge.rarity, t["text2"][:3])
            # Subtle glow behind badge
            gl  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gld = ImageDraw.Draw(gl)
            gld.ellipse([bcx-BADGE_R-5, icon_cy-BADGE_R-5,
                          bcx+BADGE_R+5, icon_cy+BADGE_R+5], fill=(*col, 20))
            gl = gl.filter(ImageFilter.GaussianBlur(5))
            card.alpha_composite(gl)
            d2 = ImageDraw.Draw(card)
            # Badge circle frame
            d2.ellipse([bcx-BADGE_R, icon_cy-BADGE_R,
                         bcx+BADGE_R, icon_cy+BADGE_R],
                        fill=(*t["bg2"][:3], 190), outline=(*col, 195), width=2)
            # Icon inside the circle
            _draw_badge_icon_art(d2, bcx, icon_cy, BADGE_R, badge, t)
        else:
            # Dark empty slot — faint circle only, NO text
            d2  = ImageDraw.Draw(card)
            d2.ellipse([bcx-BADGE_R, icon_cy-BADGE_R,
                         bcx+BADGE_R, icon_cy+BADGE_R],
                        fill=(*t["bg2"][:3], 20), outline=(*t["border"][:3], 36), width=1)
            # Subtle inner ring variation keyed to position + username
            if (uhash + i * 6271) % 2 == 0:
                rr = int(BADGE_R*0.52)
                d2.ellipse([bcx-rr, icon_cy-rr, bcx+rr, icon_cy+rr],
                            outline=(*t["border"][:3], 25), width=1)

    # ── Bottom separator ──────────────────────────────────────────────────
    draw = ImageDraw.Draw(card)
    draw.line([(OUT_PAD, ARTS_END - 1), (W - OUT_PAD, ARTS_END - 1)],
              fill=(*t["border"][:3], 60), width=1)

    # ════════════════════════════════════════════════════════════════════════
    # FOOTER  y = 678 – 720
    # ════════════════════════════════════════════════════════════════════════

    draw = ImageDraw.Draw(card)

    # Top rule
    draw.line([(OUT_PAD, FOOTER_Y - 2), (W - OUT_PAD, FOOTER_Y - 2)],
              fill=(*t["border"][:3], 38), width=1)

    # Three centred footer lines
    ft1_f = _font(11, cinzel=True)
    ft1   = "Registered in the Infernal Archives."
    ft1_w = _tw(draw, ft1, ft1_f)
    draw.text(((W - ft1_w) // 2, FOOTER_Y + 4),
              ft1, font=ft1_f, fill=(*t["text2"][:3], 135))

    ft2_f = _font(10)
    ft2   = "The Abyss remembers your name."
    ft2_w = _tw(draw, ft2, ft2_f)
    draw.text(((W - ft2_w) // 2, FOOTER_Y + 20),
              ft2, font=ft2_f, fill=(*t["text2"][:3], 100))

    ft3_f = _font(9)
    ft3   = f"\u201cThe Abyss remembers your name.\u201d"
    ft3_w = _tw(draw, ft3, ft3_f)
    draw.text(((W - ft3_w) // 2, FOOTER_Y + 34),
              ft3, font=ft3_f, fill=(*t["text2"][:3], 72))

    mc_f  = _font(8)
    mc    = f"ID: {card_id}  ·  SERIES MMXXV  ·  KINGDOM OF HELL  ·  INFERNAL REGISTRY"
    mc_w  = _tw(draw, mc, mc_f)
    draw.text(((W - mc_w) // 2, FOOTER_Y + 50),
              mc, font=mc_f, fill=(*t["text2"][:3], 52))

    # ── Post-processing (applied in order over the full canvas) ──────────────
    # Staff/authority hierarchy (Owners, Royal Family, Council, Legion) never
    # get relic border/aura effects — no gold or accent borders on their cards.
    if not is_staff_hierarchy:
        _apply_relic_effect(card, relic_id, t)

    # Subtle paper/document grain (less aggressive than old fantasy card)
    _grain_texture(card, intensity=min(7, 3 + rank_level // 6))
    _scanline_illusion(card, alpha=4)

    # Damage/worn overlay for very low ranks
    if rank_level <= 2:
        _low_rank_damage(card, rank_level, t)


    # ── Apply rounded clip mask ──────────────────────────────────────────────
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
