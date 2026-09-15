from __future__ import annotations

import json
import numpy as np

from new_machine.core import TwoGateUnit
from new_machine.task import f1_score, make_stream, recovery_error

ALPHA = 0.88
THETA0 = 0.54
SLOPE_GAIN = 0.75
STRENGTHS = (0.0, 0.01, 0.02, 0.04, 0.06, 0.08, 0.12, 0.16, 0.24, 0.32)
TRAIN_SEEDS = tuple(range(8))
TEST_SEEDS = tuple(range(100, 112))
TARGET_MUTE_EVENT_FRACTION = 0.10
STEPS = 1200


def _simulate(seed: int, mechanism: str, strength: float):
    u, mute, target = make_stream(seed=seed, steps=STEPS)
    unit = TwoGateUnit(alpha=ALPHA, theta0=THETA0, slope_gain=SLOPE_GAIN)
    reference = TwoGateUnit(alpha=ALPHA, theta0=THETA0, slope_gain=SLOPE_GAIN)

    states = np.empty(STEPS)
    ref_states = np.empty(STEPS)
    events = np.zeros(STEPS, dtype=bool)
    for t in range(STEPS):
        ref_states[t] = reference.step(float(u[t])).state
        basket = strength if mechanism == "basket" and mute[t] else 0.0
        chandelier = strength if mechanism == "chandelier" and mute[t] else 0.0
        out = unit.step(float(u[t]), basket=basket, chandelier=chandelier)
        states[t] = out.state
        events[t] = out.event

    mute_fraction = float(events[mute].mean()) if np.any(mute) else 0.0
    return {
        "event_fraction": float(events.mean()),
        "mute_event_fraction": mute_fraction,
        "f1": float(f1_score(target, events)),
        "state_rmse": float(np.sqrt(np.mean((states - ref_states) ** 2))),
        "recovery_error": float(recovery_error(ref_states, states, mute, horizon=10)),
    }


def _mean_metrics(seeds, mechanism: str, strength: float):
    rows = [_simulate(seed, mechanism, strength) for seed in seeds]
    keys = rows[0].keys()
    return {key: float(np.mean([r[key] for r in rows])) for key in keys}


def _select_strength(mechanism: str):
    scored = []
    for strength in STRENGTHS:
        metrics = _mean_metrics(TRAIN_SEEDS, mechanism, strength)
        scored.append((abs(metrics["mute_event_fraction"] - TARGET_MUTE_EVENT_FRACTION), strength))
    scored.sort(key=lambda item: (item[0], item[1]))
    return float(scored[0][1])


def _gate0():
    inputs = np.linspace(-1.0, 2.0, 61)
    controls = np.linspace(0.0, 0.8, 61)
    for u, q in zip(inputs, controls):
        b = TwoGateUnit(0.0, 0.4, 0.0).step(float(u), basket=float(q)).event
        c = TwoGateUnit(0.0, 0.4, 0.0).step(float(u), chandelier=float(q)).event
        if b != c:
            return False
    return True


def _gate1():
    reference = TwoGateUnit(0.8, 0.5, 0.0)
    basket = TwoGateUnit(0.8, 0.5, 0.0)
    chandelier = TwoGateUnit(0.8, 0.5, 0.0)
    for _ in range(12):
        reference.step(1.0)
        basket.step(1.0)
        chandelier.step(1.0)
    reference.step(1.0)
    basket.step(1.0, basket=0.3)
    chandelier.step(1.0, chandelier=0.3)
    basket_errors = []
    chandelier_errors = []
    for _ in range(12):
        r = reference.step(1.0).state
        basket_errors.append(abs(basket.step(1.0).state - r))
        chandelier_errors.append(abs(chandelier.step(1.0).state - r))
    return float(np.mean(basket_errors)), float(np.mean(chandelier_errors))


def _gate2():
    slow = TwoGateUnit(0.0, 0.8, 0.7)
    slow_any = any(slow.step(float(v)).event for v in np.linspace(0.0, 0.75, 16))
    fast = TwoGateUnit(0.0, 0.8, 0.7)
    fast.step(0.0)
    fast_event = fast.step(0.75).event
    return bool(slow_any), bool(fast_event)


def run_v0():
    basket_recovery, chandelier_recovery = _gate1()
    slow_any, fast_event = _gate2()
    basket_strength = _select_strength("basket")
    chandelier_strength = _select_strength("chandelier")
    basket = _mean_metrics(TEST_SEEDS, "basket", basket_strength)
    chandelier = _mean_metrics(TEST_SEEDS, "chandelier", chandelier_strength)
    basket["strength"] = basket_strength
    chandelier["strength"] = chandelier_strength
    return {
        "gate0_static_equivalent": _gate0(),
        "gate1_basket_recovery_error": basket_recovery,
        "gate1_chandelier_recovery_error": chandelier_recovery,
        "gate2_slow_ramp_any_event": slow_any,
        "gate2_fast_step_event": fast_event,
        "gate3": {
            "target_mute_event_fraction": TARGET_MUTE_EVENT_FRACTION,
            "basket": basket,
            "chandelier": chandelier,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_v0(), indent=2, sort_keys=True))
