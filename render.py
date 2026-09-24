#!/usr/bin/env python3
"""
render.py -- one frame of the animation: carry matrix above, addition
matrix below, quarter-inch graph cells, digits color-coded 0-9 with
black reserved for 0 so it reads distinctly from a blank (no-digit) cell.

Quarter-inch graph paper = 4 squares/inch. DPI is a parameter (default
200) so "quarter inch" is literal, not a loose description -- cell_px =
0.25 * dpi.
"""
from __future__ import annotations

from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from matrix_math import MultiplicationTrace, N_COLUMNS, N_DIGITS, trace_multiplication

# ── digit palette: 0 is black on purpose (isolates it from blank cells,
# per the request); 1-9 are 9 mutually distinct hues (Kelly/Boynton-style
# categorical set, chosen for pairwise distinguishability, not aesthetics) ─
DIGIT_COLOR = {
    0: (0, 0, 0),
    1: (230, 25, 75),
    2: (60, 180, 75),
    3: (255, 225, 25),
    4: (67, 99, 216),
    5: (245, 130, 49),
    6: (145, 30, 180),
    7: (66, 212, 244),
    8: (240, 50, 230),
    9: (191, 239, 69),
}
BLANK_COLOR = (255, 255, 255)      # no digit at this cell (addition matrix only)
GRID_LINE_COLOR = (180, 180, 180)  # quarter-inch graph paper rule lines
BG_COLOR = (255, 255, 255)
TEXT_ON_DARK = (255, 255, 255)
TEXT_ON_LIGHT = (0, 0, 0)


def _luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _cell_text_color(bg: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return TEXT_ON_DARK if _luminance(bg) < 140 else TEXT_ON_LIGHT


def render_frame(
    trace: MultiplicationTrace,
    dpi: int = 200,
    show_digit_labels: bool = True,
    margin_in: float = 0.5,
    header_in: float = 0.9,
) -> Image.Image:
    """One PNG frame: header (num1, num2, product), carry matrix
    (N_DIGITS rows x N_COLUMNS), a gap, addition matrix (N_DIGITS rows x
    N_COLUMNS), all on a literal quarter-inch grid at `dpi`."""
    cell_px = 0.25 * dpi
    margin_px = margin_in * dpi
    header_px = header_in * dpi
    gap_px = cell_px * 1.5

    grid_w = N_COLUMNS * cell_px
    grid_h = N_DIGITS * cell_px

    width = int(margin_px * 2 + grid_w)
    height = int(margin_px * 2 + header_px + grid_h + gap_px + grid_h)

    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", int(cell_px * 0.55))
        header_font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", int(dpi * 0.16))
    except OSError:
        font = ImageFont.load_default()
        header_font = font

    x0 = margin_px
    y_header = margin_px
    draw.text((x0, y_header), f"num1 = {trace.num1}", fill=(0, 0, 0), font=header_font)
    draw.text((x0, y_header + dpi * 0.22), f"num2 = {trace.num2}", fill=(0, 0, 0), font=header_font)
    draw.text((x0, y_header + dpi * 0.44), f"product = {trace.product}", fill=(0, 0, 0), font=header_font)

    y_carry = margin_px + header_px
    y_addition = y_carry + grid_h + gap_px

    def draw_grid(y0: float, get_value_and_kind):
        """kind: ('digit', v) -> colored by DIGIT_COLOR; ('blank', None) -> BLANK_COLOR."""
        for row in range(N_DIGITS):
            for col in range(N_COLUMNS):
                kind, v = get_value_and_kind(row, col)
                bg = BLANK_COLOR if kind == "blank" else DIGIT_COLOR[v]
                cx0 = x0 + col * cell_px
                cy0 = y0 + row * cell_px
                draw.rectangle([cx0, cy0, cx0 + cell_px, cy0 + cell_px], fill=bg,
                               outline=GRID_LINE_COLOR, width=1)
                if kind == "digit" and show_digit_labels:
                    txt = str(v)
                    tcol = _cell_text_color(bg)
                    tb = draw.textbbox((0, 0), txt, font=font)
                    tw, th = tb[2] - tb[0], tb[3] - tb[1]
                    draw.text((cx0 + (cell_px - tw) / 2 - tb[0], cy0 + (cell_px - th) / 2 - tb[1]),
                              txt, fill=tcol, font=font)

    # trace.steps[].row_digits/carry_out are indexed by PLACE VALUE (index
    # 0 = units, ascending = more significant) -- that's the natural,
    # verified internal representation, untouched. Screen columns read
    # left-to-right like normal writing (most significant on the left),
    # which is the OPPOSITE order -- so screen column `col` reads place-
    # value index `N_COLUMNS-1-col`. Getting this backwards was the bug:
    # units-on-the-left instead of units-on-the-right, and rows staggering
    # right instead of left as the multiplier digit's place value rises.
    def carry_lookup(row, col):
        place_idx = N_COLUMNS - 1 - col
        c = trace.steps[row].carry_out[place_idx]
        return ("digit", c)   # carry is always 0 or 1, uses same 0/1 colors -> 0=black, 1=red

    def addition_lookup(row, col):
        place_idx = N_COLUMNS - 1 - col
        d = trace.steps[row].row_digits[place_idx]
        if d is None:
            return ("blank", None)
        return ("digit", d)

    draw.text((x0, y_carry - dpi * 0.20), "CARRY MATRIX (per row, adding that row into the running total)",
               fill=(0, 0, 0), font=font)
    draw_grid(y_carry, carry_lookup)

    draw.text((x0, y_addition - dpi * 0.20), "ADDITION MATRIX (row j = num1 x digit_j(num2), shifted)",
               fill=(0, 0, 0), font=font)
    draw_grid(y_addition, addition_lookup)

    return img


def render_pair(num1: int, num2: int, dpi: int = 200, **kw) -> Image.Image:
    return render_frame(trace_multiplication(num1, num2), dpi=dpi, **kw)


if __name__ == "__main__":
    im = render_pair(1234567890, 9876543210, dpi=150)
    out = "/tmp/mma_test_frame.png"
    im.save(out)
    print(f"wrote {out}  size={im.size}")
