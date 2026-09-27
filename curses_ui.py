#!/usr/bin/env python3
"""
curses_ui.py -- live terminal viewer.

Up/Down step num2 by the current "step place" (default 10^0, the ones
place); Ctrl+O cycles which decimal place Up/Down steps, wrapping from
the 10th place (10^9) back to the ones place. PageUp/PageDown always
jump by one place value beyond the current step, for a quick coarse
move without changing your step setting. Ctrl+G types a specific num2
directly (up to 10 digits); Ctrl+N does the same for num1. A nano-style
shortcut bar sits on the last line. q quits.

ROW-EDIT MODE (Ctrl+E): a cursor arrow appears left of the matrix,
Up/Down select one of the 10 rows (row j = num1 * digit_j(num2)),
Left/Right shift ONLY that row's column offset -- moving it off its
correct place-value position, on purpose, to see what an arbitrary
arrangement adds to. This stops being "the product" the moment any
offset differs from the standard staircase (offset_j = j, "right slope
of 1") -- the total shown is the honest new operation, Sum_j(row_value_j
* 10**offset_j), which reduces exactly to num1*num2 only at the standard
offsets. Ctrl+R resets every offset back to that standard staircase.
Enter exits edit mode without resetting.

Each matrix cell is the Full Block character doubled (██),
colored by digit -- Cody's ASCII-square convention. 0 is literal black,
meant to vanish into a black terminal background so the eye tracks only
the moving 1-9 cascade as num2 steps (see draw_legend for why this is
the opposite call from render.py's static-frame renderer, deliberately).

Column order: trace.steps[].row_digits/carry_out are indexed by PLACE
VALUE (index 0 = units, ascending = more significant) -- the verified
internal representation in matrix_math.py, untouched here. Screen
columns read left-to-right like normal writing (most significant on the
left), the opposite order -- so screen column `col` reads place-value
index `N_COLUMNS-1-col`. Getting this backwards (units on the left,
rows staggering right instead of left as the multiplier digit's place
rises) was a real bug, fixed the same way in render.py.

All drawing goes through safe_addstr(), which swallows curses.error --
ncurses returns ERR from addstr/addwstr whenever text would run past the
window's right edge, including the well-known gotcha where even text
that technically fits can fail if its last character lands exactly on
the window's final column. That's normal ncurses behavior, not a bug to
chase with perfect width arithmetic for every terminal -- the standard,
correct response is to not let it crash the program.

Run: python3 curses_ui.py [num1] [num2_start]
"""
from __future__ import annotations

import colorsys
import curses
import sys

from matrix_math import N_COLUMNS, N_DIGITS, ROW_WIDTH, trace_multiplication
from factor_reconstruction import factor_search

MAX_VAL = 10 ** N_DIGITS - 1

# Factor-reconstruction mode's own safety bounds -- deliberately NOT tied to
# N_DIGITS (the multiplication mode's fixed digit count stays untouched).
# These exist so a live terminal loop stops itself honestly at the wall
# instead of hanging -- see factor_reconstruction.py's own docstring.
FACTOR_MAX_LIVE_STATES = 200_000
FACTOR_TIME_BUDGET_PER_LEVEL_S = 2.0


def CTRL(letter: str) -> int:
    return ord(letter.upper()) & 0x1F


def _rainbow_rgb() -> dict:
    """Digits 1-9 swept red->blue across the visible-spectrum hue arc
    (0deg red to 240deg blue in HSV, full saturation/value), 9 evenly
    spaced steps -- colorsys.hsv_to_rgb, not a hand-rolled gradient, so
    the spectrum is actually even. 0 stays true black, unconditionally:
    that's the standing, locked correction (0 must vanish into a black
    terminal background) and it is NOT part of the rainbow."""
    colors = {0: (0, 0, 0)}
    for digit in range(1, 10):
        hue = (digit - 1) / 8 * (240.0 / 360.0)  # 0..8 steps -> 0deg..240deg
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colors[digit] = (round(r * 255), round(g * 255), round(b * 255))
    return colors


DIGIT_RGB = _rainbow_rgb()
BLOCK = "██"  # Full Block, doubled


def _nearest_xterm256(rgb) -> int:
    r, g, b = rgb

    def to6(v):
        return round(v / 255 * 5)

    r6, g6, b6 = to6(r), to6(g), to6(b)
    return 16 + 36 * r6 + 6 * g6 + b6


def _basic8_for(rgb) -> int:
    r, g, b = rgb
    candidates = {
        curses.COLOR_BLACK: (0, 0, 0), curses.COLOR_RED: (255, 0, 0),
        curses.COLOR_GREEN: (0, 255, 0), curses.COLOR_YELLOW: (255, 255, 0),
        curses.COLOR_BLUE: (0, 0, 255), curses.COLOR_MAGENTA: (255, 0, 255),
        curses.COLOR_CYAN: (0, 255, 255), curses.COLOR_WHITE: (255, 255, 255),
    }
    best, best_d = curses.COLOR_WHITE, float("inf")
    for code, (cr, cg, cb) in candidates.items():
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_d:
            best, best_d = code, d
    return best


def _setup_colors() -> dict:
    curses.start_color()
    curses.use_default_colors()
    pairs = {}
    has_256 = curses.COLORS >= 256
    for digit in range(10):
        pair_id = digit + 1
        rgb = DIGIT_RGB[digit]
        fg = _nearest_xterm256(rgb) if has_256 else _basic8_for(rgb)
        curses.init_pair(pair_id, fg, -1)
        pairs[digit] = curses.color_pair(pair_id)
    # a reverse-video pair for the nano-style bottom bar
    curses.init_pair(20, curses.COLOR_BLACK, curses.COLOR_WHITE)
    pairs["bar"] = curses.color_pair(20)
    return pairs


def safe_addstr(win, y: int, x: int, text: str, attr=None) -> None:
    try:
        if attr is None:
            win.addstr(y, x, text)
        else:
            win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw_legend(win, y, x, pairs):
    safe_addstr(win, y, x, "legend:")
    cx = x + 8
    for digit in range(10):
        safe_addstr(win, y, cx, BLOCK, pairs[digit])
        safe_addstr(win, y, cx + 2, str(digit))
        cx += 4
    safe_addstr(win, y + 1, x, "*0 is true black -- invisible on a black terminal background, on purpose")


def row_values(num1: int, num2: int) -> list:
    """row_values[j] = num1 * digit_j(num2), j=0 the ones digit -- the same
    per-row product matrix_math.trace_multiplication uses internally, but
    kept here explicitly so edit mode can re-place it at an arbitrary
    offset instead of matrix_math's own fixed offset_j=j placement."""
    return [num1 * ((num2 // 10 ** j) % 10) for j in range(N_DIGITS)]


def digits_lsb_first(value: int, width: int) -> list:
    s = str(value).zfill(width)
    return [int(c) for c in reversed(s)][:width]


def offset_total(num1: int, num2: int, offsets: list) -> int:
    """Sum_j(row_value_j * 10**offset_j). Equals num1*num2 exactly when
    every offset_j == j (the standard staircase); any other arrangement
    is a different, honestly-new operation, not the product."""
    vals = row_values(num1, num2)
    return sum(v * (10 ** off) for v, off in zip(vals, offsets))


def draw_matrix(win, y, x, trace, pairs):
    for row in range(N_DIGITS):
        step = trace.steps[row]
        for col in range(N_COLUMNS):
            place_idx = N_COLUMNS - 1 - col   # see module docstring: column-order fix
            d = step.row_digits[place_idx]
            if d is None:
                continue
            safe_addstr(win, y + row, x + col * 2, BLOCK, pairs[d])


def draw_matrix_at_offsets(win, y, x, num1: int, num2: int, offsets: list,
                            pairs, cursor_row: int = None):
    """Edit-mode renderer: each row placed at its OWN offsets[row], not
    the standard staircase. Same screen column-order convention as
    draw_matrix (place_idx = N_COLUMNS-1-col)."""
    vals = row_values(num1, num2)
    for row in range(N_DIGITS):
        if cursor_row is not None:
            marker = "▶" if row == cursor_row else " "  # right-pointing triangle
            safe_addstr(win, y + row, x - 2, marker,
                        pairs["bar"] if row == cursor_row else None)
        digs = digits_lsb_first(vals[row], ROW_WIDTH)
        off = offsets[row]
        for k, d in enumerate(digs):
            col = off + k
            if not (0 <= col < N_COLUMNS):
                continue
            place_idx = col
            screen_col = N_COLUMNS - 1 - place_idx
            safe_addstr(win, y + row, x + screen_col * 2, BLOCK, pairs[d])


def draw_status_bar(win, pairs, step_place: int, h: int, w: int):
    left = f"^G Jump num2  ^N Jump num1  ^O Step x10 (now: 10^{step_place})  PgUp/PgDn +-1 higher place  Up/Dn +-step  ^E Edit rows  ^F Factor mode  q Quit"
    bar = left[: max(0, w - 1)].ljust(max(0, w - 1))
    safe_addstr(win, h - 1, 0, bar, pairs["bar"])


def draw_edit_status_bar(win, pairs, cursor_row: int, h: int, w: int):
    left = f"ROW EDIT  row {cursor_row}  Up/Dn select row  Left/Right shift offset  ^R reset (slope=1)  Enter exit"
    bar = left[: max(0, w - 1)].ljust(max(0, w - 1))
    safe_addstr(win, h - 1, 0, bar, pairs["bar"])


def prompt_for_number(stdscr, pairs, h: int, w: int, label: str, current: int) -> "int | None":
    """Nano-style bottom-line input: digits only, capped at N_DIGITS
    characters, Enter confirms, Esc/Ctrl+C cancels. Returns None on
    cancel so the caller leaves the value untouched."""
    buf = ""
    curses.curs_set(1)
    try:
        while True:
            prompt = f"{label} (max {N_DIGITS} digits, Enter=ok Esc=cancel): {buf}"
            safe_addstr(stdscr, h - 1, 0, " " * max(0, w - 1), pairs["bar"])
            safe_addstr(stdscr, h - 1, 0, prompt[: max(0, w - 1)], pairs["bar"])
            stdscr.move(h - 1, min(w - 2, len(prompt)))
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (27,):  # Esc
                return None
            elif ch in (curses.KEY_ENTER, 10, 13):
                if buf == "":
                    return None
                val = int(buf)
                return min(MAX_VAL, val)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                buf = buf[:-1]
            elif 48 <= ch <= 57 and len(buf) < N_DIGITS:  # ASCII '0'-'9'
                buf += chr(ch)
    finally:
        curses.curs_set(0)


def prompt_for_bignum(stdscr, pairs, h: int, w: int, label: str) -> "int | None":
    """Same nano-style input as prompt_for_number, but deliberately
    UNCAPPED -- factor-reconstruction mode's whole point is testing real
    moduli (hundreds of digits), not N_DIGITS-limited toy numbers. Digits
    only; Enter confirms, Esc/Ctrl+C cancels."""
    buf = ""
    curses.curs_set(1)
    try:
        while True:
            shown = buf if len(buf) <= w - 40 else buf[:12] + f"...({len(buf)} digits)..." + buf[-12:]
            prompt = f"{label} (any length, Enter=ok Esc=cancel): {shown}"
            safe_addstr(stdscr, h - 1, 0, " " * max(0, w - 1), pairs["bar"])
            safe_addstr(stdscr, h - 1, 0, prompt[: max(0, w - 1)], pairs["bar"])
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (27,):  # Esc
                return None
            elif ch in (curses.KEY_ENTER, 10, 13):
                if buf == "":
                    return None
                return int(buf)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                buf = buf[:-1]
            elif 48 <= ch <= 57:  # ASCII '0'-'9' -- no length cap
                buf += chr(ch)
    finally:
        curses.curs_set(0)


def draw_factor_mode(stdscr, pairs, state: dict, h: int, w: int):
    """Live view of factor_reconstruction.py's digit-DP search: watching
    the wall form, not attempting to factor anything at real key size.
    Draws the peak-live-state count per n_digits level tried so far as a
    log-scale bar, plus the current level's own per-column trace."""
    N = state["N"]
    n_str = str(N)
    digits_label = f"N ({len(n_str)} digits)"
    shown_n = n_str if len(n_str) <= w - 20 else n_str[:10] + f"...({len(n_str)} digits total)..." + n_str[-10:]
    safe_addstr(stdscr, 0, 2, f"{digits_label}: {shown_n}")
    safe_addstr(stdscr, 1, 2, "FACTOR RECONSTRUCTION -- addition-matrix undoing, from the fixed (units) end outward")

    row = 3
    if state.get("solutions"):
        p, q = state["solutions"][0]
        safe_addstr(stdscr, row, 2, f"SOLVED: N = {p} * {q}", pairs.get(2))
        row += 2
    elif state.get("wall_reached"):
        safe_addstr(stdscr, row, 2,
                    f"WALL REACHED at n_digits={state['n_digits']}: {state['wall_reason']}", pairs.get(1))
        row += 1
        safe_addstr(stdscr, row, 2,
                    "This is the honest boundary, not a bug -- see factor_reconstruction.py's own")
        row += 1
        safe_addstr(stdscr, row, 2,
                    "growth_law_estimate()/extrapolate_infeasibility() for what continuing implies.")
        row += 2
    else:
        safe_addstr(stdscr, row, 2, f"searching... n_digits={state['n_digits']}  "
                                     f"elapsed={state.get('level_elapsed', 0.0):.2f}s")
        row += 2

    safe_addstr(stdscr, row, 2, "peak live-states per n_digits level (log scale, one # per decade):")
    row += 1
    for n, peak in sorted(state["peaks"].items()):
        bar_len = max(1, int((peak and __import__("math").log10(max(peak, 1))) or 0))
        bar = "#" * min(bar_len, w - 30)
        safe_addstr(stdscr, row, 2, f"  n_digits={n:3d}  peak={peak:>10}  {bar}")
        row += 1
        if row >= h - 4:
            break

    if len(state["peaks"]) >= 2:
        ns = sorted(state["peaks"])
        ratios = [state["peaks"][b] / state["peaks"][a] for a, b in zip(ns, ns[1:]) if state["peaks"][a] > 0]
        if ratios:
            mean_ratio = sum(ratios) / len(ratios)
            row += 1
            safe_addstr(stdscr, row, 2, f"measured growth ratio: {mean_ratio:.2f}x per added digit")

    bar_text = "^B Enter modulus  Space pause/resume  r reset  Enter/Esc exit factor mode  q Quit"
    safe_addstr(stdscr, h - 1, 0, bar_text[: max(0, w - 1)].ljust(max(0, w - 1)), pairs["bar"])


def main(stdscr):
    num1 = int(sys.argv[1]) if len(sys.argv) > 1 else 1234567890
    num2 = int(sys.argv[2]) if len(sys.argv) > 2 else 1000000000
    if not (0 <= num1 <= MAX_VAL) or not (0 <= num2 <= MAX_VAL):
        raise ValueError(f"both numbers must be 0..{MAX_VAL} ({N_DIGITS} digits)")

    curses.curs_set(0)
    stdscr.keypad(True)
    pairs = _setup_colors()

    step_place = 0  # 0 = ones place, 9 = leading (10^9) place; Ctrl+O cycles, wraps 9->0

    edit_mode = False
    cursor_row = 0
    offsets = list(range(N_DIGITS))  # standard staircase, "right slope of 1"

    # Factor-reconstruction mode -- entirely separate state, no N_DIGITS
    # cap (see factor_reconstruction.py / FACTOR_MAX_LIVE_STATES above).
    factor_mode = False
    factor_running = False
    factor_state = {"N": None, "n_digits": 1, "peaks": {}, "solutions": [],
                     "wall_reached": False, "wall_reason": "", "level_elapsed": 0.0}

    needed_w = max(2 + N_COLUMNS * 2, 52)
    needed_h = 9 + N_DIGITS + 2

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        if h < needed_h or w < needed_w:
            safe_addstr(stdscr, 0, 0, f"terminal too small -- need at least {needed_w}x{needed_h}, have {w}x{h}")
            stdscr.refresh()
        elif factor_mode:
            if factor_state["N"] is None:
                safe_addstr(stdscr, 0, 2, "FACTOR RECONSTRUCTION -- press ^B to enter a modulus (any length)")
                safe_addstr(stdscr, h - 1, 0,
                            "^B Enter modulus  Enter/Esc exit factor mode  q Quit"[: max(0, w - 1)].ljust(max(0, w - 1)),
                            pairs["bar"])
                stdscr.refresh()
            else:
                draw_factor_mode(stdscr, pairs, factor_state, h, w)
                stdscr.refresh()

                if factor_running and not factor_state["solutions"] and not factor_state["wall_reached"]:
                    n = factor_state["n_digits"]
                    r = factor_search(factor_state["N"], n_digits=n,
                                       max_live_states=FACTOR_MAX_LIVE_STATES,
                                       time_budget_s=FACTOR_TIME_BUDGET_PER_LEVEL_S)
                    factor_state["peaks"][n] = max((h_[2] for h_ in r["history"]), default=0)
                    factor_state["level_elapsed"] = r["elapsed_s"]
                    if r["solutions"]:
                        factor_state["solutions"] = r["solutions"]
                        factor_running = False
                    elif r["aborted"]:
                        factor_state["wall_reached"] = True
                        factor_state["wall_reason"] = r["aborted_reason"]
                        factor_running = False
                    else:
                        factor_state["n_digits"] += 1
                    stdscr.nodelay(True)
                else:
                    stdscr.nodelay(False)
        elif edit_mode:
            total = offset_total(num1, num2, offsets)
            is_standard = offsets == list(range(N_DIGITS))
            safe_addstr(stdscr, 0, 2, f"num1 = {num1}")
            safe_addstr(stdscr, 1, 2, f"num2 = {num2}   row {cursor_row} offset = {offsets[cursor_row]}")
            label = "product" if is_standard else "shape total (NOT the product -- offsets edited)"
            safe_addstr(stdscr, 2, 2, f"{label} = {total}")

            draw_legend(stdscr, 4, 2, pairs)
            safe_addstr(stdscr, 7, 2, "ADDITION MATRIX -- ROW EDIT MODE")
            draw_matrix_at_offsets(stdscr, 8, 2, num1, num2, offsets, pairs, cursor_row)
            draw_edit_status_bar(stdscr, pairs, cursor_row, h, w)
            stdscr.refresh()
        else:
            trace = trace_multiplication(num1, num2)
            safe_addstr(stdscr, 0, 2, f"num1 = {num1}")
            safe_addstr(stdscr, 1, 2, f"num2 = {num2}   step = 10^{step_place} = {10**step_place}")
            safe_addstr(stdscr, 2, 2, f"product = {trace.product}")

            draw_legend(stdscr, 4, 2, pairs)
            safe_addstr(stdscr, 7, 2, "ADDITION MATRIX (row j = num1 x digit_j(num2), shifted)")
            draw_matrix(stdscr, 8, 2, trace, pairs)
            draw_status_bar(stdscr, pairs, step_place, h, w)
            stdscr.refresh()

        key = stdscr.getch()
        if key == -1:  # nodelay(True), no key waiting -- just keep advancing the search
            continue
        if factor_mode:
            if key in (curses.KEY_ENTER, 10, 13, 27):  # Enter or Esc -- exit factor mode
                factor_mode = False
                factor_running = False
                stdscr.nodelay(False)
            elif key in (ord("q"), ord("Q")):
                break
            elif key == CTRL("B"):
                stdscr.nodelay(False)
                new_val = prompt_for_bignum(stdscr, pairs, h, w, "factor-reconstruct N")
                if new_val is not None and new_val > 1:
                    factor_state = {"N": new_val, "n_digits": 1, "peaks": {}, "solutions": [],
                                     "wall_reached": False, "wall_reason": "", "level_elapsed": 0.0}
                    factor_running = True
            elif key == ord(" "):
                factor_running = not factor_running and factor_state["N"] is not None
                if not factor_running:
                    stdscr.nodelay(False)
            elif key in (ord("r"), ord("R")):
                if factor_state["N"] is not None:
                    factor_state = {"N": factor_state["N"], "n_digits": 1, "peaks": {}, "solutions": [],
                                     "wall_reached": False, "wall_reason": "", "level_elapsed": 0.0}
                    factor_running = True
            continue
        if edit_mode:
            if key in (curses.KEY_ENTER, 10, 13):
                edit_mode = False
            elif key == curses.KEY_UP:
                cursor_row = max(0, cursor_row - 1)
            elif key == curses.KEY_DOWN:
                cursor_row = min(N_DIGITS - 1, cursor_row + 1)
            elif key == curses.KEY_LEFT:
                offsets[cursor_row] = max(0, offsets[cursor_row] - 1)
            elif key == curses.KEY_RIGHT:
                offsets[cursor_row] = min(N_COLUMNS - 1, offsets[cursor_row] + 1)
            elif key == CTRL("R"):
                offsets = list(range(N_DIGITS))
            elif key in (ord("q"), ord("Q")):
                break
            continue

        if key in (ord("q"), ord("Q")):
            break
        elif key == CTRL("E"):
            edit_mode = True
        elif key == CTRL("F"):
            factor_mode = True
        elif key == curses.KEY_UP:
            num2 = min(MAX_VAL, num2 + 10 ** step_place)
        elif key == curses.KEY_DOWN:
            num2 = max(0, num2 - 10 ** step_place)
        elif key == curses.KEY_PPAGE:
            num2 = min(MAX_VAL, num2 + 10 ** min(N_DIGITS - 1, step_place + 1))
        elif key == curses.KEY_NPAGE:
            num2 = max(0, num2 - 10 ** min(N_DIGITS - 1, step_place + 1))
        elif key == CTRL("O"):
            step_place = (step_place + 1) % N_DIGITS  # wraps after the 10th spot back to the ones place
        elif key == CTRL("G"):
            h, w = stdscr.getmaxyx()
            new_val = prompt_for_number(stdscr, pairs, h, w, "jump num2 to", num2)
            if new_val is not None:
                num2 = new_val
        elif key == CTRL("N"):
            h, w = stdscr.getmaxyx()
            new_val = prompt_for_number(stdscr, pairs, h, w, "jump num1 to", num1)
            if new_val is not None:
                num1 = new_val


if __name__ == "__main__":
    curses.wrapper(main)
