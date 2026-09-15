from __future__ import annotations

import json
from functools import lru_cache
import numpy as np

from new_machine.core import TwoGateUnit
from new_machine.task import make_complementary_stream, recovery_error

ALPHA = 0.88
THETA0 = 0.54
SLOPE_GAIN = 0.75
BASKET_STRENGTHS = (0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)
CHANDELIER_STRENGTHS = (0.0, 0.03, 0.06, 0.09, 0.12, 0.16, 0.20, 0.30, 0.40, 0.50)
TRAIN_SEEDS = tuple(range(20, 28))
TEST_SEEDS = tuple(range(200, 212))
TARGET_CONTEXT_EVENT_FRACTION = 0.10
STEPS = 1400


def _gate_for(policy: str, context: str) -> str:
    if policy == "basket_only":
        return "basket"
    if policy == "chandelier_only":
        return "chandelier"
    if policy == "hybrid":
        return "chandelier" if context == "hide" else "basket"
    raise ValueError(f"unknown policy {policy}")


def _simulate(seed: int, policy: str, hide_strength: float, reset_strength: float):
    clean, observed, hide, reset = make_complementary_stream(seed=seed, steps=STEPS)
    reference = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)
    unit = TwoGateUnit(ALPHA, THETA0, SLOPE_GAIN)

    ref_states = np.empty(STEPS)
    states = np.empty(STEPS)
    events = np.zeros(STEPS, dtype=bool)

    hide_gate = _gate_for(policy, "hide")
    reset_gate = _gate_for(policy, "reset")

    for t in range(STEPS):
        ref_states[t] = reference.step(float(clean[t])).state
        basket = 0.0
        chandelier = 0.0
        if hide[t]:
            if hide_gate == "basket":
                basket = hide_strength
            else:
                chandelier = hide_strength
        elif reset[t]:
            if reset_gate == "basket":
                basket = reset_strength
            else:
                chandelier = reset_strength
        out = unit.step(float(observed[t]), basket=basket, chandelier=chandelier)
        states[t] = out.state
        events[t] = out.event

    hide_rate = float(events[hide].mean()) if np.any(hide) else 0.0
    reset_rate = float(events[reset].mean()) if np.any(reset) else 0.0
    hide_recovery = recovery_error(ref_states, states, hide, horizon=10)
    reset_recovery = recovery_error(ref_states, states, reset, horizon=10)
    return {
        "event_fraction": float(events.mean()),
        "hide_event_fraction": hide_rate,
        "reset_event_fraction": reset_rate,
        "state_rmse": float(np.sqrt(np.mean((states - ref_states) ** 2))),
        "hide_recovery_error": float(hide_recovery),
        "reset_recovery_error": float(reset_recovery),
        "combined_recovery_error": float(0.5 * (hide_recovery + reset_recovery)),
    }


def _mean_metrics(seeds, policy: str, hide_strength: float, reset_strength: float):
    rows = [_simulate(seed, policy, hide_strength, reset_strength) for seed in seeds]
    return {
        key: float(np.mean([row[key] for row in rows]))
        for key in rows[0]
    }


def _grid_for(policy: str, context: str):
    gate = _gate_for(policy, context)
    return BASKET_STRENGTHS if gate == "basket" else CHANDELIER_STRENGTHS


@lru_cache(maxsize=None)
def _select_strengths(policy: str):
    best = None
    for hide_strength in _grid_for(policy, "hide"):
        for reset_strength in _grid_for(policy, "reset"):
            metrics = _mean_metrics(TRAIN_SEEDS, policy, hide_strength, reset_strength)
            budget_error = (
                abs(metrics["hide_event_fraction"] - TARGET_CONTEXT_EVENT_FRACTION)
                + abs(metrics["reset_event_fraction"] - TARGET_CONTEXT_EVENT_FRACTION)
            )
            candidate = (budget_error, hide_strength + reset_strength, hide_strength, reset_strength)
            if best is None or candidate < best:
                best = candidate
    return float(best[2]), float(best[3])


def run_v1():
    policies = {}
    for policy in ("basket_only", "chandelier_only", "hybrid"):
        hide_strength, reset_strength = _select_strengths(policy)
        metrics = _mean_metrics(TEST_SEEDS, policy, hide_strength, reset_strength)
        metrics["hide_strength"] = hide_strength
        metrics["reset_strength"] = reset_strength
        policies[policy] = metrics

    hybrid_best = policies["hybrid"]["combined_recovery_error"] < min(
        policies["basket_only"]["combined_recovery_error"],
        policies["chandelier_only"]["combined_recovery_error"],
    )
    return {
        "target_context_event_fraction": TARGET_CONTEXT_EVENT_FRACTION,
        "train_seeds": list(TRAIN_SEEDS),
        "test_seeds": list(TEST_SEEDS),
        "policies": policies,
        "hybrid_primary_hypothesis_passed": bool(hybrid_best),
    }


if __name__ == "__main__":
    print(json.dumps(run_v1(), indent=2, sort_keys=True))
