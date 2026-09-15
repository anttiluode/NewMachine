import numpy as np
import pytest

from new_machine.task import f1_score, make_stream, recovery_error


def test_stream_is_deterministic_and_well_formed():
    a = make_stream(seed=7, steps=500)
    b = make_stream(seed=7, steps=500)
    for xa, xb in zip(a, b):
        assert np.array_equal(xa, xb)
    u, mute, target = a
    assert u.shape == mute.shape == target.shape == (500,)
    assert mute.dtype == bool
    assert target.dtype == bool
    assert np.isfinite(u).all()
    assert not np.any(target & mute)
    assert target.sum() > 0
    assert mute.sum() > 0


def test_different_seed_changes_stream():
    a = make_stream(seed=1, steps=500)[0]
    b = make_stream(seed=2, steps=500)[0]
    assert not np.array_equal(a, b)


def test_f1_score_handles_perfect_empty_and_partial_cases():
    target = np.array([False, True, False, True])
    assert f1_score(target, target) == pytest.approx(1.0)
    assert f1_score(target, np.zeros(4, dtype=bool)) == pytest.approx(0.0)
    pred = np.array([False, True, True, False])
    assert f1_score(target, pred) == pytest.approx(0.5)


def test_recovery_error_uses_only_post_mute_window():
    ref = np.arange(10, dtype=float)
    got = ref.copy()
    got[5:8] += np.array([1.0, 2.0, 3.0])
    mute = np.zeros(10, dtype=bool)
    mute[2:5] = True
    assert recovery_error(ref, got, mute, horizon=3) == pytest.approx(2.0)
