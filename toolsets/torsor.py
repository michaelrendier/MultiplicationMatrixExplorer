"""
toolsets/torsor.py -- walking down the solution tree: does anything in the tree point at the true path?

For N coprime to 10, the unit solutions (p', q') mod 10^k with p'q' = N form a uniformly 10-ary tree (every solution mod 10^k has exactly
ten lifts mod 10^(k+1), four roots at k = 1). The true factorisation is one root-to-leaf path. Reconstructing the factors "by walking the
tree" needs something at a node that prefers the true child among its ten siblings. This toolset measures candidate guides:

    overflow   |K_k| with K_k = (p'q' - N) / 10^k, the carry out of the top of k columns (smaller = better)
    size       p'q' closest to N from below (the archimedean bound p'q' <= N that the true path obeys at every level)
    low        smallest p' (a control with no relation to the truth)

and, for each guide, the normalised rank of the true child among its siblings (0 = ranked first, ~0.5 = no information), over many
products of two n-digit primes, with a random-child control. It also counts how many nodes the exact pruning p'q' <= N removes.

Everything is exact integer arithmetic; ranks use average rank for ties. This is a test of guides, not a factoring method.
stdlib only.
"""
from __future__ import annotations

import random
import statistics
from math import gcd, sqrt
from typing import Dict, List, Tuple

try:
    from .law import unit_solutions
except ImportError:          # run as a script
    from law import unit_solutions


def primes_between(lo: int, hi: int) -> List[int]:
    return [x for x in range(lo, hi) if all(x % d for d in range(2, int(x ** .5) + 1))]


def children(N: int, k: int) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """Map each unit solution mod 10^k to its lifts mod 10^(k+1)."""
    M = 10 ** k
    out: Dict[Tuple[int, int], List[Tuple[int, int]]] = {(p, q): [] for p, q, _ in unit_solutions(N, k)}
    for p, q, _ in unit_solutions(N, k + 1):
        out[(p % M, q % M)].append((p, q))
    return out


def branching(N: int, k: int) -> Dict[int, int]:
    """{children: parents}: uniformly 10 when the tree is uniformly 10-ary."""
    out: Dict[int, int] = {}
    for kids in children(N, k).values():
        out[len(kids)] = out.get(len(kids), 0) + 1
    return out


def _avg_rank(values: List[float], target: float) -> float:
    """Normalised average rank of `target` among `values` (0 = smallest), ties averaged; 1 value gives 0.5."""
    less = sum(v < target for v in values)
    eq = sum(v == target for v in values)
    n = len(values)
    return ((less + (eq - 1) / 2) / (n - 1)) if n > 1 else 0.5


GUIDES = {
    "overflow": lambda N, k, p, q: abs((p * q - N) // 10 ** k),
    "size": lambda N, k, p, q: N - p * q if p * q <= N else 10 ** 60,   # closest from below
    "low": lambda N, k, p, q: p,
}


def rank_test(n_digits: int, level: int, trials: int = 100, seed: int = 0) -> Dict[str, object]:
    """Rank of the true child among its siblings at tree level `level` (child modulus 10^level), for each guide.

    Products of two distinct n-digit primes; `level` runs 2..n (level 1 has four roots, no parent). Returns the mean normalised rank
    per guide, a z-score against the no-information mean 1/2 (sd sqrt(1/12/trials)), and the same for a uniformly random child.
    """
    rng = random.Random(seed)
    P = primes_between(10 ** (n_digits - 1) + 1, 10 ** n_digits)
    P = [x for x in P if gcd(x, 10) == 1]
    ranks = {g: [] for g in GUIDES}
    ranks["random child"] = []
    for _ in range(trials):
        p, q = rng.sample(P, 2)
        N = p * q
        M = 10 ** level
        parent = (p % (M // 10), q % (M // 10))
        sibs = children(N, level - 1)[parent]
        true = (p % M, q % M)
        for g, f in GUIDES.items():
            vals = [f(N, level, a, b) for a, b in sibs]
            ranks[g].append(_avg_rank(vals, f(N, level, *true)))
        ranks["random child"].append(_avg_rank(list(range(len(sibs))), rng.randrange(len(sibs))))
    sd = sqrt(1 / 12 / trials)
    return {"n_digits": n_digits, "level": level, "trials": trials,
            "mean_rank": {g: statistics.mean(v) for g, v in ranks.items()},
            "z_vs_no_information": {g: (statistics.mean(v) - 0.5) / sd for g, v in ranks.items()}}


def pruning(N: int, n_digits: int) -> List[Tuple[int, int, int]]:
    """Per level k: (k, solutions, solutions with p'q' <= N): how much the exact bound removes."""
    return [(k, len(s), sum(1 for p, q, _ in s if p * q <= N)) for k in range(1, n_digits + 1) for s in [unit_solutions(N, k)]]


def self_check() -> dict:
    N = 14351
    return {"branching_k1": branching(N, 1), "branching_k2": branching(N, 2),
            "pruning_N14351": pruning(N, 3)}


if __name__ == "__main__":
    print(self_check())
