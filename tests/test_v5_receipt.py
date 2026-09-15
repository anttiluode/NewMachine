from __future__ import annotations

from experiments.run_v5 import DEFAULT_THRESHOLD, SEEDS, THRESHOLDS, run_v5


def test_v5_receipt_has_frozen_worlds_and_threshold_bank():
    result = run_v5()
    assert result["seeds"] == list(SEEDS)
    assert result["thresholds"] == list(THRESHOLDS)
    assert result["default_event_threshold"] == DEFAULT_THRESHOLD


def test_v5_cross_view_inference_beats_sender_only_pca():
    result = run_v5()
    gate = result["subspace_gate"]
    assert gate["mean_shared_alignment"] >= 0.85
    assert gate["mean_shared_alignment"] - gate["mean_pca_alignment"] >= 0.50
    assert gate["shared_beats_pca_same_threshold_points"] == len(THRESHOLDS)


def test_v5_state_repair_improves_learned_shared_receiver():
    result = run_v5()
    gate = result["repair_gate"]
    assert gate["shared_repair_beats_shared_delta_same_threshold_points"] == len(THRESHOLDS)
    assert gate["default_receiver_rmse_reduction_fraction"] >= 0.50
    assert gate["default_event_fraction_reduction_fraction"] >= 0.50
    assert gate["default_detector_f1"] >= 0.90


def test_v5_learned_system_stays_near_oracle_at_default_point():
    result = run_v5()
    comparison = result["learned_vs_oracle"]
    assert comparison["default_receiver_rmse_ratio"] <= 1.15
