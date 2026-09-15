from __future__ import annotations

import json
import numpy as np

from new_machine.core import TwoGateUnit, signed_control
from new_machine.task import (
    f1_score,
    make_factorized_stream,
    prediction_residuals,
)

ALPHA = 0.88
THETA0 = 0.54
SLOPE_GAIN = 0.75
STATE_REPAIR_STRENGTH = 0.08
PUBLICATION_GATE_STRENGTH = 0.16
TRAIN_SEEDS = tuple(range(20, 30))
TEST_SEEDS = tuple(range(200, 220))
STEPS = 1800
RESIDUAL_THRESHOLDS = tuple(round(0.02 + 0.01 * i, 2) for i in range(49))
POLICIES = (
    "none",
    "innovation_only",
    "context_only",
    "reset_priority_signed",
    "hide_priority_signed",
    "factorized",
)


def _detections(seed: int, threshold: float):
    _clean, observed, _private, corrupt = make_factorized_stream(seed, STEPS)
    residual = prediction_residuals(observed, alpha=ALPHA)
    detected = residual > threshold
    return corrupt, detected


def _select_threshold() -> float:
    best = None
    for threshold in RESIDUAL_THRESHOLDS:
        scores = []
        for seed in TRAIN_SEEDS:
            corrupt, detected = _detections(seed, threshold)
            scores.append(f1_score(corrupt, detected))
        mean_score = float(np.mean(scores))
        candidate = (-mean_score, float(threshold))
        if best is None or candidate < best:
            best = candidate
    return float(best[1])


def _simulate(seed: int, policy: str, threshold: float):
    clean, observed, private, corrupt = make_factorized_stream(seed, STEPS)
    detected = prediction_residuals(observed, alpha=ALPHA) > threshold

    reference = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)
    unit = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)

    ref_states = np.empty(STEPS)
    states = np.empty(STEPS)
    ref_events = np.zeros(STEPS, dtype=bool)
    events = np.zeros(STEPS, dtype=bool)

    for t in range(STEPS):
        ref_out = reference.step(float(clean[t]))
        basket = 0.0
        chandelier = 0.0

        if policy == "innovation_only":
            basket = STATE_REPAIR_STRENGTH if detected[t] else 0.0
        elif policy == "context_only":
            chandelier = PUBLICATION_GATE_STRENGTH if private[t] else 0.0
        elif policy == "reset_priority_signed":
            q = (
                -STATE_REPAIR_STRENGTH
                if detected[t]
                else (PUBLICATION_GATE_STRENGTH if private[t] else 0.0)
            )
            basket, chandelier = signed_control(q)
        elif policy == "hide_priority_signed":
            q = (
                PUBLICATION_GATE_STRENGTH
                if private[t]
                else (-STATE_REPAIR_STRENGTH if detected[t] else 0.0)
            )
            basket, chandelier = signed_control(q)
        elif policy == "factorized":
            basket = STATE_REPAIR_STRENGTH if detected[t] else 0.0
            chandelier = PUBLICATION_GATE_STRENGTH if private[t] else 0.0
        elif policy != "none":
            raise ValueError(f"unknown policy {policy}")

        out = unit.step(
            float(observed[t]),
            basket=basket,
            chandelier=chandelier,
        )
        ref_states[t] = ref_out.state
        states[t] = out.state
        ref_events[t] = ref_out.event
        events[t] = out.event

    public = ~private
    overlap = private & corrupt
    return {
        "state_rmse": float(np.sqrt(np.mean((states - ref_states) ** 2))),
        "private_event_fraction": float(events[private].mean()),
        "public_event_mismatch_fraction": float(
            np.mean(events[public] != ref_events[public])
        ),
        "overlap_event_fraction": float(events[overlap].mean()),
        "overlap_state_abs_error": float(
            np.mean(np.abs(states[overlap] - ref_states[overlap]))
        ),
        "overlap_fraction": float(overlap.mean()),
    }


def _mean_policy(policy: str, threshold: float):
    rows = [_simulate(seed, policy, threshold) for seed in TEST_SEEDS]
    return {
        key: float(np.mean([row[key] for row in rows]))
        for key in rows[0]
    }


def run_v3():
    threshold = _select_threshold()
    detector_scores = []
    for seed in TEST_SEEDS:
        corrupt, detected = _detections(seed, threshold)
        detector_scores.append(f1_score(corrupt, detected))

    policies = {
        policy: _mean_policy(policy, threshold)
        for policy in POLICIES
    }

    factorized = policies["factorized"]
    reset_priority = policies["reset_priority_signed"]
    state_equal = abs(factorized["state_rmse"] - reset_priority["state_rmse"])
    public_equal = abs(
        factorized["public_event_mismatch_fraction"]
        - reset_priority["public_event_mismatch_fraction"]
    )
    private_reduction = (
        reset_priority["private_event_fraction"]
        - factorized["private_event_fraction"]
    ) / reset_priority["private_event_fraction"]
    overlap_reduction = (
        reset_priority["overlap_event_fraction"]
        - factorized["overlap_event_fraction"]
    ) / reset_priority["overlap_event_fraction"]

    primary_passed = (
        state_equal <= 1e-12
        and public_equal <= 1e-12
        and private_reduction >= 0.10
        and overlap_reduction >= 0.25
    )

    return {
        "selected_residual_threshold": threshold,
        "train_seeds": list(TRAIN_SEEDS),
        "test_seeds": list(TEST_SEEDS),
        "test_corruption_detector_f1": float(np.mean(detector_scores)),
        "policies": policies,
        "primary_gate": {
            "state_rmse_difference": float(state_equal),
            "public_event_mismatch_difference": float(public_equal),
            "private_event_reduction_fraction": float(private_reduction),
            "overlap_event_reduction_fraction": float(overlap_reduction),
            "passed": bool(primary_passed),
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_v3(), indent=2, sort_keys=True))
