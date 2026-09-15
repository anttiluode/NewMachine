import numpy as np

from new_machine.task import make_complementary_stream


def test_complementary_stream_is_deterministic_and_contexts_do_not_overlap():
    a = make_complementary_stream(seed=9, steps=700)
    b = make_complementary_stream(seed=9, steps=700)
    for xa, xb in zip(a, b):
        assert np.array_equal(xa, xb)
    clean, observed, hide, reset = a
    assert clean.shape == observed.shape == hide.shape == reset.shape == (700,)
    assert hide.dtype == bool and reset.dtype == bool
    assert not np.any(hide & reset)
    assert hide.sum() > 0 and reset.sum() > 0


def test_only_reset_windows_contaminate_observed_input():
    clean, observed, hide, reset = make_complementary_stream(seed=4, steps=700)
    delta = observed - clean
    assert np.allclose(delta[~reset], 0.0)
    assert np.all(delta[reset] > 0.0)
    assert np.allclose(delta[reset], delta[reset][0])


def test_both_context_types_have_room_for_recovery_after_windows():
    _, _, hide, reset = make_complementary_stream(seed=2, steps=700)
    for mask in (hide, reset):
        ends = np.flatnonzero(mask[:-1] & ~mask[1:]) + 1
        assert len(ends) >= 2
        for end in ends:
            assert not hide[end:min(end + 8, len(hide))].any()
            assert not reset[end:min(end + 8, len(reset))].any()
