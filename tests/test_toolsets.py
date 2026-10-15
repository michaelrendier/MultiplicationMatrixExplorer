"""Toolset checks: run with `python3 -m pytest tests -q` from the repository root."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from toolsets import closedform, law, torsor, treeaut          # noqa: E402
import factor_reconstruction as fr                              # noqa: E402


def test_law_closed_form_against_enumeration():
    assert law.self_check() == {"closed_form_mismatches": 0, "pair_at_K0": True}


def test_law_matches_the_explorers_own_search():
    for N, n in ((14351, 3), (1022117, 4)):
        hist = [h[2] for h in fr.factor_search(N, n)["history"]]
        assert hist[:n] == [law.solution_count(N, c + 1) for c in range(n)]


def test_law_lines_render():
    lines = law.law_lines(14351, 3, {1: 4, 2: 40, 3: 400})
    assert any("address" in l for l in lines) and any("closed form" in l for l in lines)


def test_closedform_every_prime_power():
    r = closedform.self_check()
    assert r["all_prime_power_ok"] and not any(r["ten_k_1_to_3_every_N"].values()) and not any(r["ten_k_4_5_selected_N"].values())


def test_tree_automorphisms_are_a_two_group():
    r = treeaut.self_check()
    assert r["brute_equals_formula"] and r["affine_maps_preserve_tree"] and r["all_affine_cycle_lengths_powers_of_two_Z2^8"]
    assert all(a == b for a, b in r["affine_group_order_2^(2n-1)"].values())


def test_solution_tree_is_uniformly_ten_ary():
    assert torsor.branching(14351, 1) == {10: 4} and torsor.branching(14351, 2) == {10: 40}


def test_true_child_is_first_at_the_last_level_and_unremarkable_before():
    last = torsor.rank_test(3, 3, trials=40, seed=1)
    assert last["mean_rank"]["overflow"] < 0.01
    early = torsor.rank_test(4, 2, trials=100, seed=1)
    assert abs(early["z_vs_no_information"]["overflow"]) < 3
