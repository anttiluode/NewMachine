from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class StepResult:
    state: float
    slope: float
    threshold: float
    event: bool


def signed_control(q: float) -> tuple[float, float]:
    """Route one signed scalar to exactly one intervention site.

    Negative values act on resident state (basket-like); positive values act
    on publication threshold (chandelier-like). Zero is a no-op.
    """
    if not math.isfinite(q):
        raise ValueError("q must be finite")
    if q < 0.0:
        return -float(q), 0.0
    if q > 0.0:
        return 0.0, float(q)
    return 0.0, 0.0


class TwoGateUnit:
    """Persistent scalar state with state-side and threshold-side control."""

    def __init__(self, alpha: float, theta0: float, slope_gain: float):
        if not math.isfinite(alpha) or not (0.0 <= alpha < 1.0):
            raise ValueError("alpha must be finite and in [0, 1)")
        if not math.isfinite(theta0):
            raise ValueError("theta0 must be finite")
        if not math.isfinite(slope_gain) or slope_gain < 0.0:
            raise ValueError("slope_gain must be finite and nonnegative")
        self.alpha = float(alpha)
        self.theta0 = float(theta0)
        self.slope_gain = float(slope_gain)
        self.state = 0.0

    def reset(self) -> None:
        self.state = 0.0

    def step(self, u: float, basket: float = 0.0, chandelier: float = 0.0) -> StepResult:
        for name, value in (("u", u), ("basket", basket), ("chandelier", chandelier)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        previous = self.state
        self.state = self.alpha * previous + (1.0 - self.alpha) * float(u) - float(basket)
        slope = self.state - previous
        threshold = self.theta0 + float(chandelier) - self.slope_gain * max(slope, 0.0)
        return StepResult(
            state=self.state,
            slope=slope,
            threshold=threshold,
            event=bool(self.state > threshold),
        )
