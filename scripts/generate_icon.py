"""One-off generator for assets/icon.ico. Not part of the app; run manually
when the icon needs to change: python scripts/generate_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

TOP_COLOR = (79, 172, 254)
BOTTOM_COLOR = (21, 101, 192)
GLYPH_COLOR = (255, 255, 255, 235)
BADGE_COLOR = (39, 174, 96, 255)
BADGE_OUTLINE = (255, 255, 255, 255)


def make_gradient_rounded_square() -> Image.Image:
    grad = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(grad)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        r = round(TOP_COLOR[0] + (BOTTOM_COLOR[0] - TOP_COLOR[0]) * t)
        g = round(TOP_COLOR[1] + (BOTTOM_COLOR[1] - TOP_COLOR[1]) * t)
        b = round(TOP_COLOR[2] + (BOTTOM_COLOR[2] - TOP_COLOR[2]) * t)
        draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=112, fill=255)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(grad, (0, 0), mask)
    return canvas


def draw_photo_glyph(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    margin = 128
    fx0, fy0, fx1, fy1 = margin, margin + 6, SIZE - margin, SIZE - margin - 26
    draw.rounded_rectangle([fx0, fy0, fx1, fy1], radius=24, outline=GLYPH_COLOR, width=18)

    width = fx1 - fx0
    height = fy1 - fy0

    sun_cx = fx0 + width * 0.32
    sun_cy = fy0 + height * 0.32
    sun_r = 22
    draw.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r], fill=GLYPH_COLOR)

    base_y = fy1 - 22
    draw.polygon(
        [
            (fx0 + 18, base_y),
            (fx0 + width * 0.46, fy0 + height * 0.32),
            (fx0 + width * 0.64, base_y),
        ],
        fill=GLYPH_COLOR,
    )
    draw.polygon(
        [
            (fx0 + width * 0.40, base_y),
            (fx0 + width * 0.70, fy0 + height * 0.20),
            (fx1 - 18, base_y),
        ],
        fill=GLYPH_COLOR,
    )


def draw_compress_badge(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    badge_r = 100
    cx = SIZE - 148
    cy = SIZE - 148
    draw.ellipse(
        [cx - badge_r, cy - badge_r, cx + badge_r, cy + badge_r],
        fill=BADGE_COLOR,
        outline=BADGE_OUTLINE,
        width=10,
    )
    draw.line([(cx, cy - 48), (cx, cy + 26)], fill=BADGE_OUTLINE, width=26)
    draw.polygon(
        [(cx - 50, cy + 2), (cx + 50, cy + 2), (cx, cy + 60)],
        fill=BADGE_OUTLINE,
    )


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    img = make_gradient_rounded_square()
    draw_photo_glyph(img)
    draw_compress_badge(img)

    img.save(OUT_DIR / "icon.png")
    img.save(
        OUT_DIR / "icon.ico",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)],
    )
    print(f"Wrote {OUT_DIR / 'icon.ico'} and {OUT_DIR / 'icon.png'}")


if __name__ == "__main__":
    main()
