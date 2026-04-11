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
_CINZEL = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Card geometry — 900×320 compact horizontal ID ───────────────────────────
W, H      = 900, 320
RADIUS    = 24
OUT_PAD   = 20               # outer edge padding
IN_PAD    = 16               # inner content padding

# ── Column grid (3-column fixed layout) ───────────────────────────────────────
# Columns never shift — skins only change colours/textures, never layout.
LFT_X     = OUT_PAD          # 20
LFT_W     = 210
LFT_R     = LFT_X + LFT_W   # 230

CTR_X     = 250              # center col starts (gap of 20 from LFT_R)
CTR_W     = 408
CTR_R     = CTR_X + CTR_W   # 658

RGT_X     = 678              # right col starts
RGT_W     = W - RGT_X - OUT_PAD  # 202
RGT_R     = RGT_X + RGT_W   # 880

# ── Zone boundaries (y) ───────────────────────────────────────────────────────
HEADER_H  = 32               # y =  0 – 32  header strip
HDR_H     = HEADER_H         # alias
MAIN_Y    = 32               # y = 32 – 234 three-column main body
MAIN_END  = 234
ART_Y     = 237              # y = 237 – 277 bound artifacts row
ARTS_END  = 277
BADGE_Y   = 280              # y = 280 – 304 circular seals
FOOTER_Y  = 306              # y = 306 – 320 footer

# ── Avatar fixed position (inside left column) ─────────────────────────────────
AV_X      = LFT_X            # 20
AV_Y      = MAIN_Y + 6      # 38
AV_SZ     = 128
AV_RADIUS = 14               # rounded corners (per spec)

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
        bg1=(14, 0, 0),   bg2=(32, 4, 4),
        border=(165, 0, 0),  accent=(225, 12, 12),
        gold=(225, 162, 28), text1=(248, 218, 218),
        text2=(172, 116, 116), glow=(210, 0, 0),
        wealth_hl=(36, 4, 4),  sigil="crown",
    ),
    "abyss_smoke": dict(
        bg1=(6, 3, 18),   bg2=(16, 7, 38),
        border=(58, 18, 118), accent=(135, 62, 225),
        gold=(168, 128, 255), text1=(212, 202, 242),
        text2=(128, 108, 178), glow=(105, 42, 205),
        wealth_hl=(14, 8, 42),  sigil="eye",
    ),
    "infernal_gold": dict(
        bg1=(14, 9, 0),   bg2=(30, 18, 4),
        border=(158, 118, 0), accent=(205, 162, 0),
        gold=(255, 212, 38), text1=(252, 238, 202),
        text2=(178, 142, 78), glow=(205, 162, 0),
        wealth_hl=(32, 22, 4),  sigil="sun",
    ),
    "royal_dark": dict(
        bg1=(4, 4, 18),   bg2=(8, 8, 36),
        border=(38, 38, 138), accent=(82, 82, 205),
        gold=(202, 182, 255), text1=(222, 222, 255),
        text2=(128, 128, 198), glow=(62, 62, 182),
        wealth_hl=(10, 10, 44),  sigil="fleur",
    ),
    "black_throne": dict(
        bg1=(5, 5, 5),    bg2=(14, 14, 14),
        border=(52, 52, 52),  accent=(138, 138, 138),
        gold=(202, 202, 202), text1=(232, 232, 232),
        text2=(138, 138, 138), glow=(98, 98, 98),
        wealth_hl=(18, 18, 18),  sigil="throne",
    ),
    "crimson_sigil": dict(
        bg1=(12, 2, 2),   bg2=(28, 6, 6),
        border=(175, 32, 32), accent=(212, 42, 42),
        gold=(242, 182, 58), text1=(248, 218, 218),
        text2=(178, 118, 118), glow=(192, 22, 22),
        wealth_hl=(30, 5, 5),  sigil="sigil",
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


# ─── Background sigil ─────────────────────────────────────────────────────────

def _bg_sigil(card: Image.Image, theme: dict):
    # Right column of 900×320 card — authority emblem crest
    # Centre of right col: x≈779, y≈133, constrained radius ≈ 70
    cx, cy, r = 779, 133, 70

    for alpha, blur in [(52, 30), (28, 8)]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        col = (*theme["glow"][:3], alpha)

        stype = theme["sigil"]
        if stype == "star":
            _sig_star(d, cx, cy, r, col)
        elif stype == "crown":
            _sig_crown(d, cx, cy, r, col)
        elif stype == "eye":
            _sig_eye(d, cx, cy, r, col)
        elif stype == "sun":
            _sig_sun(d, cx, cy, r, col)
        elif stype == "fleur":
            _sig_fleur(d, cx, cy, r, col)
        elif stype == "throne":
            _sig_throne(d, cx, cy, r, col)
        elif stype == "sigil":
            _sig_cross(d, cx, cy, r, col)

        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        card.alpha_composite(layer)


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
    # Gold accent frame for high ranks
    if rank_level >= 15:
        gold_a = min(255, 70 + (rank_level - 15) * 16)
        d.rectangle([(x - 7, y - 7), (x + sz + 6, y + sz + 6)],
                    outline=(*theme["gold"][:3], gold_a), width=1)


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

    # Multiple blurred halos radiating outward
    for offset, alpha, blur in [(32, 20, 30), (18, 48, 18), (9, 85, 12), (4, 125, 7)]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle(
            [(offset, offset), (W - 1 - offset, H - 1 - offset)],
            radius=RADIUS + 3, outline=(*gold, alpha), width=5,
        )
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        card.alpha_composite(layer)

    # Sharp crisp gold rings
    d2 = ImageDraw.Draw(card)
    d2.rounded_rectangle([(2, 2), (W - 3, H - 3)], radius=RADIUS,
                          outline=(*gold, 185), width=3)
    d2.rounded_rectangle([(8, 8), (W - 9, H - 9)], radius=RADIUS - 3,
                          outline=(*gold, 55), width=1)

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

    # Faint "CONDEMNED" watermark stamp for rank 0
    if rank_level == 0:
        stamp_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp_layer)
        sf = _font(60, cinzel=True)
        sw = _tw(sd, "CONDEMNED", sf)
        sd.text(((W - sw) // 2, H // 2 - 30), "CONDEMNED",
                font=sf, fill=(180, 0, 0, 22))
        stamp_layer = stamp_layer.rotate(-25, center=(W // 2, H // 2))
        card.alpha_composite(stamp_layer)


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
        "CONDEMNED — LOWEST CLASS",   # 0  Forsaken
        "CONDEMNED — LOWEST CLASS",   # 1  Vermin
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

    # Persistent infernal ID (hash of username — deterministic)
    card_id      = f"KH-{abs(hash(username)) % 900000 + 100000:06d}"
    classification = _CLASS[min(rank_level, len(_CLASS) - 1)]

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = _gradient(W, H, t["bg1"], t["bg2"])

    # Authority emblem watermark (right column background layer)
    _bg_sigil(card, t)

    # Rank-driven ambient vignette
    _inner_glow_vignette(card, t, rank_level)

    draw = ImageDraw.Draw(card)

    # ════════════════════════════════════════════════════════════════════════
    # CARD BORDER — clean official document frame
    # ════════════════════════════════════════════════════════════════════════
    border_a = min(200, 150 + rank_level * 3)
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*t["border"][:3], border_a), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*t["border"][:3], 40), width=1)
    if rank_level >= 16:
        gold_a = min(255, 55 + (rank_level - 16) * 14)
        draw.rounded_rectangle([(9, 9), (W - 10, H - 10)],
                                radius=RADIUS - 6,
                                outline=(*t["gold"][:3], gold_a), width=1)

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
    draw.text((OUT_PAD, 6), "KOH",
              font=_font(9, cinzel=True), fill=(*t["gold"][:3], 162))
    draw.text((OUT_PAD, 18), "TIERED  MEMORY",
              font=_font(6), fill=(*t["text2"][:3], 72))

    # Center — official header text
    hdr1_f = _font(12, cinzel=True)
    hdr1   = "KINGDOM  OF  HELL"
    hdr1_w = _tw(draw, hdr1, hdr1_f)
    _glow(card, ((W - hdr1_w) // 2, 5), hdr1, hdr1_f,
          (*t["gold"][:3], 228), t["glow"], blur=7, spread=2)
    draw = ImageDraw.Draw(card)
    hdr2_f = _font(7, cinzel=True)
    hdr2   = "INFERNAL  IDENTITY  SYSTEM"
    hdr2_w = _tw(draw, hdr2, hdr2_f)
    draw.text(((W - hdr2_w) // 2, 20), hdr2,
              font=hdr2_f, fill=(*t["text2"][:3], 135))

    # Right micro-code
    draw.text((W - OUT_PAD - 75, 6), "INFERNAL  ARC",
              font=_font(6), fill=(*t["text2"][:3], 72))

    # Header bottom rule — gold + border hairline
    draw.line([(OUT_PAD, HDR_H - 5), (W - OUT_PAD, HDR_H - 5)],
              fill=(*t["gold"][:3], 120), width=1)
    draw.line([(OUT_PAD, HDR_H - 2), (W - OUT_PAD, HDR_H - 2)],
              fill=(*t["border"][:3], 48), width=1)

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
    # Inner frame
    draw.rounded_rectangle([(AV_X - 1, AV_Y - 1), (AV_X + AV_SZ, AV_Y + AV_SZ)],
                             radius=AV_RADIUS + 1,
                             outline=(*t["border"][:3], 180), width=1)
    # Outer accent (high rank gets gold tint)
    outer_col = (*t["gold"][:3], 90) if rank_level >= 14 else (*t["border"][:3], 80)
    draw.rounded_rectangle([(AV_X - 4, AV_Y - 4), (AV_X + AV_SZ + 3, AV_Y + AV_SZ + 3)],
                             radius=AV_RADIUS + 4, outline=outer_col, width=1)

    # "IDENTIFICATION PHOTO" caption
    cap_f = _font(6, cinzel=True)
    cap   = "IDENTIFICATION  PHOTO"
    cap_w = _tw(draw, cap, cap_f)
    draw.text((AV_X + (AV_SZ - cap_w) // 2, AV_Y + AV_SZ + 4),
              cap, font=cap_f, fill=(*t["text2"][:3], 85))

    # Separator line under caption
    bal_sep_y = AV_Y + AV_SZ + 16
    draw.line([(AV_X + 6, bal_sep_y), (AV_X + AV_SZ - 6, bal_sep_y)],
              fill=(*t["border"][:3], 50), width=1)

    # Balance panel
    bp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bp).rounded_rectangle(
        [(AV_X - 2, bal_sep_y + 3), (AV_X + AV_SZ + 2, MAIN_END - 8)],
        radius=6, fill=(*t["wealth_hl"][:3], 75),
    )
    card.alpha_composite(bp)
    draw = ImageDraw.Draw(card)

    bal_lbl_f = _font(7, cinzel=True)
    bal_lbl   = "BALANCE"
    bal_lbl_w = _tw(draw, bal_lbl, bal_lbl_f)
    draw.text((AV_X + (AV_SZ - bal_lbl_w) // 2, bal_sep_y + 7),
              bal_lbl, font=bal_lbl_f, fill=(*t["text2"][:3], 138))

    # Balance number + coin icon
    bal_str  = _fmt_dc(balance)
    bal_font = _fit_font(draw, bal_str, AV_SZ - 32, 26, 16, bold=True)
    bal_fh   = getattr(bal_font, "size", 22)
    coin_sz  = max(int(bal_fh * 0.82), 16)
    bal_w    = _tw(draw, bal_str, bal_font)
    tot_bal  = bal_w + 4 + coin_sz
    bal_x    = AV_X + (AV_SZ - tot_bal) // 2
    bal_y_p  = bal_sep_y + 18
    _glow(card, (bal_x, bal_y_p), bal_str, bal_font,
          (*t["gold"][:3], 255), t["glow"], blur=14, spread=3)
    _composite_coin(card, bal_x + bal_w + 4,
                    bal_y_p + (bal_fh - coin_sz) // 2, coin_sz)
    draw = ImageDraw.Draw(card)

    # "D E V I L C O I N S" sublabel
    dc_sub   = "D E V I L C O I N S"
    dc_f     = _font(6, cinzel=True)
    dc_w     = _tw(draw, dc_sub, dc_f)
    draw.text((AV_X + (AV_SZ - dc_w) // 2, bal_y_p + bal_fh + 4),
              dc_sub, font=dc_f, fill=(*t["text2"][:3], 78))

    # Left/center vertical rule
    draw.line([(LFT_R + 9, MAIN_Y + 8), (LFT_R + 9, MAIN_END - 8)],
              fill=(*t["border"][:3], 52), width=1)

    # ── CENTER COLUMN ─────────────────────────────────────────────────────────
    flbl    = _font(7, cinzel=True)    # field label
    fx      = CTR_X
    fy      = AV_Y                     # aligned with avatar top
    fw      = CTR_W                    # 408 px
    col_mid = fx + fw // 2            # mid-point for two-sub-col splits

    # ── NAME ──
    draw.text((fx, fy), "NAME", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 11
    name_f = _fit_font(draw, dn, fw - 4, 22, 12, bold=True)
    _glow(card, (fx, fy), dn, name_f,
          t["text1"], t["glow"], blur=6, spread=2)
    draw = ImageDraw.Draw(card)
    fy += getattr(name_f, "size", 20) + 5

    # thin rule
    draw.line([(fx, fy), (CTR_R, fy)], fill=(*t["border"][:3], 32), width=1)
    fy += 9

    # ── RANK (left half) | TITLE (right half) ──
    hw = fw // 2 - 6
    draw.text((fx, fy),         "RANK",  font=flbl, fill=(*t["text2"][:3], 108))
    draw.text((col_mid + 4, fy),"TITLE", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 11
    rank_disp = display_role[:16] if display_role else "—"
    _glow(card, (fx, fy), rank_disp, _font(16, bold=True),
          (*t["gold"][:3], 228), t["glow"], blur=6, spread=1)
    draw = ImageDraw.Draw(card)
    has_title  = bool(equipped_title and equipped_title.lower()
                      not in ("unmarked", ""))
    title_disp = equipped_title if has_title else "—"
    title_vf   = _fit_font(draw, title_disp, hw, 14, 9, bold=True)
    draw.text((col_mid + 4, fy + 2), title_disp, font=title_vf,
              fill=(*t["accent"][:3], 208))
    fy += 22

    # thin rule
    draw.line([(fx, fy), (CTR_R, fy)], fill=(*t["border"][:3], 28), width=1)
    fy += 9

    # ── ID NO. (left) | CLASSIFICATION (right) ──
    draw.text((fx, fy),          "ID NO.",         font=flbl, fill=(*t["text2"][:3], 108))
    draw.text((col_mid + 4, fy), "CLASSIFICATION", font=flbl, fill=(*t["text2"][:3], 108))
    fy += 11
    _glow(card, (fx, fy), card_id, _font(12, bold=True),
          (*t["gold"][:3], 198), t["glow"], blur=4, spread=1)
    draw = ImageDraw.Draw(card)
    cls_f = _fit_font(draw, classification, hw, 11, 8, bold=True)
    draw.text((col_mid + 4, fy + 1), classification, font=cls_f,
              fill=(*t["accent"][:3], 175))
    fy += 17

    # ── Data boundary — heavier double rule ──
    draw.line([(fx, fy),     (CTR_R, fy)],     fill=(*t["border"][:3], 75), width=2)
    draw.line([(fx, fy + 4), (CTR_R, fy + 4)], fill=(*t["gold"][:3], 30),   width=1)
    fy += 16

    # ── KINGDOM RANK | TAXES PAID  (stat cols) ──
    stat_lbl_f = _font(7, cinzel=True)
    stat_val_f = _font(22, bold=True)
    sc_left    = fx + fw // 4
    sc_right   = fx + (fw * 3) // 4

    def _stat_cell(cx_: int, label_: str, val_: str,
                   currency_: bool = False, king_: bool = False):
        lw_ = _tw(draw, label_, stat_lbl_f)
        draw.text((cx_ - lw_ // 2, fy), label_,
                  font=stat_lbl_f, fill=(*t["text2"][:3], 130))
        vfh_  = getattr(stat_val_f, "size", 22)
        csz_  = max(int(vfh_ * 0.74), 16)
        vw_   = _tw(draw, val_, stat_val_f)
        tot_  = vw_ + (csz_ + 5 if currency_ else 0)
        tx_   = cx_ - tot_ // 2
        col_  = (*t["gold"][:3], 255) if king_ else (*t["accent"][:3], 218)
        _glow(card, (tx_, fy + 12), val_, stat_val_f, col_, t["glow"],
              blur=10 if king_ else 5, spread=3 if king_ else 2)
        if currency_:
            _composite_coin(card, tx_ + vw_ + 5,
                            fy + 12 + (vfh_ - csz_) // 2, csz_)

    _stat_cell(sc_left,  "KINGDOM  RANK", f"#{kingdom_rank}", king_=is_kingdom1)
    _stat_cell(sc_right, "TAXES  PAID",   _fmt_dc(taxes_paid), currency_=True)
    draw = ImageDraw.Draw(card)

    # Thin vertical divider between stat cells
    draw.line([(col_mid, fy + 4), (col_mid, fy + 38)],
              fill=(*t["border"][:3], 38), width=1)

    # ── RIGHT COLUMN separator line ────────────────────────────────────────
    draw.line([(CTR_R + 9, MAIN_Y + 8), (CTR_R + 9, MAIN_END - 8)],
              fill=(*t["border"][:3], 40), width=1)

    # ── RIGHT COLUMN label (small, overlaid on sigil area) ────────────────
    rgt_lbl_f = _font(7, cinzel=True)
    rgt_lbl   = "AUTHORITY  SEAL"
    rgt_lbl_w = _tw(draw, rgt_lbl, rgt_lbl_f)
    draw.text((RGT_X + (RGT_W - rgt_lbl_w) // 2, MAIN_END - 18),
              rgt_lbl, font=rgt_lbl_f, fill=(*t["text2"][:3], 70))

    # Full-width main-body bottom separator
    draw = ImageDraw.Draw(card)
    draw.line([(OUT_PAD, MAIN_END - 2), (W - OUT_PAD, MAIN_END - 2)],
              fill=(*t["border"][:3], 90), width=2)
    draw.line([(OUT_PAD, MAIN_END + 2), (W - OUT_PAD, MAIN_END + 2)],
              fill=(*t["gold"][:3], 32), width=1)

    # ════════════════════════════════════════════════════════════════════════
    # BOUND ARTIFACTS ROW  y = 237 – 277  (full width, 40 px)
    # Compact inline registry: RELIC · SKIN · TITLE (three equal slots)
    # ════════════════════════════════════════════════════════════════════════

    draw = ImageDraw.Draw(card)

    # Artifact names & colours
    relic_name_ = (RELICS_CATALOG[relic_id].name
                   if relic_id and relic_id in RELICS_CATALOG else "UNBOUND")
    relic_col_  = (*t["accent"][:3], 215) if relic_id else (*t["text2"][:3], 62)
    skin_name_  = _SKIN_NAMES.get(skin_id or "default", "STANDARD ISSUE")
    skin_col_   = (*t["gold"][:3], 205) if (skin_id and skin_id != "default") \
                  else (*t["text2"][:3], 85)
    title_name_ = equipped_title if has_title else "UNMARKED"
    title_col_  = (*t["accent"][:3], 205) if has_title else (*t["text2"][:3], 62)

    # Section label
    art_lbl_f = _font(7, cinzel=True)
    art_lbl   = "BOUND  ARTIFACTS"
    art_lbl_w = _tw(draw, art_lbl, art_lbl_f)
    draw.text((OUT_PAD, ART_Y + 4), art_lbl,
              font=art_lbl_f, fill=(*t["text2"][:3], 112))
    draw.line([(OUT_PAD + art_lbl_w + 8, ART_Y + 8),
               (W - OUT_PAD, ART_Y + 8)],
              fill=(*t["border"][:3], 40), width=1)

    # Three horizontal artifact slots
    slot_gap    = 12
    slot_y      = ART_Y + 16
    slot_h      = ARTS_END - slot_y - 4    # ~57 px
    usable_w    = W - OUT_PAD * 2
    slot_w      = (usable_w - slot_gap * 2) // 3
    slot_xs     = [OUT_PAD,
                   OUT_PAD + slot_w + slot_gap,
                   OUT_PAD + (slot_w + slot_gap) * 2]
    slot_data   = [
        ("RELIC",  relic_name_, relic_col_),
        ("SKIN",   skin_name_,  skin_col_),
        ("TITLE",  title_name_, title_col_),
    ]
    slot_lbl_f  = _font(7, cinzel=True)
    slot_val_sz = 13

    for (slot_, val_, vcol_), sx_ in zip(slot_data, slot_xs):
        # Slot background
        sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sp_d = ImageDraw.Draw(sp)
        sp_d.rounded_rectangle(
            [(sx_, slot_y), (sx_ + slot_w - 1, slot_y + slot_h)],
            radius=6, fill=(*t["bg2"][:3], 50),
            outline=(*t["border"][:3], 60), width=1,
        )
        card.alpha_composite(sp)
        d2 = ImageDraw.Draw(card)

        # Left accent stripe
        d2.line([(sx_ + 1, slot_y + 6), (sx_ + 1, slot_y + slot_h - 6)],
                fill=(*vcol_[:3], 148), width=2)

        # Slot label (top-left)
        d2.text((sx_ + 8, slot_y + 5), slot_, font=slot_lbl_f,
                fill=(*t["text2"][:3], 100))

        # Value (auto-sized, centered vertically)
        vv_    = (val_[:18] + "…") if len(val_) > 19 else val_
        vf_    = _fit_font(d2, vv_, slot_w - 14, slot_val_sz, 8, bold=True)
        vw_    = _tw(d2, vv_, vf_)
        vfh_   = getattr(vf_, "size", 12)
        vx_    = sx_ + (slot_w - vw_) // 2
        vy_    = slot_y + (slot_h - vfh_) // 2 + 4
        _glow(card, (vx_, vy_), vv_, vf_,
              vcol_, t["glow"], blur=3, spread=1)

    draw = ImageDraw.Draw(card)

    # Artifacts bottom separator
    draw.line([(OUT_PAD, ARTS_END - 1), (W - OUT_PAD, ARTS_END - 1)],
              fill=(*t["border"][:3], 60), width=1)

    # ════════════════════════════════════════════════════════════════════════
    # CIRCULAR SEALS ROW  y = 280 – 304  (24 px)
    # Circular badge icons — official infernal seals
    # ════════════════════════════════════════════════════════════════════════

    draw = ImageDraw.Draw(card)
    valid_badges = [BADGES_CATALOG[b] for b in badges_list[:3] if b in BADGES_CATALOG]
    SEAL_R  = 11                          # circle radius (22 px diameter)
    SEAL_CY = BADGE_Y + SEAL_R + 1       # vertical centre

    if valid_badges:
        # "SEALS OF RECOGNITION" micro-label left-aligned
        sl_f  = _font(6, cinzel=True)
        sl    = "SEALS  OF  RECOGNITION"
        draw.text((OUT_PAD, BADGE_Y + 1), sl,
                  font=sl_f, fill=(*t["text2"][:3], 90))

        # Position badges right-aligned within the row
        spacing  = SEAL_R * 2 + 8
        n_badges = len(valid_badges)
        total_bw = n_badges * (SEAL_R * 2) + (n_badges - 1) * 8
        bx_start = (W - total_bw) // 2
        seal_x   = bx_start + SEAL_R

        for badge in valid_badges:
            col = _RARITY_BADGE_COLOR.get(badge.rarity, t["text2"][:3])
            # Glow ring
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gld = ImageDraw.Draw(gl)
            gld.ellipse([(seal_x - SEAL_R - 3, SEAL_CY - SEAL_R - 3),
                          (seal_x + SEAL_R + 3, SEAL_CY + SEAL_R + 3)],
                         fill=(*col, 35))
            gl = gl.filter(ImageFilter.GaussianBlur(4))
            card.alpha_composite(gl)
            d2 = ImageDraw.Draw(card)

            # Fill circle
            d2.ellipse([(seal_x - SEAL_R, SEAL_CY - SEAL_R),
                         (seal_x + SEAL_R, SEAL_CY + SEAL_R)],
                        fill=(*t["bg2"][:3], 180),
                        outline=(*col, 200), width=2)

            # Abbreviation inside (first 2 chars, tiny font)
            ab   = badge.name[:2].upper()
            ab_f = _font(7, bold=True)
            ab_w = _tw(d2, ab, ab_f)
            ab_fh = getattr(ab_f, "size", 7)
            d2.text((seal_x - ab_w // 2, SEAL_CY - ab_fh // 2),
                    ab, font=ab_f, fill=(*col, 218))

            # Badge name below the seal
            nm_f  = _font(6)
            nm_w  = _tw(d2, badge.name[:10], nm_f)
            d2.text((seal_x - nm_w // 2, SEAL_CY + SEAL_R + 2),
                    badge.name[:10], font=nm_f,
                    fill=(*col, 140))

            seal_x += spacing
    else:
        nb_f  = _font(8)
        nb    = "No seals of recognition registered."
        nb_w  = _tw(draw, nb, nb_f)
        draw.text(((W - nb_w) // 2, BADGE_Y + 4), nb,
                  font=nb_f, fill=(*t["text2"][:3], 48))

    # ════════════════════════════════════════════════════════════════════════
    # FOOTER  y = 306 – 320
    # ════════════════════════════════════════════════════════════════════════

    draw = ImageDraw.Draw(card)

    # Thin separator
    draw.line([(OUT_PAD, FOOTER_Y - 1), (W - OUT_PAD, FOOTER_Y - 1)],
              fill=(*t["border"][:3], 34), width=1)

    # Single footer inscription + machine code on same line split left/right
    fi_f  = _font(7)
    fi    = "The Abyss remembers your name."
    fi_w  = _tw(draw, fi, fi_f)
    draw.text((OUT_PAD, FOOTER_Y + 3), fi,
              font=fi_f, fill=(*t["text2"][:3], 110))

    mc_f  = _font(6)
    mc    = f"ID: {card_id}  ·  SERIES MMXXV  ·  INFERNAL REGISTRY"
    mc_w  = _tw(draw, mc, mc_f)
    draw.text((W - OUT_PAD - mc_w, FOOTER_Y + 5), mc,
              font=mc_f, fill=(*t["text2"][:3], 60))

    # ── Post-processing (applied in order over the full canvas) ──────────────
    _apply_relic_effect(card, relic_id, t)
    _rank_evolution_frame(card, rank_level, t)

    # Subtle paper/document grain (less aggressive than old fantasy card)
    _grain_texture(card, intensity=min(7, 3 + rank_level // 6))
    _scanline_illusion(card, alpha=4)

    # Damage/worn overlay for very low ranks
    if rank_level <= 2:
        _low_rank_damage(card, rank_level, t)

    # ── Kingdom #1 supreme aura (applied last, above everything) ─────────────
    if is_kingdom1:
        _kingdom1_aura(card, t)

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
