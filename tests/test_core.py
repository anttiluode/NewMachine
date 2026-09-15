import numpy as np
import pytest

from new_machine.core import TwoGateUnit


def test_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        TwoGateUnit(alpha=-0.1, theta0=0.5, slope_gain=0.0)
    with pytest.raises(ValueError):
        TwoGateUnit(alpha=1.0, theta0=0.5, slope_gain=0.0)
    with pytest.raises(ValueError):
        TwoGateUnit(alpha=0.5, theta0=0.5, slope_gain=-1.0)


def test_static_basket_and_chandelier_are_output_equivalent():
    inputs = np.linspace(-1.0, 2.0, 31)
    controls = np.linspace(0.0, 0.8, 31)
    for u, q in zip(inputs, controls):
        basket = TwoGateUnit(alpha=0.0, theta0=0.4, slope_gain=0.0)
        chandelier = TwoGateUnit(alpha=0.0, theta0=0.4, slope_gain=0.0)
        eb = basket.step(u, basket=q).event
        ec = chandelier.step(u, chandelier=q).event
        assert eb == ec


def test_basket_control_leaves_persistent_state_scar():
    ref = TwoGateUnit(alpha=0.8, theta0=0.5, slope_gain=0.0)
    basket = TwoGateUnit(alpha=0.8, theta0=0.5, slope_gain=0.0)
    for _ in range(12):
        ref.step(1.0)
        basket.step(1.0)
    ref.step(1.0)
    basket.step(1.0, basket=0.3)
    diffs = []
    for _ in range(8):
        r = ref.step(1.0)
        b = basket.step(1.0)
        diffs.append(abs(r.state - b.state))
    assert diffs[0] > 0.0
    assert diffs[-1] > 0.0
    assert diffs[-1] < diffs[0]


def test_chandelier_control_does_not_change_persistent_state():
    ref = TwoGateUnit(alpha=0.8, theta0=0.5, slope_gain=0.0)
    chandelier = TwoGateUnit(alpha=0.8, theta0=0.5, slope_gain=0.0)
    for _ in range(12):
        assert ref.step(1.0).state == pytest.approx(chandelier.step(1.0).state)
    ref_now = ref.step(1.0)
    ch_now = chandelier.step(1.0, chandelier=0.3)
    assert ch_now.state == pytest.approx(ref_now.state)
    for _ in range(8):
        assert chandelier.step(1.0).state == pytest.approx(ref.step(1.0).state)


def test_slope_sensitive_knee_prefers_fast_rise_at_lower_absolute_state():
    slow = TwoGateUnit(alpha=0.0, theta0=0.8, slope_gain=0.7)
    slow_events = [slow.step(v).event for v in np.linspace(0.0, 0.75, 16)]
    fast = TwoGateUnit(alpha=0.0, theta0=0.8, slope_gain=0.7)
    fast.step(0.0)
    fast_event = fast.step(0.75).event
    assert not any(slow_events)
    assert fast_event
