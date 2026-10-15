# The Toolbox — Multiplication Matrix Explorer

One page per toolset in `toolsets/`: API-style (functions, parameters, returns, a run), no narrative. The math behind the core is in
[../core_functionality.md](../core_functionality.md) and [../addition_matrix_basin.md](../addition_matrix_basin.md).

> **Protocol.** Adding a toolset means adding its page and its row here, then re-checking the whole table is current before calling the
> update done. Each toolset is stdlib-only, exact, and has a `self_check()`; `tests/test_toolsets.py` runs them.

| Page | Toolset | What it is | Added |
|---|---|---|---|
| [01_law.md](01_law.md) | `toolsets/law.py` | closed-form count of the factor search's live states, unit-group torsors, the K = 0 address, the factor-panel lines | 2026-10-14 |
| [02_torsor.md](02_torsor.md) | `toolsets/torsor.py` | the solution tree: uniform 10-ary branching, guide rank tests, exact pruning counts | 2026-10-14 |
| [03_treeaut.md](03_treeaut.md) | `toolsets/treeaut.py` | automorphisms of the depth-n binary tree; why x → a·x + b on ℤ/2ⁿ has power-of-two cycles | 2026-10-14 |
| [04_closedform.md](04_closedform.md) | `toolsets/closedform.py` | the closed form for solutions of a·b ≡ N mod pᵏ, checked for every N and several primes | 2026-10-14 |

Engine counterpart: `ValaQuenta/modules/addition_matrix/` (core: matrix, rotors, law, address). Paper: `FourthAgePapers/AdditionMatrixOrbits/`.
