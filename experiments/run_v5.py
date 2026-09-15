from __future__ import annotations

from functools import lru_cache
import json

import numpy as np

from new_machine.vector_receiver import simulate_vector_policy


SEEDS = (3, 7, 11, 19, 23, 31, 47, 59)
THRESHOLDS = (0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20)
DEFAULT_THRESHOLD = 0.10
STEPS = 1800
CALIBRATION_STEPS = 420
POLICIES = (
    "raw_delta",
    "pca_delta",
    "shared_delta",
    "shared_repair",
    "oracle_repair",
)
METRIC_KEYS = (
    "sender_rmse",
    "receiver_rmse",
    "event_fraction",
    "detector_f1",
    "repair_fraction",
    "shared_alignment",
    "pca_alignment",
    "detector_threshold",
)


def _mean_metrics(policy: str, threshold: float) -> dict[str, float]:
    rows = [
        simulate_vector_policy(
            seed=seed,
            policy=policy,
            event_threshold=threshold,
            steps=STEPS,
            calibration_steps=CALIBRATION_STEPS,
        )["metrics"]
        for seed in SEEDS
    ]
    return {
        key: float(np.mean([float(row[key]) for row in rows]))
        for key in METRIC_KEYS
    }


def _curve(policy: str) -> list[dict[str, float]]:
    return [
        {"threshold": float(threshold), **_mean_metrics(policy, threshold)}
        for threshold in THRESHOLDS
    ]


@lru_cache(maxsize=1)
def run_v5() -> dict[str, object]:
    curves = {policy: _curve(policy) for policy in POLICIES}
    default = {
        policy: _mean_metrics(policy, DEFAULT_THRESHOLD)
        for policy in POLICIES
    }

    pca_curve = curves["pca_delta"]
    shared_curve = curves["shared_delta"]
    repair_curve = curves["shared_repair"]

    shared_beats_pca = [
        shared["receiver_rmse"] < pca["receiver_rmse"] - 1e-12
        and shared["event_fraction"] <= pca["event_fraction"] + 1e-12
        for pca, shared in zip(pca_curve, shared_curve, strict=True)
    ]
    repair_beats_shared = [
        repair["receiver_rmse"] < shared["receiver_rmse"] - 1e-12
        and repair["event_fraction"] <= shared["event_fraction"] + 1e-12
        for shared, repair in zip(shared_curve, repair_curve, strict=True)
    ]

    pca_default = default["pca_delta"]
    shared_default = default["shared_delta"]
    repair_default = default["shared_repair"]
    oracle_default = default["oracle_repair"]

    return {
        "seeds": list(SEEDS),
        "thresholds": list(THRESHOLDS),
        "default_event_threshold": DEFAULT_THRESHOLD,
        "steps": STEPS,
        "calibration_steps": CALIBRATION_STEPS,
        "curves": curves,
        "default_threshold": default,
        "subspace_gate": {
            "mean_shared_alignment": float(shared_default["shared_alignment"]),
            "mean_pca_alignment": float(shared_default["pca_alignment"]),
            "alignment_advantage": float(
                shared_default["shared_alignment"] - shared_default["pca_alignment"]
            ),
            "shared_beats_pca_same_threshold_points": int(sum(shared_beats_pca)),
            "default_receiver_rmse_reduction_vs_pca_fraction": float(
                (pca_default["receiver_rmse"] - shared_default["receiver_rmse"])
                / pca_default["receiver_rmse"]
            ),
            "default_event_fraction_reduction_vs_pca_fraction": float(
                (pca_default["event_fraction"] - shared_default["event_fraction"])
                / pca_default["event_fraction"]
            ),
        },
        "repair_gate": {
            "shared_repair_beats_shared_delta_same_threshold_points": int(
                sum(repair_beats_shared)
            ),
            "default_receiver_rmse_reduction_fraction": float(
                (shared_default["receiver_rmse"] - repair_default["receiver_rmse"])
                / shared_default["receiver_rmse"]
            ),
            "default_event_fraction_reduction_fraction": float(
                (shared_default["event_fraction"] - repair_default["event_fraction"])
                / shared_default["event_fraction"]
            ),
            "default_detector_f1": float(repair_default["detector_f1"]),
        },
        "learned_vs_oracle": {
            "default_receiver_rmse_ratio": float(
                repair_default["receiver_rmse"] / oracle_default["receiver_rmse"]
            ),
            "default_receiver_rmse_absolute_gap": float(
                repair_default["receiver_rmse"] - oracle_default["receiver_rmse"]
            ),
            "default_event_fraction_difference": float(
                repair_default["event_fraction"] - oracle_default["event_fraction"]
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_v5(), indent=2, sort_keys=True))
