# Multiplication Matrix Explorer

**Cody Michael Allison** (Michael Rendier) · the.wandering.god@gmail.com ·
[github.com/michaelrendier](https://github.com/michaelrendier) ·
ORCID: [0009-0007-7239-6760](https://orcid.org/0009-0007-7239-6760)

Renamed from Multiplication Matrix *Animator* (2026-09-24) once the tool
grew past playback into a live editing/exploration instrument — the
name change tracks what the tool actually does now, not a rewrite.

Animates and lets you *edit* grade-school long multiplication of two
10-digit numbers as two stacked, color-coded grids: a **carry matrix** on
top and an **addition matrix** below, both drawn on a literal quarter-inch
graph (0.25" cells, `cell_px = 0.25 * dpi`).

## The addition matrix basin

The addition matrix isn't just a display of one multiplication — it's
ten fixed row-templates (`num1 * 0` .. `num1 * 9`) that a second number's
digits reshuffle into position. That fixed-template, reshuffled-position
structure is what makes it a genuine **basin**: a bounded state space
(ten row values, each placeable at any of 20 column offsets) with one
distinguished point (the standard staircase, offset_j = j) where the
whole thing reduces to an actual product, and a much larger surrounding
region where it doesn't. Full derivations — the exact ordered/unordered
permutation counts, the 2-adic (bitshift) and decimal-trailing-zero
reduction theorems, and the offset-shift equation `curses_ui.py`'s row-
edit mode now lets you drive by hand — are in
[`wiki/addition_matrix_basin.md`](wiki/addition_matrix_basin.md).

## The math (`matrix_math.py`)

Row `j` of the addition matrix is `num1 * digit_j(num2)`, shifted left `j`
places. Rows are summed **one at a time** into a running total (not all
10 at once) specifically so every carry is a single digit, 0 or 1 —
that's what lets the carry matrix use the exact same color scheme as the
addition matrix instead of needing its own wider palette. 20 columns
cover every case: the widest single row (`num1 * 9`) is at most 11
digits, and the full product of two 10-digit numbers is at most 20.

Verified against Python's own `*`, row by row and on the final total,
for edge cases (`0`, min, max) plus 200 random pairs — `python3
matrix_math.py` reruns the check.

## Colors

`0` is black, on purpose — isolates it cleanly from a **blank** cell
(white — a column this row doesn't reach at all, not a real zero).
Digits `1`–`9` get 9 mutually distinct hues. Carry cells reuse the same
`0`/`1` colors (carry is always 0 or 1 by construction).

## Rendering one frame (`render.py`)

```python
from render import render_pair
img = render_pair(1234567890, 9876543210, dpi=200)   # literal quarter-inch cells at 200dpi
img.save("frame.png")
```

## The exhaustive range, and why it can't be literal

Every pair of 10-digit numbers is `~9e9 * 9e9 ≈ 8.1e19` multiplications —
not a large render job, one that cannot finish, ever, at any frame rate.
`mapper.py`'s `MatrixSpaceEvolutionMapper` is built around that constraint:
it renders **on demand**, one bounded path through the space at a time,
the same posture as navigating a fractal live rather than pre-rendering
the whole parameter plane.

```python
from mapper import MatrixSpaceEvolutionMapper

m = MatrixSpaceEvolutionMapper(num1_start=1234567890, num2_start=9876543210)

# num2 walks forward, num1 fixed
stream = m.sweep_num2(count=30, step=1)

# turn one decimal place of num2 like a single odometer wheel
stream = m.digit_drive(count=10, target="num2", place=0, step=1)

# both numbers walk together (the diagonal of the multiplication plane)
stream = m.diagonal(count=30, step=1)

# a hand-picked list of specific pairs, in order
stream = m.explicit([(1234567890, 9876543210), (9999999999, 1)])

m.render_gif(stream, "out.gif", dpi=120, ms_per_frame=400)
```

Evolution modes: `sweep_num1`, `sweep_num2`, `diagonal`, `digit_drive`,
`explicit`, `custom(fn, count)` for anything not covered above.

## Driving it live (`driver.py`)

```bash
python3 driver.py [num1] [num2]
```

Every one of the 20 digits (10 per number) is its own odometer wheel —
scroll or click `+`/`-` on any digit and the frame re-renders
immediately with the new pair. Overflow/underflow ripples into the
neighboring digit like a real odometer (clamped at the leading digit,
no wraparound past it). This is the literal "drive it around" mode —
no range to configure first, just turn dials and watch the matrices
update.

## Terminal viewer (`curses_ui.py`)

```bash
python3 curses_ui.py [num1] [num2_start]
```

One live-updating addition matrix (no carry matrix in this view),
redrawn on every keypress. Each cell is the Full Block character doubled
(`██`), color-coded by digit, with a compact digit=color legend at the
top. `0` is literal black, deliberately, locked — it's meant to vanish
into a black terminal background so the eye tracks only the moving 1-9
cascade as num2 steps, rather than being cluttered by the most common
digit. (Opposite call from the static PIL renderer below, on purpose — a
frozen single frame wants 0 legible; a live-stepping view wants it out
of the way.) Digits `1`-`9` are a true rainbow — red (`1`) to blue (`9`),
9 evenly spaced steps around the visible-spectrum hue arc
(`colorsys.hsv_to_rgb`, not a hand-rolled gradient). Colors auto-map to
the terminal's 256-color palette when available, falling back to the 8
basic ANSI colors otherwise.

Keys:
- `Up`/`Down` — step num2 by the current step place (default `10^0`, ones)
- `Ctrl+O` — cycle which decimal place Up/Down steps; wraps from the
  10th place (`10^9`) back to the ones place
- `PageUp`/`PageDown` — jump by one place value beyond the current step,
  for a fast coarse move without changing your step setting
- `Ctrl+G` — type a specific num2 directly (bottom-line prompt, digits
  only, capped at 10 characters)
- `Ctrl+N` — same, for num1
- `Ctrl+E` — enter **row-edit mode** (below)
- `q` — quit

A nano-style shortcut bar sits on the last line listing all of the above.

### Row-edit mode (`Ctrl+E`)

Lets you pull a single row off its correct place-value position and see
what the resulting arrangement adds to — a `▶` cursor appears left of
the matrix.

- `Up`/`Down` — move the cursor to a different row (`row j = num1 *
  digit_j(num2)`)
- `Left`/`Right` — shift the *selected row only* to a different column
  offset (0..19)
- `Ctrl+R` — reset every row back to the standard staircase
  (`offset_j = j`, "slope of 1")
- `Enter` — exit row-edit mode (offsets are kept, not reset)

The total shown updates on every shift: `Σ(row_value_j * 10**offset_j)`.
At the standard staircase this is exactly `num1 * num2` — provably, not
approximately, since that sum *is* long multiplication's own definition.
The moment any row's offset differs from `j`, the display switches from
`product =` to `shape total (NOT the product -- offsets edited) =`,
because at that point it genuinely isn't the product anymore, it's a
different, user-defined operation on the same ten row-values. See the
wiki page for the exact math of what that operation is and isn't.

Column order: numbers read left-to-right normally (most significant
digit on the left), and each row shifts further **left** as the
multiplier digit's place value rises — the actual grade-school layout.
(An earlier version had this backwards — units on the left, rows
shifting right — fixed in both this file and `render.py`.)

## Files

- `matrix_math.py` — the exact arithmetic, self-checking
- `render.py` — one PNG frame, quarter-inch grid, color-coded
- `mapper.py` — the constructor / evolution-mode frame generator, GIF export (capped) + streaming PNG-sequence export (uncapped)
- `driver.py` — live Tkinter "drive around" viewer (mouse/scroll, one digit wheel per place)
- `curses_ui.py` — live terminal viewer (Up/Down arrows step num2, redraws instantly; `Ctrl+E` row-edit mode; rainbow 1-9)
- `wiki/addition_matrix_basin.md` — the basin's own math: exact permutation counts, the 2-adic and decimal-trailing-zero reduction theorems, the offset-shift equation

## Related

- `~/.claude/skills/addition-matrix/SKILL.md` — the methodology skill
  built from this tool's own findings (periodicity under incrementing,
  the digit=color mapping, orientation discipline). Load it before
  studying this repo's output.
- `FourthAgePapers/FastInverse/` — the "costly direction collapses to
  free when the representation already encodes the answer" claim this
  basin's ordered/unordered permutation gap (10^9 vs 9,225 for one
  column) is a direct, checked instance of.
