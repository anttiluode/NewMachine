from __future__ import annotations

import json

import numpy as np

from new_machine.receiver import simulate_policy


SEEDS = (3, 7, 11, 19, 23, 31, 47, 59)
THRESHOLDS = (0.0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18)
DEFAULT_THRESHOLD = 0.04
POLICIES = ("dense", "delta", "signed", "factorized")
METRICS = (
    "sender_rmse",
    "receiver_rmse",
    "event_fraction",
    "private_event_fraction",
    "overlap_event_fraction",
    "recovery_rmse",
    "detector_f1",
)


def _mean_metrics(policy: str, threshold: float) -> dict[str, float]:
    rows = [
        simulate_policy(seed=seed, policy=policy, event_threshold=threshold)["metrics"]
        for seed in SEEDS
    ]
    return {
        key: float(np.mean([float(row[key]) for row in rows]))
        for key in METRICS
    }


def _frontier(policy: str) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for threshold in THRESHOLDS:
        metrics = _mean_metrics(policy, threshold)
        points.append({"threshold": float(threshold), **metrics})
    return points


def run_v4() -> dict[str, object]:
    frontier = {policy: _frontier(policy) for policy in POLICIES}
    default = {
        policy: _mean_metrics(policy, DEFAULT_THRESHOLD)
        for policy in POLICIES
    }

    signed = frontier["signed"]
    factorized = frontier["factorized"]
    sender_diffs = [
        abs(f["sender_rmse"] - s["sender_rmse"])
        for s, f in zip(signed, factorized, strict=True)
    ]
    pareto_better = [
        (f["event_fraction"] <= s["event_fraction"] + 1e-12)
        and (f["receiver_rmse"] < s["receiver_rmse"] - 1e-12)
        for s, f in zip(signed, factorized, strict=True)
    ]
    receiver_improvements = [
        s["receiver_rmse"] - f["receiver_rmse"]
        for s, f in zip(signed, factorized, strict=True)
    ]
    event_reductions = [
        s["event_fraction"] - f["event_fraction"]
        for s, f in zip(signed, factorized, strict=True)
    ]

    delta_default = default["delta"]
    signed_default = default["signed"]
    factorized_default = default["factorized"]

    return {
        "seeds": list(SEEDS),
        "thresholds": list(THRESHOLDS),
        "default_event_threshold": DEFAULT_THRESHOLD,
        "frontier": frontier,
        "default_threshold": default,
        "state_repair_vs_delta": {
            "signed_receiver_rmse_reduction_fraction": float(
                (delta_default["receiver_rmse"] - signed_default["receiver_rmse"])
                / delta_default["receiver_rmse"]
            ),
            "factorized_receiver_rmse_reduction_fraction": float(
                (delta_default["receiver_rmse"] - factorized_default["receiver_rmse"])
                / delta_default["receiver_rmse"]
            ),
            "signed_event_fraction_difference": float(
                signed_default["event_fraction"] - delta_default["event_fraction"]
            ),
            "factorized_event_fraction_difference": float(
                factorized_default["event_fraction"] - delta_default["event_fraction"]
            ),
        },
        "factorized_vs_signed": {
            "sender_rmse_max_abs_difference": float(max(sender_diffs)),
            "pareto_better_points": int(sum(pareto_better)),
            "frontier_extension_found": bool(any(pareto_better)),
            "all_points_dominate_signed": bool(all(pareto_better)),
            "max_receiver_rmse_improvement": float(max(receiver_improvements)),
            "min_receiver_rmse_improvement": float(min(receiver_improvements)),
            "max_event_fraction_reduction": float(max(event_reductions)),
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_v4(), indent=2, sort_keys=True))
