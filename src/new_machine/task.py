from __future__ import annotations

import numpy as np


def make_stream(seed: int, steps: int = 1200):
    if steps < 120:
        raise ValueError("steps must be at least 120")
    rng = np.random.default_rng(seed)
    slow = np.empty(steps, dtype=float)
    slow[0] = 0.55 + 0.03 * rng.normal()
    for t in range(1, steps):
        slow[t] = 0.985 * slow[t - 1] + 0.015 * 0.55 + 0.018 * rng.normal()

    u = slow + 0.03 * rng.normal(size=steps)
    mute = np.zeros(steps, dtype=bool)
    target = np.zeros(steps, dtype=bool)

    start = 55 + int(rng.integers(0, 15))
    block = 95
    while start + 25 < steps:
        duration = 14 + int(rng.integers(0, 8))
        end = min(start + duration, steps - 4)
        mute[start:end] = True
        if end + 1 < steps:
            target[end] = True
            target[end + 1] = True
            u[end:end + 2] += 0.38
        start += block + int(rng.integers(-8, 9))

    return u, mute, target


def f1_score(target: np.ndarray, prediction: np.ndarray) -> float:
    target = np.asarray(target, dtype=bool)
    prediction = np.asarray(prediction, dtype=bool)
    if target.shape != prediction.shape:
        raise ValueError("target and prediction must have the same shape")
    tp = int(np.sum(target & prediction))
    fp = int(np.sum(~target & prediction))
    fn = int(np.sum(target & ~prediction))
    denom = 2 * tp + fp + fn
    return 0.0 if denom == 0 else (2.0 * tp) / denom


def recovery_error(reference: np.ndarray, observed: np.ndarray, mute: np.ndarray, horizon: int = 8) -> float:
    reference = np.asarray(reference, dtype=float)
    observed = np.asarray(observed, dtype=float)
    mute = np.asarray(mute, dtype=bool)
    if reference.shape != observed.shape or reference.shape != mute.shape:
        raise ValueError("reference, observed, and mute must have the same shape")
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    ends = np.flatnonzero(mute[:-1] & ~mute[1:]) + 1
    errors = []
    for start in ends:
        stop = min(start + horizon, len(reference))
        errors.extend(np.abs(reference[start:stop] - observed[start:stop]))
    return 0.0 if not errors else float(np.mean(errors))


def make_complementary_stream(seed: int, steps: int = 1400):
    if steps < 300:
        raise ValueError("steps must be at least 300")
    rng = np.random.default_rng(seed)
    clean = np.empty(steps, dtype=float)
    clean[0] = 0.55 + 0.03 * rng.normal()
    for t in range(1, steps):
        clean[t] = 0.985 * clean[t - 1] + 0.015 * 0.55 + 0.018 * rng.normal()
    clean += 0.025 * rng.normal(size=steps)

    observed = clean.copy()
    hide = np.zeros(steps, dtype=bool)
    reset = np.zeros(steps, dtype=bool)
    contamination = 0.45

    start = 45 + int(rng.integers(0, 12))
    kind_hide = True
    while start + 28 < steps:
        duration = 14 + int(rng.integers(0, 7))
        end = start + duration
        if kind_hide:
            hide[start:end] = True
        else:
            reset[start:end] = True
            observed[start:end] += contamination
        kind_hide = not kind_hide
        start += 92 + int(rng.integers(-5, 6))

    return clean, observed, hide, reset
