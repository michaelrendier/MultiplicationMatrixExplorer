# `toolsets/closedform.py` — the closed form, checked for every N

**Import:** `from toolsets.closedform import check_prime_power, check_ten` · stdlib only (imports `toolsets.law`).

| Function | Parameters | Returns |
|---|---|---|
| `brute(N, M)` | target, modulus | pairs (a, b) mod M with ab = N, by summing gcd(a, M) over the a for which it divides N mod M |
| `check_prime_power(p, k)` | prime, exponent | number of residues N mod pᵏ whose closed form differs from enumeration (0 = holds for every N) |
| `check_ten(k, sample=None)` | exponent, optional list of N | the same modulo 10ᵏ (every N when no sample) |
| `self_check()` | — | p = 2 (k ≤ 10), 3 (k ≤ 6), 5 (k ≤ 4), 7 (k ≤ 3), 11 (k ≤ 2); 10ᵏ for k ≤ 3 every N and k = 4, 5 for ten chosen N |

```
>>> check_prime_power(2, 10), check_prime_power(5, 4), check_prime_power(11, 2)
(0, 0, 0)
>>> self_check()['all_prime_power_ok']
True
```

The docstring carries the derivation (split a by its valuation; each i ≤ min(v, k−1) contributes φ(pᵏ) pairs; a = 0 contributes pᵏ more when N ≡ 0). The code is the check, not a proof.
