from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


UINT32 = 2**32
BASELINE = 0.55
SENDER_ALPHA = 0.90
RECEIVER_ALPHA = 0.995
DETECTOR_THRESHOLD = 0.20
LOCAL_ONLY_OFFSET = 0.10


@dataclass
class Lcg32:
    state: int

    def __post_init__(self) -> None:
        self.state = int(self.state) & 0xFFFFFFFF

    def uniform(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / UINT32

    def signed(self) -> float:
        return 2.0 * self.uniform() - 1.0


def _world(
    seed: int,
    steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if steps < 32:
        raise ValueError("steps must be at least 32")

    rng = Lcg32(seed ^ 0x9E3779B9)
    truth = np.empty(steps, dtype=float)
    local_truth = np.empty(steps, dtype=float)
    observed = np.empty(steps, dtype=float)
    private = np.zeros(steps, dtype=bool)
    corrupt = np.zeros(steps, dtype=bool)

    truth[0] = BASELINE + 0.02 * rng.signed()
    for t in range(steps):
        if t:
            truth[t] = 0.992 * truth[t - 1] + 0.008 * BASELINE + 0.012 * rng.signed()

        private[t] = ((t + (seed * 7) % 83) % 83) < 18
        corrupt[t] = ((t + (seed * 11) % 97) % 97) < 16

        # A private interval may contain legitimate local computation that the
        # downstream receiver should not track. This is relevance, not noise.
        local_truth[t] = truth[t] + (LOCAL_ONLY_OFFSET if private[t] else 0.0)
        observed[t] = local_truth[t] + 0.02 * rng.signed() + (0.45 if corrupt[t] else 0.0)

    return truth, local_truth, observed, private, corrupt


def _recovery_rmse(truth: np.ndarray, receiver: np.ndarray, corrupt: np.ndarray, horizon: int = 12) -> float:
    ends = np.flatnonzero(corrupt[:-1] & ~corrupt[1:]) + 1
    errors: list[float] = []
    for start in ends:
        stop = min(start + horizon, len(truth))
        errors.extend((receiver[start:stop] - truth[start:stop]).tolist())
    if not errors:
        return 0.0
    arr = np.asarray(errors, dtype=float)
    return float(np.sqrt(np.mean(arr * arr)))


def simulate_policy(
    seed: int,
    policy: str,
    event_threshold: float = 0.08,
    steps: int = 1200,
) -> dict[str, object]:
    """Run one sender/receiver policy on a deterministic stream.

    `truth` is the receiver-relevant public state. `local_truth` may contain a
    valid local-only excursion during private windows. The sender is scored
    against local truth; the receiver is scored against public truth.

    Policies:
      dense      - publish every step, no repair.
      delta      - publish innovations above threshold, no repair.
      signed     - repair detected corruption OR suppress private output;
                   repair has priority when both are required.
      factorized - repair and publication suppression are independent.
    """
    if policy not in {"dense", "delta", "signed", "factorized"}:
        raise ValueError(f"unknown policy: {policy}")
    if not np.isfinite(event_threshold) or event_threshold < 0.0:
        raise ValueError("event_threshold must be finite and nonnegative")

    truth, local_truth, observed, private, corrupt = _world(int(seed), int(steps))
    sender = np.empty(steps, dtype=float)
    receiver = np.empty(steps, dtype=float)
    detected = np.zeros(steps, dtype=bool)
    repaired = np.zeros(steps, dtype=bool)
    events = np.zeros(steps, dtype=bool)

    sender_state = BASELINE
    receiver_state = BASELINE

    for t in range(steps):
        detected[t] = abs(observed[t] - sender_state) > DETECTOR_THRESHOLD

        wants_repair = bool(detected[t] and policy in {"signed", "factorized"})
        repaired[t] = wants_repair
        if wants_repair:
            sender_state = RECEIVER_ALPHA * sender_state + (1.0 - RECEIVER_ALPHA) * BASELINE
        else:
            sender_state = SENDER_ALPHA * sender_state + (1.0 - SENDER_ALPHA) * observed[t]
        sender[t] = sender_state

        receiver_prediction = RECEIVER_ALPHA * receiver_state + (1.0 - RECEIVER_ALPHA) * BASELINE

        if policy == "factorized":
            suppress = bool(private[t])
        elif policy == "signed":
            suppress = bool(private[t] and not detected[t])
        else:
            suppress = False

        if policy == "dense":
            publish = True
        else:
            publish = abs(sender_state - receiver_prediction) >= event_threshold
        publish = bool(publish and not suppress)
        events[t] = publish

        receiver_state = sender_state if publish else receiver_prediction
        receiver[t] = receiver_state

    overlap = private & detected
    metrics = {
        "sender_rmse": float(np.sqrt(np.mean((sender - local_truth) ** 2))),
        "receiver_rmse": float(np.sqrt(np.mean((receiver - truth) ** 2))),
        "event_fraction": float(np.mean(events)),
        "private_event_fraction": float(np.mean(events[private])) if np.any(private) else 0.0,
        "overlap_event_fraction": float(np.mean(events[overlap])) if np.any(overlap) else 0.0,
        "recovery_rmse": _recovery_rmse(truth, receiver, corrupt),
        "detector_f1": _binary_f1(corrupt, detected),
    }

    return {
        "policy": policy,
        "seed": int(seed),
        "event_threshold": float(event_threshold),
        "metrics": metrics,
        "trace": {
            "truth": truth,
            "local_truth": local_truth,
            "observed": observed,
            "sender": sender,
            "receiver": receiver,
            "private": private,
            "corrupt": corrupt,
            "detected_corrupt": detected,
            "repaired": repaired,
            "events": events,
        },
    }


def _binary_f1(target: np.ndarray, prediction: np.ndarray) -> float:
    tp = int(np.sum(target & prediction))
    fp = int(np.sum(~target & prediction))
    fn = int(np.sum(target & ~prediction))
    denom = 2 * tp + fp + fn
    return 0.0 if denom == 0 else float((2 * tp) / denom)


def run_frontier(
    seed: int,
    thresholds: Iterable[float] = (0.0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18),
    steps: int = 1200,
) -> dict[str, list[dict[str, float]]]:
    result: dict[str, list[dict[str, float]]] = {}
    for policy in ("dense", "delta", "signed", "factorized"):
        points: list[dict[str, float]] = []
        for threshold in thresholds:
            sim = simulate_policy(seed=seed, policy=policy, event_threshold=float(threshold), steps=steps)
            metrics = sim["metrics"]
            points.append(
                {
                    "threshold": float(threshold),
                    "receiver_rmse": float(metrics["receiver_rmse"]),
                    "event_fraction": float(metrics["event_fraction"]),
                    "recovery_rmse": float(metrics["recovery_rmse"]),
                }
            )
        result[policy] = points
    return result
