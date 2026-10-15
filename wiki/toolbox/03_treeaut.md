# `toolsets/treeaut.py` — automorphisms of the binary tree

**Import:** `from toolsets.treeaut import automorphism_count_brute, affine_group_order, cycle_lengths` · stdlib only.

| Function | Parameters | Returns |
|---|---|---|
| `preserves_tree(perm, n)` | permutation of the 2ⁿ leaves, depth | whether every aligned block maps onto an aligned block |
| `automorphism_count_brute(n)` | depth (n ≤ 3) | number of tree-preserving permutations, by enumerating all of them |
| `automorphism_count_recursive(n)` | depth | 2·|Aut(Tₙ₋₁)|², i.e. 2^(2ⁿ − 1) |
| `affine_group_order(n)` | depth | number of distinct maps x → ax + b (a odd) on ℤ/2ⁿ |
| `affine_maps_preserve_tree(n)` | depth | whether every such map sends residues mod 2ᵏ consistently |
| `cycle_lengths(a, b, m)` | map, modulus | sorted distinct cycle lengths of x → ax + b on ℤ/m |
| `self_check()` | — | all of the above, and the ℤ/5ᵐ cycle lengths of x → 2x + 1 |

```
>>> self_check()['brute_force'], self_check()['recursion']
({1: 2, 2: 8, 3: 128}, {1: 2, 2: 8, 3: 128, 4: 32768})
>>> self_check()['affine_group_order_2^(2n-1)']
{2: (8, 8), 3: (32, 32), 4: (128, 128), 5: (512, 512), 6: (2048, 2048)}
>>> self_check()['Z5^m_cycle_lengths_of_x->2x+1'][4]
[1, 4, 20, 100, 500]
```

The group is a 2-group, so every element has power-of-two order and every cycle a power-of-two length. On ℤ/5ᵐ the unit group has order 4·5^(m−1): lengths 4, 20, 100, … appear.
