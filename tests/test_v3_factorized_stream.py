import numpy as np

from new_machine.task import make_factorized_stream, prediction_residuals


def test_factorized_stream_has_independent_private_corrupt_and_overlap_regimes():
    clean, observed, private, corrupt = make_factorized_stream(seed=17, steps=1200)
    assert np.any(private & ~corrupt)
    assert np.any(corrupt & ~private)
    assert np.any(private & corrupt)
    assert np.any(~private & ~corrupt)
    np.testing.assert_allclose(observed[~corrupt], clean[~corrupt])
    np.testing.assert_allclose(observed[corrupt] - clean[corrupt], 0.45)


def test_prediction_residuals_are_causal_and_same_length():
    observed = np.array([0.5, 0.6, 0.4], dtype=float)
    residual = prediction_residuals(observed, alpha=0.8)
    assert residual.shape == observed.shape
    assert residual[0] == 0.5
    expected_second = 0.6 - (0.2 * 0.5)
    assert abs(residual[1] - expected_second) < 1e-15
