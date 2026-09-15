from __future__ import annotations

import numpy as np

from new_machine.vector_receiver import calibrate_world, make_vector_world, simulate_vector_policy


def test_vector_world_is_deterministic_and_has_independent_local_state():
    a = make_vector_world(seed=17, steps=320)
    b = make_vector_world(seed=17, steps=320)

    for key in ("public_truth", "sender_clean", "sender_observed", "peer_view"):
        assert a[key].shape == (320, 6)
        assert np.allclose(a[key], b[key])

    assert a["corrupt"].shape == (320,)
    assert a["public_projector"].shape == (6, 6)
    assert np.allclose(a["public_projector"] @ a["public_projector"], a["public_projector"], atol=1e-10)
    assert not np.allclose(a["sender_clean"], a["public_truth"])
    assert not np.allclose(a["peer_view"], a["public_truth"])


def test_cross_view_calibration_recovers_shared_subspace_better_than_sender_pca():
    shared_scores = []
    pca_scores = []
    for seed in (3, 7, 11, 19):
        world = make_vector_world(seed=seed, steps=900)
        calibration = calibrate_world(world, calibration_steps=420, shared_dim=2)
        shared_scores.append(calibration["shared_alignment"])
        pca_scores.append(calibration["pca_alignment"])

    assert float(np.mean(shared_scores)) > 0.85
    assert float(np.mean(shared_scores)) > float(np.mean(pca_scores)) + 0.20


def test_vector_policy_reports_real_receiver_and_inference_metrics():
    result = simulate_vector_policy(
        seed=23,
        policy="shared_repair",
        event_threshold=0.10,
        steps=1000,
        calibration_steps=420,
    )
    metrics = result["metrics"]

    assert metrics["receiver_rmse"] >= 0.0
    assert metrics["sender_rmse"] >= 0.0
    assert 0.0 <= metrics["event_fraction"] <= 1.0
    assert 0.0 <= metrics["detector_f1"] <= 1.0
    assert 0.0 <= metrics["shared_alignment"] <= 1.0
    assert 0.0 <= metrics["pca_alignment"] <= 1.0
