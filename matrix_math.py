#!/usr/bin/env python3
"""
matrix_math.py -- the exact arithmetic behind the addition-matrix animation.

Grade-school long multiplication of two 10-digit numbers, row by row:
each row j is (num1 * digit_j_of_num2), shifted left j places. The rows
are then summed ONE AT A TIME into a running total -- not all 10 at once --
specifically so every carry stays a single digit (0 or 1). Summing 10
digits in a column simultaneously can carry up to 9; summing two numbers
(running total + one row) at a time never carries past 1. That's what
keeps the carry matrix the same shape and same color-depth as the
addition matrix instead of needing its own wider palette.

20 columns (0=least significant) hold every case: two 10-digit numbers
multiply to at most a 20-digit product (9999999999 * 9999999999 has 20
digits), and the widest single row (num1 * 9) has at most 11 digits.

Verified against Python's own `*` for every row and the final total --
see verify() at the bottom, run standalone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

N_DIGITS = 10          # digits per input number
ROW_WIDTH = N_DIGITS + 1   # widest a single row's product can be (num1 * single digit)
N_COLUMNS = N_DIGITS + ROW_WIDTH  # = 20, room for row 9's shift (cols 9..19) plus row 0 (cols 0..10)


def digits_lsb_first(n: int, width: int) -> List[int]:
    """n's decimal digits, least-significant first, zero-padded to width.
    Raises if n needs more than `width` digits -- callers size width
    generously on purpose so this is a real assertion, not a silent trim."""
    out = []
    for _ in range(width):
        out.append(n % 10)
        n //= 10
    if n != 0:
        raise ValueError(f"value needs more than {width} digits")
    return out


@dataclass
class RowStep:
    """One row of the animation: the row's own digits (positioned by
    column, None where the row contributes nothing) and the carries
    generated adding this row into the running total."""
    row_index: int              # which digit of num2 this row multiplies by
    multiplier_digit: int       # num2's digit at this position
    row_digits: List[Optional[int]] = field(default_factory=list)   # len N_COLUMNS, None = blank cell
    carry_out: List[int] = field(default_factory=list)              # len N_COLUMNS, 0 or 1
    running_total_after: int = 0


@dataclass
class MultiplicationTrace:
    num1: int
    num2: int
    steps: List[RowStep]
    product: int


def trace_multiplication(num1: int, num2: int) -> MultiplicationTrace:
    """The full, exact, step-by-step trace: one RowStep per digit of
    num2, addition-matrix cells and carry-matrix cells both positioned
    on the same N_COLUMNS grid."""
    if not (0 <= num1 < 10 ** N_DIGITS) or not (0 <= num2 < 10 ** N_DIGITS):
        raise ValueError(f"both numbers must fit in {N_DIGITS} digits")

    d1 = digits_lsb_first(num1, N_DIGITS)
    d2 = digits_lsb_first(num2, N_DIGITS)

    running_total = [0] * N_COLUMNS   # digit array, lsb-first, column c = place value 10^c
    steps: List[RowStep] = []

    for j in range(N_DIGITS):
        b = d2[j]
        row_value = num1 * b  # 0..90 * up to 9999999999 -> at most 11 digits
        row_digit_stream = digits_lsb_first(row_value, ROW_WIDTH)  # lsb-first, len 11

        # place this row's digits at columns j .. j+ROW_WIDTH-1; blank elsewhere
        row_digits: List[Optional[int]] = [None] * N_COLUMNS
        for k, dgt in enumerate(row_digit_stream):
            row_digits[j + k] = dgt

        # add this row into the running total, one column at a time, carry in {0,1}
        carry = 0
        carry_out = [0] * N_COLUMNS
        new_total = list(running_total)
        for c in range(N_COLUMNS):
            b_c = row_digits[c] if row_digits[c] is not None else 0
            s = new_total[c] + b_c + carry
            new_total[c] = s % 10
            carry = s // 10
            carry_out[c] = carry
        # any final carry beyond column N_COLUMNS-1 would mean N_COLUMNS
        # was sized too small -- assert it's impossible by construction
        assert carry == 0, "carry overflowed N_COLUMNS -- widen the grid"

        running_total = new_total
        total_value = sum(dgt * (10 ** c) for c, dgt in enumerate(running_total))

        steps.append(RowStep(
            row_index=j,
            multiplier_digit=b,
            row_digits=row_digits,
            carry_out=carry_out,
            running_total_after=total_value,
        ))

    product = steps[-1].running_total_after
    return MultiplicationTrace(num1=num1, num2=num2, steps=steps, product=product)


def verify(n_random: int = 200, seed: int = 0) -> dict:
    """Checked, not assumed: every row's value and the final running
    total match Python's own arithmetic exactly, for random pairs plus
    the min/max/edge cases."""
    import random
    rng = random.Random(seed)
    lo, hi = 10 ** (N_DIGITS - 1), 10 ** N_DIGITS - 1
    cases = [(lo, lo), (hi, hi), (lo, hi), (0, 0), (0, hi), (1, hi)]
    cases += [(rng.randint(0, hi), rng.randint(0, hi)) for _ in range(n_random)]

    n_checked = 0
    for num1, num2 in cases:
        tr = trace_multiplication(num1, num2)
        expected = num1 * num2
        assert tr.product == expected, f"{num1}*{num2}: got {tr.product}, want {expected}"
        # cross-check each row against the digit it claims to multiply by
        d2 = digits_lsb_first(num2, N_DIGITS)
        running = 0
        for j, step in enumerate(tr.steps):
            assert step.multiplier_digit == d2[j]
            row_val = sum((d if d is not None else 0) * (10 ** c)
                          for c, d in enumerate(step.row_digits))
            # row_digits are positioned at absolute columns, so their
            # summed value already carries the *10**j shift -- compare
            # against the shifted quantity, not the raw row product.
            assert row_val == num1 * d2[j] * (10 ** j), f"row {j} mismatch for {num1}*{num2}"
            running += num1 * d2[j] * (10 ** j)
            assert step.running_total_after == running, f"running total mismatch at row {j}"
        n_checked += 1
    return {"ok": True, "n_checked": n_checked}


if __name__ == "__main__":
    print(verify())
    tr = trace_multiplication(1234567890, 9876543210)
    print(f"1234567890 * 9876543210 = {tr.product}")
    print(f"python check: {1234567890 * 9876543210}")
    print(f"match: {tr.product == 1234567890 * 9876543210}")
