"""
toolsets/treeaut.py -- automorphisms of the depth-n binary tree, and why x -> a x + b on Z/2^n has power-of-two cycles.

The residues mod 2^k form a binary tree of depth n (the parent of a residue mod 2^(k+1) is its residue mod 2^k). Its automorphism group has
order 2^(2^n - 1): at each of the 2^n - 1 internal nodes the two children may be swapped, and these choices are independent (the iterated
wreath product of C2 with itself, the Sylow 2-subgroup of the symmetric group on the 2^n leaves). It is therefore a 2-group, and every
element has power-of-two order, so every cycle of every element has a power-of-two length.

The affine maps x -> a x + b (a odd) on Z/2^n preserve the tree (x mod 2^k determines (a x + b) mod 2^k), so they sit inside that group.
Their own group has order 2^(n-1) * 2^n = 2^(2n-1).

On Z/5^m the same construction is a 5-ary tree whose automorphism group is not a 5-group (each node carries a symmetric group on 5 children; the
order formula is not checked here); the unit group of Z/5^m has order 4 * 5^(m-1), so cycle lengths 4, 20, 100, ... appear (measured below),
not powers of 5.

Checks here: brute-force counting of tree automorphisms for n = 1, 2, 3 (every permutation of the 2^n leaves, tested for tree-preservation),
the recursion |Aut(T_n)| = 2 |Aut(T_{n-1})|^2 for n = 4 by construction, the order of the affine group on Z/2^n by counting distinct maps,
and the affine cycle lengths on Z/2^n and on Z/5^m. stdlib only.
"""
from __future__ import annotations

from itertools import permutations
from typing import Dict, List


def preserves_tree(perm: tuple, n: int) -> bool:
    """A permutation of the 2^n leaves (as positions 0..2^n-1) is a tree automorphism iff it maps every aligned block of size 2^j onto an aligned block."""
    for j in range(1, n):
        size = 1 << j
        for start in range(0, 1 << n, size):
            images = {perm[x] // size for x in range(start, start + size)}
            if len(images) != 1:
                return False
    return True


def automorphism_count_brute(n: int) -> int:
    """Number of permutations of the 2^n leaves preserving the tree (n <= 3: all 40320 permutations for n = 3)."""
    return sum(1 for p in permutations(range(1 << n)) if preserves_tree(p, n))


def automorphism_count_recursive(n: int) -> int:
    """2 * |Aut(T_{n-1})|^2, starting from |Aut(T_0)| = 1: the closed form is 2^(2^n - 1)."""
    return 1 if n == 0 else 2 * automorphism_count_recursive(n - 1) ** 2


def affine_group_order(n: int) -> int:
    """Number of distinct maps x -> a x + b (a odd) on Z/2^n."""
    M = 1 << n
    return len({tuple((a * x + b) % M for x in range(M)) for a in range(1, M, 2) for b in range(M)})


def affine_maps_preserve_tree(n: int) -> bool:
    M = 1 << n
    for a in range(1, M, 2):
        for b in range(M):
            for k in range(1, n):
                m = 1 << k
                if any((a * x + b) % m != (a * (x % m) + b) % m for x in range(M)):
                    return False
    return True


def cycle_lengths(a: int, b: int, m: int) -> List[int]:
    seen, out = bytearray(m), []
    for s in range(m):
        if not seen[s]:
            n, x = 0, s
            while not seen[x]:
                seen[x] = 1
                x = (a * x + b) % m
                n += 1
            out.append(n)
    return sorted(set(out))


def self_check() -> Dict[str, object]:
    brute = {n: automorphism_count_brute(n) for n in (1, 2, 3)}
    return {"brute_force": brute, "formula_2^(2^n-1)": {n: 2 ** (2 ** n - 1) for n in (1, 2, 3, 4)},
            "recursion": {n: automorphism_count_recursive(n) for n in (1, 2, 3, 4)},
            "brute_equals_formula": all(brute[n] == 2 ** (2 ** n - 1) for n in brute),
            "affine_group_order_2^(2n-1)": {n: (affine_group_order(n), 2 ** (2 * n - 1)) for n in (2, 3, 4, 5, 6)},
            "affine_maps_preserve_tree": all(affine_maps_preserve_tree(n) for n in (3, 4, 5)),
            "all_affine_cycle_lengths_powers_of_two_Z2^8": all(l & (l - 1) == 0 for a in range(1, 256, 2) for b in range(0, 256, 17) for l in cycle_lengths(a, b, 256)),
            "Z5^m_cycle_lengths_of_x->2x+1": {m: cycle_lengths(2, 1, 5 ** m) for m in (1, 2, 3, 4)}}


if __name__ == "__main__":
    for k, v in self_check().items():
        print(f"{k}: {v}")
