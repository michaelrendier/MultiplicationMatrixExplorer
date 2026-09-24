# The Addition Matrix Basin

**Cody Michael Allison** (Michael Rendier) · the.wandering.god@gmail.com ·
[github.com/michaelrendier](https://github.com/michaelrendier) ·
ORCID: [0009-0007-7239-6760](https://orcid.org/0009-0007-7239-6760)

Every number below is computed and checked against the actual running
code (`matrix_math.py`, `curses_ui.py`), not asserted. This page is the
math behind `curses_ui.py`'s row-edit mode and the exact-count work that
led to it.

---

## 1. The basin, defined

Fix `num1`. There are exactly ten possible row values —
`num1*0 .. num1*9` — full stop; no choice of `num2` ever produces an
eleventh. `num2`'s ten digits only decide *which* of those ten fixed
templates lands at *which* column offset. That's the basin: ten fixed
row-values, a 20-column space of possible offsets, and one distinguished
configuration — the standard staircase `offset_j = j` — where the whole
arrangement reduces to an actual product:

    Σ_j ( (num1 * digit_j(num2)) * 10^offset_j )  =  num1 * num2      iff offset_j = j for every j

That's not approximate — it's long multiplication's own definition,
restated. Every other point in the 20^10-sized offset space is a
different, legal, well-defined operation that is *not* the product.
`curses_ui.py`'s row-edit mode (`Ctrl+E`) drives this basin directly:
select a row, move its offset, watch the total leave (and, via `Ctrl+R`,
return to) that one distinguished point.

## 2. How much of the basin's structure survives compression — exact counts

Local structure (only ten templates exist) says very little about how
those templates can *arrange*. Measured directly, for one column, ten
slots, target last-digit 7:

    ORDERED   (slot order matters):    exactly 10^9  =  1,000,000,000
    UNORDERED (multisets, no order):   exactly 9,225

Both exact, not estimated. The ordered count has a clean bijective proof:
fix any 9 of the 10 slots freely; the 10th is *forced* to whichever
single digit completes the sum to the target mod 10 — always exists,
always unique. That argument is target-independent, so the distribution
across all ten possible last digits is perfectly uniform, 10^9 each,
`10^10` total. The unordered count has no such bijection (permuting which
slot holds which value doesn't manufacture new multisets) — computed by
direct enumeration over all `C(19,10) = 92,378` multisets. It sits close
to, but is *not* equal to, the naive "divide by 10" guess of 9,237.8 —
real, small, non-uniformity (off by 12.8, ~0.14%), not rounding noise.

**Ratio: ≈108,401×, roughly five to six orders of magnitude.** That gap
is the direct, checked reason a column's arrangement-space dwarfs its
composition-space — see `FourthAgePapers/FastInverse/README.md` for the
general claim this is one instance of.

## 3. The bitshift theorem — 2-adic valuation is additive, exactly

Take each of the ten rows, strip its own trailing zero *bits* (binary,
not decimal) until it's odd, sum the results. This is not noise; it
follows one exact theorem:

    odd_part(num1 * d)  =  odd_part(num1) * odd_part(d)

because 2-adic valuation (`v_2`, the trailing-zero-bit count) is
additive under multiplication: `v_2(ab) = v_2(a) + v_2(b)`, for any
integers `a, b` — a standard, exact number-theoretic fact, not specific
to this tool. Two worked, fully-verified instances:

**`num1 = 1234567890`** (even; `odd_part(num1) = 617283945`). Sweeping
`d = 0..9` once each: `Σ odd_part(d) = 1+1+3+1+5+3+7+1+9 = 31` — a
constant independent of `num1`. So for *any* even-ending `num1` swept
this way, the bitshifted sum is exactly `31 * odd_part(num1)`. Checked:
`617283945 * 31 = 19,135,802,295`, matching the direct computation
exactly.

**`num1 = 1546854629`** (odd; `odd_part(num1) = num1` itself, no
reduction needed on that side). Against the real problem
`1546854629 * 7283619945` (digits `5,4,9,9,1,6,3,8,2,7`,
`Σ odd_part(digit) = 5+1+9+9+1+3+3+1+1+7 = 40`): bitshifted sum
`= 1546854629 * 40 = 61,874,185,160`, matching the direct row-by-row
computation exactly. (Note `40` here is *this* `num2`'s own digit
multiset, not the universal `31` — `31` only holds for a full,
non-repeating `0..9` sweep.)

## 4. Decimal-trailing-zero stripping — a different operation, and an exact O(1) predictor

Stripping trailing zero *digits* (decimal, leaving the remaining digits
untouched) is a genuinely different operation from the bitshift above —
they don't track each other. For `num1 = 1546854629 * 7283619945`, every
one of the ten rows came back completely unchanged: no row happened to
end in a decimal zero. Checked directly, and it wasn't luck — it's
decided entirely by one number, before a single row gets computed:

    units(num1) coprime to 10  (i.e. units(num1) in {1,3,7,9})
        => the ONLY digit d in {0..9} that can ever put a decimal zero
           on the end of num1*d is d=0 itself.

Because `(num1*d) mod 10 = (units(num1)*d) mod 10`, and when
`units(num1)` is invertible mod 10, that vanishes only at `d≡0`.
`units(1546854629) = 9`, coprime to 10 (`9*9=81≡1`), and `num2`'s digits
never include a `0` — so every row was guaranteed clean in advance. For
`units(num1) ∈ {2,4,6,8}` (shares the factor 2 with 10) or `= 5` (shares
the factor 5) or `= 0` (every row contaminated), more digits — or all of
them — can trigger a trailing zero. Checkable in O(1) off `units(num1)`
alone, no multiplication required, before deciding whether this
operation is even worth running on a given `num1`.

## 5. Status

Sections 2-4: **CALCULATED** — every number here was produced by the
actual code and checked against direct enumeration or a closed-form
identity, not estimated. Section 1 (the basin as a modeling frame, and
`curses_ui.py`'s row-edit mode as a way to drive it): **OPEN** — a tool
for exploring the space by hand, not itself a theorem. The "ping"
(`0 -> p -> q -> N -> q -> p -> 0` as a driven standing wave) and
orthogonal-halves ideas discussed alongside this tool are separate,
earlier-stage, and not yet built here.
