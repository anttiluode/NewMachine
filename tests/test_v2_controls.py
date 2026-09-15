import numpy as np

from new_machine.core import TwoGateUnit, signed_control
from new_machine.task import make_complementary_stream, recovery_hold_mask


def test_signed_control_routes_negative_to_state_gate():
    basket, chandelier = signed_control(-0.25)
    assert basket == 0.25
    assert chandelier == 0.0


def test_signed_control_routes_positive_to_publication_gate():
    basket, chandelier = signed_control(0.25)
    assert basket == 0.0
    assert chandelier == 0.25


def test_signed_control_zero_is_noop():
    assert signed_control(0.0) == (0.0, 0.0)


def test_signed_scalar_reproduces_direct_hybrid_exactly():
    clean, observed, hide, reset = make_complementary_stream(seed=311, steps=700)
    direct = TwoGateUnit(alpha=0.88, theta0=0.54, slope_gain=0.75)
    signed = TwoGateUnit(alpha=0.88, theta0=0.54, slope_gain=0.75)

    for t in range(len(clean)):
        basket = 0.08 if reset[t] else 0.0
        chandelier = 0.16 if hide[t] else 0.0
        a = direct.step(float(observed[t]), basket=basket, chandelier=chandelier)

        q = 0.16 if hide[t] else (-0.08 if reset[t] else 0.0)
        b_gate, c_gate = signed_control(q)
        b = signed.step(float(observed[t]), basket=b_gate, chandelier=c_gate)

        assert a.state == b.state
        assert a.slope == b.slope
        assert a.threshold == b.threshold
        assert a.event == b.event


def test_recovery_hold_mask_starts_after_control_window():
    mask = np.array([False, True, True, False, False, False, True, False, False])
    hold = recovery_hold_mask(mask, horizon=2)
    expected = np.array([False, False, False, True, True, False, False, True, True])
    np.testing.assert_array_equal(hold, expected)
