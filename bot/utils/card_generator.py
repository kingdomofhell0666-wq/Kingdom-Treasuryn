"""
Kingdom Treasury — Infernal Identity Card Generator
900 × 1100 px  |  Vertical AAA Layout  |  Pillow
Zones: Header · Identity · Wealth · Stats · Badges · Audit · Footer
"""

import io
import math
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Asset paths ──────────────────────────────────────────────────────────────
_CINZEL = "bot/assets/fonts/Cinzel.ttf"
_DEJA_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJA_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Card geometry ────────────────────────────────────────────────────────────
W, H     = 900, 1100
RADIUS   = 26
PAD      = 18           # tight — content dominates the surface

# ── Zone boundaries (y) ──────────────────────────────────────────────────────
HEADER_H  = 50

DIV1      = 50
ID_Y      = 56
AV_SZ     = 206          # large avatar
AV_X      = PAD
AV_Y      = ID_Y + 10

DIV2      = 278
WEALTH_Y  = 284
DIV3      = 508
STATS_Y   = 514
DIV4      = 656
BADGE_Y   = 662
DIV5      = 832
AUDIT_Y   = 838
DIV6      = 1008
FOOTER_Y  = 1014

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


# ─── Badge registry ───────────────────────────────────────────────────────────
BADGE_REGISTRY = {
    "duel_champion":   ("Duel\nChampion",   "swords",  (205, 42, 42)),
    "high_roller":     ("High\nRoller",     "coin",    (215, 172, 42)),
    "mine_veteran":    ("Mine\nVeteran",    "pick",    (130, 90, 65)),
    "treasury_patron": ("Treasury\nPatron", "shield",  (52, 132, 215)),
    "abyss_loyalist":  ("Abyss\nLoyalist",  "eye",     (118, 42, 215)),
    "branded_soul":    ("Branded\nSoul",    "flame",   (225, 68, 0)),
    "cerberus_guard":  ("Cerberus\nGuard",  "paw",     (148, 148, 155)),
    "void_walker":     ("Void\nWalker",     "star",    (38, 38, 78)),
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


# ─── Background sigil ─────────────────────────────────────────────────────────

def _bg_sigil(card: Image.Image, theme: dict):
    cx, cy, r = 690, 555, 230

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


# ─── Badge icon drawing ───────────────────────────────────────────────────────

def _draw_badge_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, symbol: str, col: tuple):
    """Draw a small geometric icon centered at (cx, cy) in a ~36px bounding box."""
    r = 18
    c = (*col[:3], 220)
    co = (*col[:3], 160)

    if symbol == "swords":
        for ang in [45, -45]:
            rad = math.radians(ang)
            x1 = cx - r * math.cos(rad)
            y1 = cy + r * math.sin(rad)
            x2 = cx + r * math.cos(rad)
            y2 = cy - r * math.sin(rad)
            draw.line([(x1, y1), (x2, y2)], fill=c, width=3)
        draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=c)

    elif symbol == "coin":
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=c, width=2)
        draw.ellipse([(cx - r + 4, cy - r + 4), (cx + r - 4, cy + r - 4)], outline=co, width=1)
        sf = ImageFont.truetype(_DEJA_B, 18) if True else None
        try:
            sf = ImageFont.truetype(_DEJA_B, 18)
            draw.text((cx - 6, cy - 11), "D", font=sf, fill=c)
        except Exception:
            pass

    elif symbol == "pick":
        # pickaxe: angled line with head
        draw.line([(cx - r, cy + r - 2), (cx + r - 2, cy - r)], fill=c, width=3)
        draw.polygon([(cx + r - 2, cy - r), (cx + r - 8, cy - r + 8),
                      (cx + r + 6, cy - r - 4)], fill=c)

    elif symbol == "shield":
        pts = [
            (cx, cy - r), (cx + r, cy - r // 2),
            (cx + r, cy + 2), (cx, cy + r),
            (cx - r, cy + 2), (cx - r, cy - r // 2),
        ]
        draw.polygon(pts, outline=c, width=2)
        draw.line([(cx, cy - r + 4), (cx, cy + r - 6)], fill=co, width=1)
        draw.line([(cx - r + 4, cy - 2), (cx + r - 4, cy - 2)], fill=co, width=1)

    elif symbol == "eye":
        # almond
        pts_top = [(cx + r * math.cos(math.pi - math.pi * i / 8),
                    cy - r * 0.45 * math.sin(math.pi * i / 8)) for i in range(9)]
        pts_bot = [(cx + r * math.cos(math.pi * i / 8),
                    cy + r * 0.45 * math.sin(math.pi * i / 8)) for i in range(9)]
        draw.polygon(pts_top + pts_bot, outline=c, width=2)
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=c)

    elif symbol == "flame":
        pts = [
            (cx, cy - r),
            (cx + 10, cy - 6),
            (cx + 8, cy + 4),
            (cx + 14, cy - 2),
            (cx + 6, cy + r),
            (cx, cy + r - 4),
            (cx - 6, cy + r),
            (cx - 14, cy - 2),
            (cx - 8, cy + 4),
            (cx - 10, cy - 6),
        ]
        draw.polygon(pts, outline=c, width=2)
        draw.ellipse([(cx - 5, cy + 4), (cx + 5, cy + 14)], fill=c)

    elif symbol == "paw":
        draw.ellipse([(cx - 9, cy), (cx + 9, cy + 16)], fill=c)
        for ox, oy in [(-14, -4), (-6, -12), (6, -12), (14, -4)]:
            draw.ellipse([(cx + ox - 5, cy + oy - 5), (cx + ox + 5, cy + oy + 5)], fill=c)

    elif symbol == "star":
        pts = []
        for i in range(10):
            ang = math.pi * i / 5 - math.pi / 2
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        draw.polygon(pts, fill=c)


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

def _fmt_dc(n: int) -> str:
    return f"{n:,} DC"


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
    badges: Optional[List[str]] = None,
    audit_state: str = "neutral",          # "flagged" | "cleared" | "neutral"
) -> io.BytesIO:

    t = _t(skin_id)
    badges = badges or []

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = _gradient(W, H, t["bg1"], t["bg2"])

    # ── Background sigil (behind everything) ──────────────────────────────
    _bg_sigil(card, t)

    # ── Wealth zone highlight ──────────────────────────────────────────────
    _wealth_highlight(card, t)

    draw = ImageDraw.Draw(card)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 1 — HEADER
    # ────────────────────────────────────────────────────────────────────────

    # Card borders
    draw.rounded_rectangle([(1, 1), (W - 2, H - 2)],
                            radius=RADIUS, outline=(*t["border"][:3], 220), width=2)
    draw.rounded_rectangle([(5, 5), (W - 6, H - 6)],
                            radius=RADIUS - 3, outline=(*t["border"][:3], 45), width=1)

    # Header center text
    hf = _font(10, cinzel=True)
    htxt = "KINGDOM  OF  HELL    ·    INFERNAL  IDENTITY  CARD"
    draw.text(((W - _tw(draw, htxt, hf)) // 2, 14), htxt,
              font=hf, fill=(*t["text2"][:3], 155))

    # Kingdom Rank badge — top right (larger, dominant)
    kr_str = f"#{kingdom_rank}"
    krf = _font(36, bold=True, cinzel=True)
    krw = _tw(draw, kr_str, krf)
    _glow(card, (W - PAD - krw, 6), kr_str, krf,
          (*t["gold"][:3], 252), t["glow"], blur=16, spread=4)
    draw = ImageDraw.Draw(card)
    krl = _font(9, cinzel=True)
    krlw = _tw(draw, "KINGDOM RANK", krl)
    draw.text((W - PAD - krlw, 44), "KINGDOM RANK",
              font=krl, fill=(*t["text2"][:3], 140))

    _double_line(draw, DIV1, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 2 — IDENTITY
    # ────────────────────────────────────────────────────────────────────────

    _paste_avatar(card, avatar_bytes, t)
    draw = ImageDraw.Draw(card)

    # Display name — dominant
    name_x = AV_X + AV_SZ + 22
    max_name_w = W - name_x - PAD - 50

    dn = display_name or username
    name_font = _fit_font(draw, dn, max_name_w, 64, 28, bold=True)
    name_y = AV_Y + 6
    _glow(card, (name_x, name_y), dn, name_font,
          t["text1"], t["glow"], blur=10, spread=3)
    draw = ImageDraw.Draw(card)

    # Secondary line: Rank — Title
    has_title = equipped_title and equipped_title.lower() not in ("unmarked", "")
    title_text = equipped_title if has_title else "Kingdom of Hell"
    rp_font = _font(19, bold=True)
    sec_font = _font(19)
    name_h = getattr(name_font, "size", 52)
    sec_y = name_y + name_h + 6
    rank_part = f"{rank}  —  "
    rpw = _tw(draw, rank_part, rp_font)
    _glow(card, (name_x, sec_y), rank_part, rp_font,
          (*t["gold"][:3], 236), t["glow"], blur=5, spread=1)
    draw = ImageDraw.Draw(card)
    draw.text((name_x + rpw, sec_y), title_text,
              font=sec_font, fill=(*t["accent"][:3], 220))

    # Tax bracket tag
    RANK_TAX = {
        "Forsaken": 0.12, "Condemned": 0.09, "Hellbound": 0.06,
        "Archdemon": 0.03, "Duke": 0.01, "Chancellor": 0.00,
    }
    tax_rate = RANK_TAX.get(rank, 0.12)
    tax_str = "TAX EXEMPT" if tax_rate == 0 else f"TAX BRACKET  {int(tax_rate * 100)}%"
    tbf = _font(12)
    draw.text((name_x, sec_y + 26), tax_str,
              font=tbf, fill=(*t["text2"][:3], 158))

    # Username (subtle)
    if username and username.lower() != dn.lower():
        unf = _font(11)
        draw.text((name_x, sec_y + 46), f"@{username}",
                  font=unf, fill=(*t["text2"][:3], 105))

    _double_line(draw, DIV2, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 3 — WEALTH (DOMINANT)
    # ────────────────────────────────────────────────────────────────────────

    wlf = _font(13, cinzel=True)
    wlw = _tw(draw, "WEALTH", wlf)
    draw.text(((W - wlw) // 2, WEALTH_Y + 10), "WEALTH",
              font=wlf, fill=(*t["text2"][:3], 180))

    bal_str = _fmt_dc(balance)
    bal_font = _fit_font(draw, bal_str, W - 60, 92, 50, bold=True)
    bal_w = _tw(draw, bal_str, bal_font)
    bal_y = WEALTH_Y + 30
    _glow(card, ((W - bal_w) // 2, bal_y), bal_str, bal_font,
          (*t["gold"][:3], 255), t["glow"], blur=24, spread=6)
    draw = ImageDraw.Draw(card)

    bal_h = getattr(bal_font, "size", 82)
    accent_y = bal_y + bal_h + 14
    draw.line([(W // 5, accent_y), (2 * W // 5, accent_y)],
              fill=(*t["border"][:3], 60), width=1)
    draw.line([(3 * W // 5, accent_y), (4 * W // 5, accent_y)],
              fill=(*t["border"][:3], 60), width=1)
    dc_lbl = "D  E  V  I  L  C  O  I  N  S"
    dc_f = _font(10, cinzel=True)
    dc_w = _tw(draw, dc_lbl, dc_f)
    draw.text(((W - dc_w) // 2, accent_y - 4), dc_lbl,
              font=dc_f, fill=(*t["text2"][:3], 118))

    _double_line(draw, DIV3, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 4 — STATS
    # ────────────────────────────────────────────────────────────────────────

    lbl_f = _font(11, cinzel=True)
    val_f  = _font(28, bold=True)
    val_f2 = _font(18, bold=True)

    cols = [W // 6, W // 2, 5 * W // 6]

    def _stat(cx_: int, label: str, value: str, large: bool = True):
        lw_ = _tw(draw, label, lbl_f)
        draw.text((cx_ - lw_ // 2, STATS_Y + 6), label,
                  font=lbl_f, fill=(*t["text2"][:3], 178))
        vf = val_f if large else val_f2
        vw_ = _tw(draw, value, vf)
        _glow(card, (cx_ - vw_ // 2, STATS_Y + 26), value, vf,
              (*t["accent"][:3], 232), t["glow"], blur=7, spread=2)

    _stat(cols[0], "KINGDOM RANK", f"#{kingdom_rank}")
    _stat(cols[1], "TAXES FILED", _fmt_dc(taxes_paid))
    rs_col_str = f"{risk_score} / 100"
    _stat(cols[2], "RISK SCORE", rs_col_str, large=False)
    draw = ImageDraw.Draw(card)

    # Risk score mini-bar
    _risk_bar(draw, risk_score, t, STATS_Y + 108)

    _double_line(draw, DIV4, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 5 — BADGES
    # ────────────────────────────────────────────────────────────────────────

    badge_section_y = BADGE_Y
    blbl_f = _font(11, cinzel=True)
    blw = _tw(draw, "EARNED COMMENDATIONS", blbl_f)
    draw.text(((W - blw) // 2, badge_section_y + 6), "EARNED COMMENDATIONS",
              font=blbl_f, fill=(*t["text2"][:3], 160))

    badge_icon_y = badge_section_y + 26

    visible_badges = [b for b in badges if b in BADGE_REGISTRY][:6]

    if visible_badges:
        bsz = 58          # badge square size
        gap = 18 if len(visible_badges) <= 5 else 12
        total_bw = len(visible_badges) * bsz + (len(visible_badges) - 1) * gap
        start_bx = (W - total_bw) // 2

        for i, badge_id in enumerate(visible_badges):
            label_str, symbol, badge_col = BADGE_REGISTRY[badge_id]
            bx = start_bx + i * (bsz + gap)
            by = badge_icon_y

            # Badge background square
            badge_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(badge_bg)
            bd.rounded_rectangle(
                [(bx, by), (bx + bsz, by + bsz)],
                radius=10,
                fill=(*badge_col[:3], 40),
                outline=(*badge_col[:3], 130), width=1
            )
            card.alpha_composite(badge_bg)
            draw = ImageDraw.Draw(card)

            # Badge icon
            _draw_badge_icon(draw, bx + bsz // 2, by + bsz // 2 - 1, symbol, badge_col)

            # Badge label
            name_lines = label_str.split("\n")
            bf = _font(8)
            for li, line in enumerate(name_lines):
                lw_ = _tw(draw, line, bf)
                draw.text((bx + (bsz - lw_) // 2, by + bsz + 4 + li * 11),
                          line, font=bf, fill=(*badge_col[:3], 185))
    else:
        nob_f = _font(12)
        nob = "No commendations on record."
        nob_w = _tw(draw, nob, nob_f)
        draw.text(((W - nob_w) // 2, badge_icon_y + 30), nob,
                  font=nob_f, fill=(*t["text2"][:3], 110))

    _double_line(draw, DIV5, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 6 — CERBERUS AUDIT STATE
    # ────────────────────────────────────────────────────────────────────────

    draw = ImageDraw.Draw(card)
    az = AUDIT_Y
    az_h = DIV6 - az

    if audit_state == "flagged":
        # Red warning overlay
        warn_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        wd = ImageDraw.Draw(warn_layer)
        wd.rounded_rectangle([(PAD, az + 4), (W - PAD, az + az_h - 4)],
                              radius=12, fill=(90, 0, 0, 65))
        card.alpha_composite(warn_layer)
        draw = ImageDraw.Draw(card)

        # Warning triangle (Cerberus)
        tri_cx, tri_cy = 80, az + az_h // 2
        tri_r = 28
        tri_pts = [(tri_cx, tri_cy - tri_r),
                   (tri_cx + tri_r * 0.88, tri_cy + tri_r * 0.5),
                   (tri_cx - tri_r * 0.88, tri_cy + tri_r * 0.5)]
        draw.polygon(tri_pts, outline=(220, 40, 40, 220), width=2)
        # Cerberus triple dot (3 heads)
        for ox in [-8, 0, 8]:
            draw.ellipse([(tri_cx + ox - 3, tri_cy - 6), (tri_cx + ox + 3, tri_cy)],
                          fill=(220, 40, 40, 200))
        draw.line([(tri_cx, tri_cy + 4), (tri_cx, tri_cy + 12)],
                  fill=(220, 40, 40, 220), width=2)

        at_f = _font(18, bold=True)
        at_w = _tw(draw, "CERBERUS AUDIT  —  ACTIVE", at_f)
        _glow(card, ((W - at_w) // 2, az + 12),
              "CERBERUS AUDIT  —  ACTIVE", at_f,
              (225, 42, 42, 245), (180, 0, 0), blur=9, spread=2)
        draw = ImageDraw.Draw(card)

        rs_f = _font(13)
        rs_str = f"Risk Level: {risk_score}/100   ·   Immediate attention required."
        rs_w = _tw(draw, rs_str, rs_f)
        draw.text(((W - rs_w) // 2, az + 40), rs_str,
                  font=rs_f, fill=(208, 140, 140, 205))

        # Red risk bar
        _risk_bar(draw, risk_score, t, az + 68)
        _line(draw, az + 68 + 10 + 14, t, alpha=30)

        warn_f = _font(10)
        wt = "Cerberus is watching. Every DevilCoin is accounted for."
        wtw = _tw(draw, wt, warn_f)
        draw.text(((W - wtw) // 2, az + 104), wt,
                  font=warn_f, fill=(195, 100, 100, 165))

    elif audit_state == "cleared":
        # Gold seal overlay
        seal_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(seal_layer)
        sd.rounded_rectangle([(PAD, az + 4), (W - PAD, az + az_h - 4)],
                              radius=12, fill=(*t["gold"][:3], 20))
        card.alpha_composite(seal_layer)
        draw = ImageDraw.Draw(card)

        # Seal circle (left)
        sc_cx, sc_cy = 78, az + az_h // 2
        draw.ellipse([(sc_cx - 26, sc_cy - 26), (sc_cx + 26, sc_cy + 26)],
                     outline=(*t["gold"][:3], 180), width=2)
        draw.ellipse([(sc_cx - 20, sc_cy - 20), (sc_cx + 20, sc_cy + 20)],
                     outline=(*t["gold"][:3], 100), width=1)
        # Checkmark
        draw.line([(sc_cx - 10, sc_cy + 2), (sc_cx - 3, sc_cy + 10)],
                  fill=(*t["gold"][:3], 210), width=3)
        draw.line([(sc_cx - 3, sc_cy + 10), (sc_cx + 12, sc_cy - 10)],
                  fill=(*t["gold"][:3], 210), width=3)

        clr_f = _font(18, bold=True)
        clr_str = "RECORD VERIFIED  —  CERBERUS CLEARED"
        clr_w = _tw(draw, clr_str, clr_f)
        _glow(card, ((W - clr_w) // 2, az + 12), clr_str, clr_f,
              (*t["gold"][:3], 234), t["glow"], blur=7, spread=1)
        draw = ImageDraw.Draw(card)

        cf2 = _font(13)
        cm = f"Risk Score: {risk_score}/100   ·   Kingdom record in good standing."
        cmw = _tw(draw, cm, cf2)
        draw.text(((W - cmw) // 2, az + 42), cm,
                  font=cf2, fill=(*t["text2"][:3], 175))

        _line(draw, az + 70, t, alpha=35)
        cf3 = _font(10)
        ct = '"Your ledger is clean. The Kingdom acknowledges your compliance."'
        ctw = _tw(draw, ct, cf3)
        draw.text(((W - ctw) // 2, az + 86), ct,
                  font=cf3, fill=(*t["text2"][:3], 140))

    else:
        # Neutral kingdom status
        ns_f = _font(14, cinzel=True)
        ns = "KINGDOM STATUS"
        nsw = _tw(draw, ns, ns_f)
        draw.text(((W - nsw) // 2, az + 16), ns,
                  font=ns_f, fill=(*t["text2"][:3], 155))

        div_cx = W // 2
        draw.line([(div_cx - 80, az + 38), (div_cx - 12, az + 38)],
                  fill=(*t["border"][:3], 60), width=1)
        draw.line([(div_cx + 12, az + 38), (div_cx + 80, az + 38)],
                  fill=(*t["border"][:3], 60), width=1)

        # Small diamond center
        draw.polygon([(div_cx, az + 32), (div_cx + 7, az + 38),
                      (div_cx, az + 44), (div_cx - 7, az + 38)],
                     fill=(*t["accent"][:3], 160))

        st_f = _font(16, bold=True)
        st = "STANDING MEMBER  ·  NO AUDIT PENDING"
        stw = _tw(draw, st, st_f)
        draw.text(((W - stw) // 2, az + 54), st,
                  font=st_f, fill=(*t["accent"][:3], 190))

        sf2 = _font(12)
        sv = "All records nominal. Cerberus rests."
        svw = _tw(draw, sv, sf2)
        draw.text(((W - svw) // 2, az + 82), sv,
                  font=sf2, fill=(*t["text2"][:3], 140))

        # Skin indicator
        skin_names = {
            "default": "Infernal Standard", "blood_crown": "Blood Crown",
            "abyss_smoke": "Abyss Smoke",   "infernal_gold": "Infernal Gold",
            "royal_dark": "Royal Dark",     "black_throne": "Black Throne",
            "crimson_sigil": "Crimson Sigil",
        }
        sk = skin_names.get(skin_id or "default", "Infernal Standard")
        sk_f = _font(9)
        sk_str = f"Active Skin:  {sk}"
        sk_w = _tw(draw, sk_str, sk_f)
        draw.text(((W - sk_w) // 2, az + 108), sk_str,
                  font=sk_f, fill=(*t["text2"][:3], 105))

    _double_line(draw, DIV6, t)

    # ────────────────────────────────────────────────────────────────────────
    # ZONE 7 — FOOTER
    # ────────────────────────────────────────────────────────────────────────

    ff = _font(11)
    fw = _tw(draw, footer_flavor, ff)
    draw.text(((W - fw) // 2, FOOTER_Y + 18), footer_flavor,
              font=ff, fill=(*t["text2"][:3], 152))

    # Card ID / watermark
    wm_f = _font(8)
    wm = f"Kingdom Treasury  ·  ID-{hash(username) % 99999:05d}"
    draw.text((PAD, FOOTER_Y + 44), wm,
              font=wm_f, fill=(*t["text2"][:3], 70))

    skin_wm = f"// {skin_id or 'default'} //"
    sw_w = _tw(draw, skin_wm, wm_f)
    draw.text((W - PAD - sw_w, FOOTER_Y + 44), skin_wm,
              font=wm_f, fill=(*t["text2"][:3], 70))

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
