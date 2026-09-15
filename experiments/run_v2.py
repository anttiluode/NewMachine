from __future__ import annotations

import json
import numpy as np

from new_machine.core import TwoGateUnit, signed_control
from new_machine.task import make_complementary_stream, recovery_error, recovery_hold_mask

ALPHA = 0.88
THETA0 = 0.54
SLOPE_GAIN = 0.75
HYBRID_HIDE_STRENGTH = 0.16
HYBRID_RESET_STRENGTH = 0.08
HOLD_HORIZON = 8
TEST_SEEDS = tuple(range(200, 212))
STEPS = 1400
CHANDELIER_SWEEP = (0.0, 0.03, 0.06, 0.09, 0.12, 0.16, 0.20, 0.30, 0.40, 0.50)


def _signed_equivalence(seed: int):
    _clean, observed, hide, reset = make_complementary_stream(seed=seed, steps=STEPS)
    direct = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)
    signed = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)

    max_state_difference = 0.0
    max_threshold_difference = 0.0
    event_mismatch_count = 0

    for t in range(STEPS):
        direct_out = direct.step(
            float(observed[t]),
            basket=HYBRID_RESET_STRENGTH if reset[t] else 0.0,
            chandelier=HYBRID_HIDE_STRENGTH if hide[t] else 0.0,
        )
        q = (
            HYBRID_HIDE_STRENGTH
            if hide[t]
            else (-HYBRID_RESET_STRENGTH if reset[t] else 0.0)
        )
        basket, chandelier = signed_control(q)
        signed_out = signed.step(float(observed[t]), basket=basket, chandelier=chandelier)

        max_state_difference = max(
            max_state_difference, abs(direct_out.state - signed_out.state)
        )
        max_threshold_difference = max(
            max_threshold_difference, abs(direct_out.threshold - signed_out.threshold)
        )
        event_mismatch_count += int(direct_out.event != signed_out.event)

    return {
        "max_state_difference": float(max_state_difference),
        "max_threshold_difference": float(max_threshold_difference),
        "event_mismatch_count": int(event_mismatch_count),
    }


def _simultaneous_reset(seed: int, chandelier_strength: float):
    clean, observed, _hide, reset = make_complementary_stream(seed=seed, steps=STEPS)
    hold = recovery_hold_mask(reset, horizon=HOLD_HORIZON)
    exposure = reset | hold

    reference = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)
    basket_only = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)
    both = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)

    ref_states = np.empty(STEPS)
    basket_states = np.empty(STEPS)
    both_states = np.empty(STEPS)
    ref_events = np.zeros(STEPS, dtype=bool)
    both_events = np.zeros(STEPS, dtype=bool)

    for t in range(STEPS):
        ref_out = reference.step(float(clean[t]))
        basket = HYBRID_RESET_STRENGTH if reset[t] else 0.0
        basket_out = basket_only.step(float(observed[t]), basket=basket)
        both_out = both.step(
            float(observed[t]),
            basket=basket,
            chandelier=(chandelier_strength if exposure[t] else 0.0),
        )

        ref_states[t] = ref_out.state
        basket_states[t] = basket_out.state
        both_states[t] = both_out.state
        ref_events[t] = ref_out.event
        both_events[t] = both_out.event

    return {
        "max_state_difference_vs_basket": float(
            np.max(np.abs(both_states - basket_states))
        ),
        "reset_recovery_error": float(
            recovery_error(ref_states, both_states, reset, horizon=10)
        ),
        "exposure_event_fraction": float(both_events[exposure].mean()),
        "clean_event_mismatch_fraction": float(
            np.mean(both_events[exposure] != ref_events[exposure])
        ),
        "hold_event_fraction": float(both_events[hold].mean()),
        "hold_clean_event_mismatch_fraction": float(
            np.mean(both_events[hold] != ref_events[hold])
        ),
    }


def _mean_simultaneous(chandelier_strength: float):
    rows = [
        _simultaneous_reset(seed, chandelier_strength)
        for seed in TEST_SEEDS
    ]
    return {
        key: float(np.mean([row[key] for row in rows]))
        for key in rows[0]
    }


def run_v2():
    signed_rows = [_signed_equivalence(seed) for seed in TEST_SEEDS]
    signed_result = {
        "max_state_difference": float(
            max(row["max_state_difference"] for row in signed_rows)
        ),
        "max_threshold_difference": float(
            max(row["max_threshold_difference"] for row in signed_rows)
        ),
        "event_mismatch_count": int(
            sum(row["event_mismatch_count"] for row in signed_rows)
        ),
    }

    sweep = []
    for chandelier_strength in CHANDELIER_SWEEP:
        metrics = _mean_simultaneous(chandelier_strength)
        metrics["chandelier_strength"] = float(chandelier_strength)
        sweep.append(metrics)

    baseline = sweep[0]
    free_win = any(
        row["chandelier_strength"] > 0.0
        and row["exposure_event_fraction"] < baseline["exposure_event_fraction"]
        and row["clean_event_mismatch_fraction"] <= baseline["clean_event_mismatch_fraction"]
        + 1e-15
        for row in sweep[1:]
    )

    return {
        "test_seeds": list(TEST_SEEDS),
        "hold_horizon": HOLD_HORIZON,
        "signed_scalar_control": signed_result,
        "simultaneous_reset_sweep": sweep,
        "simultaneous_free_win_found": bool(free_win),
    }


if __name__ == "__main__":
    print(json.dumps(run_v2(), indent=2, sort_keys=True))
