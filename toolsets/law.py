"""
toolsets/law.py -- the law of the factor search, and the address of the final answer.

Digit-by-digit factor reconstruction (factor_reconstruction.py) keeps exactly the pairs
(p, q) mod 10^(c+1) with p*q = N there. The number of such pairs is a product over the
primes 2 and 5 (Chinese remainder theorem):

    f_p(N, k) = (v + 1) * phi(p^k)              if v = v_p(N) < k
    f_p(N, k) = k * phi(p^k) + p^k              if N = 0 mod p^k
    count(N, k) = f_2(N, k) * f_5(N, k)

For v2, v5 < k this is (v2+1)(v5+1) * 4 * 10^(k-1): (v2+1)(v5+1) torsors of the unit group
(Z/10^k)^x, which has order 4 * 10^(k-1). That is the x10 per digit measured on the search.

Address: for a unit solution p' mod 10^n, q' = N / p' mod 10^n and K = (p'q' - N) / 10^n is an
integer; the true factorisation into two n-digit numbers is exactly K = 0. The address is
unique among zero-overflow solutions and is NOT isolated: other solutions have small |K|.

This is not a factoring method; the counts are the cost of the search it describes.
Mirrors ValaQuenta/modules/addition_matrix/maths.py (the engine); tests cross-check the two.
stdlib only.
"""
from __future__ import annotations

import statistics
from math import gcd
from typing import Dict, List, Optional, Tuple


def valuation(N: int, p: int, cap: Optional[int] = None) -> int:
    """Exponent of prime p in N; N = 0 returns cap."""
    if N == 0:
        return cap if cap is not None else 10 ** 9
    v = 0
    while N % p == 0 and (cap is None or v < cap):
        N //= p
        v += 1
    return v


def phi_prime_power(p: int, k: int) -> int:
    return p ** (k - 1) * (p - 1)


def prime_power_solutions(N: int, p: int, k: int) -> int:
    v = valuation(N, p, cap=k)
    return (v + 1) * phi_prime_power(p, k) if v < k else k * phi_prime_power(p, k) + p ** k


def solution_count(N: int, k: int) -> int:
    """#{(p, q) mod 10^k : p*q = N mod 10^k}, closed form."""
    return prime_power_solutions(N, 2, k) * prime_power_solutions(N, 5, k)


def unit_group_order(k: int) -> int:
    return phi_prime_power(2, k) * phi_prime_power(5, k)


def torsor_orbits(N: int, k: int) -> Optional[int]:
    v2, v5 = valuation(N, 2, cap=k), valuation(N, 5, cap=k)
    return None if (v2 >= k or v5 >= k) else (v2 + 1) * (v5 + 1)


def unit_solutions(N: int, n: int) -> List[Tuple[int, int, int]]:
    """Every unit pair (p', q') mod 10^n with p'q' = N there, with overflow K. Needs gcd(N, 10) = 1."""
    M = 10 ** n
    if gcd(N, 10) != 1:
        raise ValueError("unit_solutions needs N coprime to 10")
    out = []
    for p in range(1, M):
        if gcd(p, 10) != 1:
            continue
        q = (N * pow(p, -1, M)) % M
        out.append((p, q, (p * q - N) // M))
    return out


def address_profile(N: int, n: int) -> Dict[str, object]:
    sols = unit_solutions(N, n)
    ks = [abs(k) for _, _, k in sols]
    nz = sorted(k for k in ks if k)
    return {"n": n, "solutions": len(sols), "zero_overflow": ks.count(0),
            "smallest_nonzero_K": nz[0] if nz else None,
            "median_nonzero_K": statistics.median(nz) if nz else None,
            "largest_K": max(ks), "zero_overflow_pairs": sorted((p, q) for p, q, k in sols if k == 0)}


ADDRESS_MAX_DIGITS = 6   # 4 * 10^5 solutions: fast; beyond this the panel says so instead of waiting


def law_lines(N: int, n_digits: int, peaks: Dict[int, int]) -> List[str]:
    """Text lines for the explorer's factor panel: the closed-form count against the measured peak, and the address."""
    lines = []
    v2, v5 = valuation(N, 2, cap=n_digits), valuation(N, 5, cap=n_digits)
    lines.append(f"law: v2(N)={valuation(N, 2)}  v5(N)={valuation(N, 5)}  unit group of Z/10^k has order 4*10^(k-1)")
    for n in sorted(peaks):
        cf = solution_count(N, n)
        lines.append(f"  n_digits={n}: closed form at column n-1 = {cf}   measured peak = {peaks[n]}")
    if gcd(N, 10) == 1 and n_digits <= ADDRESS_MAX_DIGITS:
        pr = address_profile(N, n_digits)
        lines.append(f"address (n={n_digits}): {pr['solutions']} unit solutions, K=0 for {pr['zero_overflow']} "
                     f"(smallest nonzero |K| = {pr['smallest_nonzero_K']}): unique but not isolated")
    elif gcd(N, 10) != 1:
        lines.append("address: N shares a factor with 10, the unit-solution address is not defined here")
    else:
        lines.append(f"address: skipped above {ADDRESS_MAX_DIGITS} digits (4*10^(n-1) solutions)")
    return lines


def self_check() -> dict:
    """Closed form against enumeration for N in [0, 2*10^k + 50), k = 1..3, and the K = 0 pair for 101*103."""
    def brute(N, k):
        M = 10 ** k
        return sum(gcd(a, M) for a in range(M) if (N % M) % gcd(a, M) == 0)
    bad = [(N, k) for k in (1, 2, 3) for N in range(0, 2 * 10 ** k + 50) if solution_count(N, k) != brute(N, k)]
    pr = address_profile(101 * 103, 3)
    return {"closed_form_mismatches": len(bad), "pair_at_K0": pr["zero_overflow_pairs"] == [(101, 103), (103, 101)]}


if __name__ == "__main__":
    print(self_check())
