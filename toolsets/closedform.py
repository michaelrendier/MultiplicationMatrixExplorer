"""
toolsets/closedform.py -- the closed form for the number of solutions of a*b = N mod p^k, checked exhaustively for any prime power.

    f(N, p, k) = (v + 1) * phi(p^k)            if v = v_p(N) < k           (N a non-zero residue)
    f(N, p, k) = k * phi(p^k) + p^k            if N = 0 mod p^k

Derivation (the part the code does not prove; the counts below are the check). Split a by its valuation i = v_p(a) in 0..k-1: a = p^i * u with u a
unit mod p^(k-i); there are phi(p^(k-i)) such a. The equation p^i * u * b = N mod p^k needs p^i | N (so i <= v) and then fixes b mod p^(k-i),
leaving p^i lifts of b mod p^k. Each i <= min(v, k-1) therefore contributes phi(p^(k-i)) * p^i = phi(p^k) pairs. For v < k, i runs 0..v: (v+1)*phi(p^k).
For N = 0 mod p^k every i in 0..k-1 contributes phi(p^k), and a = 0 contributes p^k pairs (b free): k*phi(p^k) + p^k.
The count mod 10^k is the product over p = 2, 5 (Chinese remainder theorem).

`check_prime_power(p, k)` enumerates every N mod p^k against every a (O(p^(2k))); `check_ten(k)` enumerates N mod 10^k for k <= 3 and a
chosen sample for k = 4, 5. stdlib only.
"""
from __future__ import annotations

from math import gcd
from typing import Dict, List

try:
    from .law import phi_prime_power, prime_power_solutions, solution_count
except ImportError:          # run as a script
    from law import phi_prime_power, prime_power_solutions, solution_count


def brute(N: int, M: int) -> int:
    """Pairs (a, b) mod M with a*b = N mod M: for each a, gcd(a, M) solutions when gcd(a, M) divides N mod M."""
    return sum(gcd(a, M) for a in range(M) if (N % M) % gcd(a, M) == 0)


def check_prime_power(p: int, k: int) -> int:
    """Number of residues N mod p^k whose closed form differs from enumeration (0 = the formula holds for every N)."""
    M = p ** k
    return sum(prime_power_solutions(N, p, k) != brute(N, M) for N in range(M))


def check_ten(k: int, sample: List[int] = None) -> int:
    M = 10 ** k
    Ns = range(M) if sample is None else sample
    return sum(solution_count(N, k) != brute(N, M) for N in Ns)


def self_check() -> Dict[str, object]:
    pp = {(p, k): check_prime_power(p, k) for p, ks in ((2, (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)), (3, (1, 2, 3, 4, 5, 6)), (5, (1, 2, 3, 4)), (7, (1, 2, 3)), (11, (1, 2))) for k in ks}
    pickN = lambda k: [0, 1, 2 ** k, 5 ** k, 2 ** (k - 1) * 5 ** (k - 1), 2 ** k * 5 ** k // 2, 12345 % 10 ** k, 10 ** k - 1, 4000 % 10 ** k, 6250 % 10 ** k]
    return {"prime_power_mismatches (every N)": {f"{p}^{k}": m for (p, k), m in pp.items()},
            "all_prime_power_ok": all(m == 0 for m in pp.values()),
            "ten_k_1_to_3_every_N": {k: check_ten(k) for k in (1, 2, 3)},
            "ten_k_4_5_selected_N": {k: check_ten(k, pickN(k)) for k in (4, 5)}}


if __name__ == "__main__":
    for k, v in self_check().items():
        print(f"{k}: {v}")
