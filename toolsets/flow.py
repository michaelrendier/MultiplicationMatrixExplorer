"""
toolsets/flow.py -- the discrete-time piece of matrix-flow analysis: the order (the "circle number") of an integer 2x2 matrix mod m,
and which KIND of circle it is, read from the discriminant.

A continuous planar flow dx/dt = Ax is classified by the eigenvalues of A (GenerationalLineage `matrix_flow`: elliptic = round circle,
hyperbolic = boost, parabolic = shear). The explorer lives in the discrete, modular world, where the same three kinds appear as the
discriminant D = tr^2 - 4 det of A over F_p:

    D a non-zero square mod p   hyperbolic  eigenvalues in F_p,    order divides p - 1
    D a non-square mod p        elliptic    eigenvalues in F_p^2,   A^(p+1) is the scalar det(A),  order divides 2(p + 1)
    D = 0 mod p                 parabolic   repeated eigenvalue,    order = p * ord(lambda) for a non-scalar A (a shear on top of a scale)

Everything here is exact integer arithmetic. The worked case is the Fibonacci matrix [[1,1],[1,0]], whose order mod m is the Pisano period;
mod 10^k the orbit length is 60, 300, then 15*10^(k-1) for k >= 3 (1500, 15000). The same order is the cycle length of a digit stream, which is the
periodicity the addition matrix shows under single-digit incrementing. stdlib only.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

Mat = Tuple[Tuple[int, int], Tuple[int, int]]
FIB: Mat = ((1, 1), (1, 0))


def mul(A: Mat, B: Mat, m: int) -> Mat:
    return (((A[0][0] * B[0][0] + A[0][1] * B[1][0]) % m, (A[0][0] * B[0][1] + A[0][1] * B[1][1]) % m),
            ((A[1][0] * B[0][0] + A[1][1] * B[1][0]) % m, (A[1][0] * B[0][1] + A[1][1] * B[1][1]) % m))


def order_mod(A: Mat, m: int, limit: int = 10 ** 6) -> Optional[int]:
    """Least n >= 1 with A^n = I mod m; None if A is singular mod m (no inverse) or the order exceeds `limit` (reported, not guessed)."""
    from math import gcd
    if gcd(A[0][0] * A[1][1] - A[0][1] * A[1][0], m) != 1:
        return None
    I = ((1 % m, 0), (0, 1 % m))
    P = tuple(tuple(x % m for x in row) for row in A)
    for n in range(1, limit + 1):
        if P == I:
            return n
        P = mul(P, A, m)
    return None


def kind_mod_p(A: Mat, p: int) -> str:
    """'hyperbolic' | 'elliptic' | 'parabolic' for an odd prime p, from the discriminant."""
    D = ((A[0][0] + A[1][1]) ** 2 - 4 * (A[0][0] * A[1][1] - A[0][1] * A[1][0])) % p
    if D == 0:
        return "parabolic"
    return "hyperbolic" if pow(D, (p - 1) // 2, p) == 1 else "elliptic"


def shift_nilpotency(n: int) -> int:
    """The n-column digit shift (multiply by 10) is nilpotent: N^n = 0, index exactly n. The ADD generator of the explorer's own grid."""
    N = [[1 if j == i + 1 else 0 for j in range(n)] for i in range(n)]
    P = [row[:] for row in N]
    for k in range(1, n + 1):
        if all(v == 0 for row in P for v in row):
            return k
        P = [[sum(P[i][t] * N[t][j] for t in range(n)) for j in range(n)] for i in range(n)]
    return -1


def self_check() -> Dict[str, object]:
    pisano = {m: order_mod(FIB, m) for m in (10, 100, 1000, 10000)}
    odd_primes = [p for p in range(3, 400) if all(p % d for d in range(2, int(p ** .5) + 1))]
    bound_ok = True
    kinds = {"hyperbolic": 0, "elliptic": 0, "parabolic": 0}
    for p in odd_primes:
        o, k = order_mod(FIB, p), kind_mod_p(FIB, p)
        kinds[k] += 1
        bound_ok &= ((p - 1) % o == 0) if k == "hyperbolic" else (2 * (p + 1)) % o == 0 if k == "elliptic" else o % p == 0
    return {"pisano_10^k": pisano, "pisano_matches_15*10^(k-1)_from_k=3": pisano[1000] == 1500 and pisano[10000] == 15000,
            "pisano_10_100": (pisano[10], pisano[100]) == (60, 300),
            "order_divides_bound_for_every_odd_prime_below_400": bound_ok, "kind_counts": kinds,
            "singular_mod_m_is_None": order_mod(((2, 0), (0, 1)), 10) is None,
            "shift_nilpotency_20": shift_nilpotency(20) == 20}


if __name__ == "__main__":
    for k, v in self_check().items():
        print(f"{k}: {v}")
