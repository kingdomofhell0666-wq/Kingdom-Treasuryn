"""Generate a compact pixel-art Infernal Mines animation for /grind."""

import io

from PIL import Image, ImageDraw, ImageFont


WIDTH = 384
HEIGHT = 216
FRAME_COUNT = 42
FRAME_DURATION_MS = 160
ANIMATION_DURATION_SECONDS = FRAME_COUNT * FRAME_DURATION_MS / 1000
_PIXEL = 4

_BG_TOP = (14, 11, 22, 255)
_BG_BOTTOM = (37, 18, 25, 255)
_ROCK_DARK = (49, 37, 43, 255)
_ROCK_MID = (75, 49, 48, 255)
_ROCK_LIGHT = (111, 67, 53, 255)
_FIRE = (255, 105, 35, 255)
_DEMON = (180, 43, 43, 255)
_DEMON_DARK = (105, 27, 38, 255)
_HORN = (50, 27, 36, 255)
_GOLD = (255, 194, 48, 255)
_GOLD_LIGHT = (255, 232, 115, 255)


def _pixel_rect(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color):
    left = max(0, (x // _PIXEL) * _PIXEL)
    top = max(0, (y // _PIXEL) * _PIXEL)
    right = min(WIDTH - 1, ((x + w + _PIXEL - 1) // _PIXEL) * _PIXEL - 1)
    bottom = min(HEIGHT - 1, ((y + h + _PIXEL - 1) // _PIXEL) * _PIXEL - 1)
    draw.rectangle(
        (left, top, right, bottom),
        fill=color,
    )


def _background(frame_number: int) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), _BG_TOP)
    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        mix = y / max(1, HEIGHT - 1)
        color = tuple(
            int(_BG_TOP[channel] * (1 - mix) + _BG_BOTTOM[channel] * mix)
            for channel in range(3)
        ) + (255,)
        draw.line((0, y, WIDTH, y), fill=color)

    # Mine mouth and rock face.
    draw.rectangle((238, 58, 383, 179), fill=(8, 7, 13, 255))
    draw.polygon(
        ((222, 178), (223, 99), (243, 68), (272, 57), (316, 66), (336, 96), (337, 179)),
        fill=(8, 7, 13, 255),
    )
    rocks = (
        (244, 52, 39, 18), (282, 60, 43, 15), (325, 54, 38, 18),
        (244, 176, 45, 22), (294, 180, 37, 19), (338, 171, 43, 25),
        (352, 103, 31, 19), (346, 135, 38, 21), (220, 127, 20, 18),
    )
    for index, (x, y, w, h) in enumerate(rocks):
        color = (_ROCK_DARK, _ROCK_MID, _ROCK_LIGHT)[(index + frame_number // 4) % 3]
        draw.rectangle((x, y, x + w, y + h), fill=color)
        draw.line((x + 4, y + 3, x + w - 5, y + 3), fill=(137, 83, 56, 100), width=2)

    # Uneven floor and a few embedded stones.
    draw.rectangle((0, 176, WIDTH, HEIGHT), fill=(35, 24, 34, 255))
    draw.line((0, 176, WIDTH, 176), fill=(108, 54, 46, 255), width=3)
    for x, y, w in ((28, 188, 17), (88, 198, 11), (270, 190, 15), (352, 201, 19)):
        draw.rectangle((x, y, x + w, y + 4), fill=_ROCK_MID)

    # A torch flickers on the cave wall.
    torch_y = 99 + (frame_number % 3) * 2
    draw.rectangle((68, 84, 73, 115), fill=(91, 52, 38, 255))
    draw.polygon(((60, torch_y + 8), (69, torch_y - 8), (78, torch_y + 7)), fill=_FIRE)
    draw.rectangle((67, torch_y - 1, 71, torch_y + 8), fill=_GOLD)
    draw.ellipse((54, torch_y - 9, 84, torch_y + 22), fill=(210, 74, 21, 24))

    return image


def _draw_pickaxe(draw: ImageDraw.ImageDraw, x: int, y: int, phase: int, walking: bool):
    if walking:
        start = (x + 43, y + 39)
        end = (x + 59, y + 13)
    else:
        swing = phase % 4
        start = (x + 42, y + 38)
        end = ((x + 59, y + 12), (x + 62, y + 24), (x + 58, y + 37), (x + 50, y + 45))[swing]
    draw.line((start, end), fill=(113, 68, 43, 255), width=5)
    head_x, head_y = end
    draw.line(
        ((head_x - 9, head_y + 4), (head_x + 7, head_y - 4)),
        fill=(177, 180, 186, 255),
        width=5,
    )
    draw.line(
        ((head_x - 7, head_y + 2), (head_x + 5, head_y - 4)),
        fill=(229, 210, 168, 255),
        width=2,
    )


def _draw_demon(
    image: Image.Image,
    x: int,
    phase: int,
    walking: bool,
    victory: bool,
    net_reward: int,
):
    draw = ImageDraw.Draw(image)
    ground_y = 174
    body_top = ground_y - 60

    # The raised coin is drawn first so the demon's hand can overlap it.
    if victory:
        coin_x = x + 37
        coin_y = body_top - 25
        draw.ellipse((coin_x - 3, coin_y - 3, coin_x + 31, coin_y + 31), fill=(102, 52, 19, 220))
        draw.ellipse((coin_x, coin_y, coin_x + 26, coin_y + 26), fill=_GOLD)
        draw.ellipse((coin_x + 4, coin_y + 3, coin_x + 22, coin_y + 21), fill=_GOLD_LIGHT)
        draw.text((coin_x + 5, coin_y + 7), "DC", fill=(104, 58, 18, 255), font=ImageFont.load_default())

        reward_text = f"+{max(0, int(net_reward)):,} DC"
        reward_font = ImageFont.load_default()
        reward_width = draw.textbbox((0, 0), reward_text, font=reward_font)[2]
        text_x = max(6, min(WIDTH - reward_width - 6, coin_x - (reward_width - 26) // 2))
        draw.rectangle((text_x - 4, coin_y - 20, text_x + reward_width + 4, coin_y - 3), fill=(13, 9, 17, 230))
        draw.text((text_x, coin_y - 19), reward_text, fill=_GOLD_LIGHT, font=reward_font)

    # Tail and sharply outlined horns make the miner read clearly as a demon.
    draw.line(
        ((x + 18, body_top + 41), (x + 5, body_top + 49), (x + 13, body_top + 55)),
        fill=_DEMON_DARK,
        width=6,
    )
    draw.polygon(
        ((x + 13, body_top + 55), (x + 4, body_top + 58), (x + 9, body_top + 49)),
        fill=_DEMON,
    )
    draw.polygon(
        ((x + 19, body_top + 19), (x + 14, body_top - 1), (x + 30, body_top + 10), (x + 31, body_top + 18)),
        fill=_HORN,
    )
    draw.polygon(
        ((x + 40, body_top + 18), (x + 50, body_top - 2), (x + 51, body_top + 18)),
        fill=_HORN,
    )
    _pixel_rect(draw, x + 12, body_top + 17, 8, 10, _DEMON_DARK)
    _pixel_rect(draw, x + 47, body_top + 17, 8, 10, _DEMON_DARK)

    # Face and torso use separate outlines so the eyes stay visible at small size.
    _pixel_rect(draw, x + 15, body_top + 10, 40, 32, _HORN)
    _pixel_rect(draw, x + 19, body_top + 14, 32, 24, _DEMON)
    _pixel_rect(draw, x + 24, body_top + 23, 7, 5, _GOLD_LIGHT)
    _pixel_rect(draw, x + 40, body_top + 23, 7, 5, _GOLD_LIGHT)
    _pixel_rect(draw, x + 27, body_top + 24, 3, 4, (57, 21, 31, 255))
    _pixel_rect(draw, x + 43, body_top + 24, 3, 4, (57, 21, 31, 255))
    _pixel_rect(draw, x + 32, body_top + 33, 12, 3, (57, 21, 31, 255))
    _pixel_rect(draw, x + 17, body_top + 38, 36, 19, _DEMON_DARK)
    _pixel_rect(draw, x + 22, body_top + 40, 26, 13, _DEMON)
    _pixel_rect(draw, x + 18, body_top + 51, 34, 5, (87, 34, 38, 255))

    # Legs shift while walking and brace during the mining/victory poses.
    step = (phase % 2) * 4 if walking else 0
    _pixel_rect(draw, x + 20, body_top + 43, 12, 16 - step, _DEMON_DARK)
    _pixel_rect(draw, x + 36, body_top + 43, 12, 16 + step, _DEMON_DARK)
    _pixel_rect(draw, x + 16, ground_y - 5, 19, 6, (44, 25, 31, 255))
    _pixel_rect(draw, x + 34, ground_y - 5, 20, 6, (44, 25, 31, 255))

    if victory:
        # Upraised arm and fist beneath the coin.
        draw.line((x + 46, body_top + 29, x + 58, body_top + 11), fill=_DEMON, width=9)
        _pixel_rect(draw, x + 54, body_top + 6, 11, 10, _DEMON)
    else:
        _draw_pickaxe(draw, x, body_top + 5, phase, walking)


def generate_mine_animation(net_reward: int) -> io.BytesIO:
    """Return a short looping GIF whose victory frame shows the real net reward."""
    reward = max(0, int(net_reward))
    rgba_frames = []
    for frame_number in range(FRAME_COUNT):
        image = _background(frame_number)
        if frame_number < 12:
            demon_x = 18 + frame_number * 12
            walking = True
            victory = False
        elif frame_number < 36:
            demon_x = 162
            walking = False
            victory = False
        else:
            demon_x = 162
            walking = False
            victory = True

        _draw_demon(
            image,
            demon_x,
            frame_number,
            walking,
            victory,
            reward,
        )

        if 12 <= frame_number < 36:
            draw = ImageDraw.Draw(image)
            impact_x = 242 + (frame_number % 3) * 3
            impact_y = 132 + (frame_number % 2) * 5
            draw.line((impact_x - 9, impact_y, impact_x + 8, impact_y - 6), fill=_GOLD_LIGHT, width=2)
            draw.line((impact_x, impact_y - 11, impact_x + 4, impact_y + 5), fill=(217, 160, 119, 255), width=2)
            if frame_number % 2 == 0:
                draw.rectangle((impact_x + 7, impact_y + 7, impact_x + 11, impact_y + 11), fill=(139, 92, 80, 255))
                draw.rectangle((impact_x - 12, impact_y + 6, impact_x - 8, impact_y + 10), fill=(181, 113, 82, 255))

        rgba_frames.append(image)

    # All GIF frames must share one palette or indexed colors shift between frames.
    palette_source = Image.new("RGB", (WIDTH, HEIGHT * len(rgba_frames)))
    for index, frame in enumerate(rgba_frames):
        palette_source.paste(frame.convert("RGB"), (0, index * HEIGHT))
    palette = palette_source.quantize(colors=128, dither=Image.Dither.NONE)
    frames = [
        frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in rgba_frames
    ]

    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=False,
        disposal=2,
    )
    output.seek(0)
    return output