# `toolsets/law.py` — the law of the factor search, and the address

**Import:** `from toolsets.law import solution_count, address_profile, law_lines` · stdlib only · mirrors `ValaQuenta/modules/addition_matrix/maths.py` (a test compares them).

| Function | Parameters | Returns |
|---|---|---|
| `valuation(N, p, cap=None)` | integer, prime, optional cap | exponent of `p` in `N` (`N = 0` returns `cap`) |
| `phi_prime_power(p, k)` | prime, exponent | φ(pᵏ) |
| `prime_power_solutions(N, p, k)` | target, prime, exponent | #{(a, b) mod pᵏ : ab = N}: (v+1)φ(pᵏ) if v < k, else kφ(pᵏ) + pᵏ |
| `solution_count(N, k)` | target, exponent | the count mod 10ᵏ: product over p = 2, 5 |
| `unit_group_order(k)` | exponent | 4·10^(k−1) |
| `torsor_orbits(N, k)` | target, exponent | (v₂+1)(v₅+1), or `None` when a valuation ≥ k |
| `unit_solutions(N, n)` | target coprime to 10, exponent | list of `(p', q', K)` over all unit solutions mod 10ⁿ, K = (p'q' − N)/10ⁿ; raises `ValueError` otherwise |
| `address_profile(N, n)` | same | dict: solutions, zero_overflow, smallest/median nonzero K, largest K, the K = 0 pairs |
| `law_lines(N, n_digits, peaks)` | target, digit count, `{n: peak}` | text lines for the explorer's factor panel |
| `self_check()` | — | closed form vs enumeration (N < 2·10ᵏ+50, k ≤ 3) and the K = 0 pair for 101·103 |

```
>>> [solution_count(14351, c + 1) for c in range(3)]
[4, 40, 400]
>>> solution_count(420, 2), torsor_orbits(420, 3)
(320, 6)
>>> address_profile(101 * 103, 3)['zero_overflow_pairs']
[(101, 103), (103, 101)]
>>> self_check()
{'closed_form_mismatches': 0, 'pair_at_K0': True}
```

The address panel is computed only up to `ADDRESS_MAX_DIGITS = 6` digits (4·10⁵ solutions). The address is unique among zero-overflow solutions and **not isolated**.
