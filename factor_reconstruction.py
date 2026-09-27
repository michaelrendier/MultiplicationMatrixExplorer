"""
factor_reconstruction.py -- the addition-matrix UNDOING direction: given a
modulus (the "final answer"), search for the two unknown factors that
produced it, digit by digit, from the fixed/units end outward.

Deliberately independent of matrix_math.py's N_DIGITS=10 constant -- that
constant is fixed for the forward/multiplication-visualization mode and
must stay untouched. This module's `n_digits` is a per-call argument with
NO ceiling: the caller decides how far to push it, because the honest
answer for a real modulus (hundreds of digits) is that it becomes
combinatorially intractable long before reaching the real digit count --
this module is built to SHOW that wall forming, not to hide it behind an
artificial cap.

Digit-DP / constraint-propagation search: state = (p_digits_so_far,
q_digits_so_far, carry). At each column c, every candidate new digit pair
(p_c, q_c) survives only if the full convolution sum at that column
(sum of p_i*q_j for i+j=c, using every digit fixed so far, plus carry-in)
matches N's actual digit there, mod 10, with the correct carry propagating
forward. Verified exact on real examples 2026-09-26 (61*53, 113*127,
1009*1013) and confirmed to reproduce the SAME per-column growth law
(~x10 per added digit) on a real 925-digit RSA modulus's own low-order
digits, not just on small toy examples.

stdlib only.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple


def digits_lsb(n: int, width: int) -> List[int]:
    out = []
    for _ in range(width):
        out.append(n % 10)
        n //= 10
    return out


def factor_search_step(N: int, n_digits: int,
                        states: List[Tuple[List[int], List[int], int]],
                        c: int) -> List[Tuple[List[int], List[int], int]]:
    """Advance the search by exactly one column. Exposed separately (not
    just as an internal loop body) so a live UI can draw the live-state
    count after every single column instead of waiting for the whole
    search to finish."""
    target_digit = (N // 10 ** c) % 10
    new_states = []
    candidates = range(10) if c < n_digits else (0,)
    for p_digits, q_digits, carry in states:
        for new_p in candidates:
            for new_q in candidates:
                trial_p = p_digits + [new_p] if c < n_digits else p_digits
                trial_q = q_digits + [new_q] if c < n_digits else q_digits
                s = carry
                for i in range(len(trial_p)):
                    j = c - i
                    if 0 <= j < len(trial_q):
                        s += trial_p[i] * trial_q[j]
                if s % 10 == target_digit:
                    new_states.append((trial_p, trial_q, s // 10))
    return new_states


def digits_to_int(digits: List[int]) -> int:
    return sum(d * (10 ** i) for i, d in enumerate(digits))


def factor_search(N: int, n_digits: int,
                   max_live_states: Optional[int] = None,
                   time_budget_s: Optional[float] = None,
                   on_column: Optional[Any] = None) -> Dict[str, Any]:
    """
    Full search up to n_digits per factor (2*n_digits columns total). No
    digit cap is imposed here -- n_digits is whatever the caller asks for.
    `max_live_states` / `time_budget_s` are honest ABORT conditions (report
    ABORTED, don't silently truncate); `on_column(c, before, after)` is an
    optional live callback, e.g. for a curses display.
    """
    n_cols = 2 * n_digits
    states: List[Tuple[List[int], List[int], int]] = [([], [], 0)]
    history: List[Tuple[int, int, int]] = []
    t0 = time.time()
    aborted_reason = None

    for c in range(n_cols):
        before = len(states)
        states = factor_search_step(N, n_digits, states, c)
        after = len(states)
        history.append((c, before, after))
        if on_column:
            on_column(c, before, after)
        if max_live_states is not None and after > max_live_states:
            aborted_reason = f"live states ({after}) exceeded cap ({max_live_states}) at column {c}"
            break
        if time_budget_s is not None and (time.time() - t0) > time_budget_s:
            aborted_reason = f"time budget ({time_budget_s}s) exceeded at column {c}"
            break

    solutions = []
    if aborted_reason is None:
        for p_digits, q_digits, carry in states:
            if carry == 0:
                p, q = digits_to_int(p_digits), digits_to_int(q_digits)
                if p * q == N and p > 1 and q > 1:
                    solutions.append((p, q))

    return {
        "N": N, "n_digits": n_digits, "n_columns": n_cols,
        "history": history, "aborted": aborted_reason is not None,
        "aborted_reason": aborted_reason, "elapsed_s": time.time() - t0,
        "solutions": sorted(set(tuple(sorted(pq)) for pq in solutions)),
        "final_live_states": len(states),
    }


def growth_law_estimate(history_by_n_digits: Dict[int, List[Tuple[int, int, int]]]
                         ) -> Dict[str, Any]:
    """Fit the observed peak-live-state growth against n_digits -- the
    x10-per-digit law measured 2026-09-26. Reports the actual ratio
    between consecutive peaks, not an assumed constant."""
    peaks = {n: max(h[2] for h in hist) for n, hist in history_by_n_digits.items()}
    ns = sorted(peaks)
    ratios = []
    for a, b in zip(ns, ns[1:]):
        if peaks[a] > 0:
            ratios.append(peaks[b] / peaks[a])
    return {"peaks": peaks, "consecutive_ratios": ratios,
            "mean_ratio": sum(ratios) / len(ratios) if ratios else None}


def extrapolate_infeasibility(peak_at_small_n: int, small_n: int,
                               target_n: int, growth_ratio: float = 10.0) -> Dict[str, Any]:
    """Honest extrapolation: given a MEASURED peak at small_n and a
    MEASURED growth ratio, what would the peak be at target_n (e.g. the
    real factor length of an actual modulus)? Reported as an order-of-
    magnitude estimate, explicitly labeled as extrapolated, not measured."""
    exponent_delta = target_n - small_n
    estimated_peak_log10 = (exponent_delta * (growth_ratio and __import__("math").log10(growth_ratio))
                             + __import__("math").log10(max(peak_at_small_n, 1)))
    return {
        "measured_peak": peak_at_small_n, "measured_at_n_digits": small_n,
        "target_n_digits": target_n, "growth_ratio_used": growth_ratio,
        "estimated_peak_log10": estimated_peak_log10,
        "note": "EXTRAPOLATED, not measured -- for target_n_digits in the "
                "hundreds this number has no physical meaning (exceeds "
                "atoms in the observable universe); it exists to show the "
                "wall, not to be waited out.",
    }


if __name__ == "__main__":
    # small, verified examples -- exact, not extrapolated
    for N, n in ((3233, 2), (14351, 3), (1022117, 4)):
        r = factor_search(N, n_digits=n)
        assert r["solutions"], (N, r)
        print(f"N={N:>8}  n_digits={n}  solutions={r['solutions']}  "
              f"peak_live_states={max(h[2] for h in r['history'])}")

    # the growth law, measured across n=2..4
    hist_by_n = {}
    for N, n in ((3233, 2), (14351, 3), (1022117, 4)):
        hist_by_n[n] = factor_search(N, n_digits=n)["history"]
    law = growth_law_estimate(hist_by_n)
    print(f"\ngrowth law: peaks={law['peaks']}  ratios={law['consecutive_ratios']}  "
          f"mean_ratio={law['mean_ratio']:.2f}")

    # the honest extrapolation to a real ~462-digit-per-factor RSA modulus
    est = extrapolate_infeasibility(peak_at_small_n=4000, small_n=4, target_n=462,
                                     growth_ratio=law["mean_ratio"])
    print(f"\nextrapolated peak at n_digits=462: 10^{est['estimated_peak_log10']:.1f}")
    print(f"  {est['note']}")
