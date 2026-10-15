# Core functionality of the Multiplication Matrix Explorer

**Cody Michael Allison** (Michael Rendier) · the.wandering.god@gmail.com ·
[github.com/michaelrendier](https://github.com/michaelrendier) ·
ORCID: [0009-0007-7239-6760](https://orcid.org/0009-0007-7239-6760)

This page names what the explorer does at its core, file by file, and where each part is also an engine
(`ValaQuenta/modules/addition_matrix/`, v1.0). The explorer will keep receiving updates; new analysis goes in
`toolsets/` with a page under `wiki/toolbox/`, and the core below stays small.

## 1. The addition matrix (`matrix_math.py`)

`trace_multiplication(num1, num2)` writes one row per digit of `num2` (row *j* = `num1 × digit_j`, starting at column *j*),
adds the rows one at a time into a running total, and records the carry out of every column. Adding two numbers at a time
keeps every carry in {0, 1}, which is what lets the carry matrix share the addition matrix's colours. The grid has
`N_COLUMNS = N_DIGITS + ROW_WIDTH = 21` columns (the module docstring's "20" counts the product width; the constant is 21).
`verify()` checks every row and the total against Python's `*`.

## 2. The basin and row editing (`curses_ui.py`, `wiki/addition_matrix_basin.md`)

Ten fixed row values `num1 × 0..9`, placed at column offsets; the standard staircase `offset_j = j` is the product, every other
offset vector is a legal operation that is not the product. Row-edit mode (Ctrl+E) drives it by hand. Derivations are in
[addition_matrix_basin.md](addition_matrix_basin.md).

## 3. Factor reconstruction (`factor_reconstruction.py`, Ctrl+F in the viewer)

Given N, search for p, q column by column from the units end; a pair survives only if the column's digit of p·q matches N's.
`factor_search` takes no digit cap; `max_live_states` and `time_budget_s` are honest abort conditions that report ABORTED.
The explorer is built to show the wall forming, not to hide it.

## 4. The law of the search (`toolsets/law.py`, shown in the factor panel)

The live-state count after column *c* is exactly #{(p, q) mod 10^(c+1) : p·q ≡ N}. For N coprime to 10 that is the order of
the unit group, 4·10ᶜ, for every column below the factor length (×10 per added digit: the growth ratio the panel measures);
with 2s and 5s in N it is (v₂+1)(v₅+1) torsors of that group. The panel prints the closed form beside the measured peak, and the
address below.

## 5. The address (`toolsets/law.py`: `unit_solutions`, `address_profile`)

For a unit solution mod 10ⁿ, K = (p′q′ − N)/10ⁿ is an integer; the true factorisation into two n-digit numbers is exactly
K = 0. It is unique among zero-overflow solutions and is **not isolated**: other solutions have |K| as small as 1. Computing it
needs every solution mod 10ⁿ, so the panel computes it up to 6 digits and says so beyond that. The address is not a factoring
method; it names where the answer sits among the survivors.

## What the rotors are

The digit in column *c* of `num1 × num2` is a wheel in `num2` with exact period 10^(c+1)/gcd(num1, 10^(c+1)); the ring ℤ/10ᵏ is
ℤ/2ᵏ × ℤ/5ᵏ, two stacks of wheels; the odometer `x → x + 1` returns on the multiples of 10 to the odometer one scale down.
These are checked in the engine (`modules/addition_matrix`, notebook `01_matrix_and_rotors`).

## Where things are

| Part | Explorer | Engine (`ValaQuenta`) |
|---|---|---|
| matrix, carries | `matrix_math.py` | `matrix_rows`, `carry_matrix` (cross-checked cell for cell) |
| factor search | `factor_reconstruction.py` | `live_state_counts` (cross-checked column by column) |
| law, address | `toolsets/law.py` | `solution_count_closed`, `address_profile` (cross-checked) |
| further tools | `toolsets/`, [wiki/toolbox](toolbox/00_index.md) | — |
