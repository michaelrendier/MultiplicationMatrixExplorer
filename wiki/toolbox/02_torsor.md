# `toolsets/torsor.py` — the solution tree and its guides

**Import:** `from toolsets.torsor import branching, rank_test, pruning` · stdlib only (imports `toolsets.law`).

| Function | Parameters | Returns |
|---|---|---|
| `children(N, k)` | target coprime to 10, exponent | `{(p, q) mod 10ᵏ: [lifts mod 10^(k+1)]}` |
| `branching(N, k)` | same | `{children: parents}`; `{10: 4} at k = 1` when uniformly 10-ary |
| `rank_test(n_digits, level, trials=100, seed=0)` | digits per prime, child modulus 10^level (2..n), trials, seed | mean normalised rank of the true child among its siblings for guides `overflow`, `size`, `low` and a `random child` control, with z-scores against 0.5 (0 = ranked first) |
| `pruning(N, n_digits)` | target, digits | per level `(k, solutions, solutions with p'q' ≤ N)` |
| `self_check()` | — | branching at k = 1, 2 and pruning for N = 14351 |
| `GUIDES` | — | the guide functions `f(N, k, p, q)` (smaller = better) |

```
>>> branching(14351, 2)
{10: 40}
>>> pruning(14351, 3)
[(1, 4, 4), (2, 40, 40), (3, 400, 26)]
>>> rank_test(4, 2, trials=100, seed=1)['z_vs_no_information']['overflow']      # near 0: no information
>>> rank_test(3, 3, trials=40, seed=1)['mean_rank']['overflow']                  # ~0: the K = 0 address, trivial at the last level
```

Guides `overflow` and `size` give identical rankings (both are the distance from p'q' to N). A test of guides, not a factoring method. The runs, including the two borderline cells that were chased, are in `ContextPlease/claude/scratchpad/2026-10-14_addition_matrix_followups/`.
