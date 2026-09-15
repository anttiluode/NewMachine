from __future__ import annotations

from experiments.run_v4 import SEEDS, THRESHOLDS, run_v4


def test_v4_receipt_has_fixed_seed_bank_and_thresholds():
    result = run_v4()
    assert result["seeds"] == list(SEEDS)
    assert result["thresholds"] == list(THRESHOLDS)
    assert set(result["frontier"]) == {"dense", "delta", "signed", "factorized"}


def test_v4_factorized_and_signed_have_identical_sender_dynamics():
    result = run_v4()
    comparison = result["factorized_vs_signed"]
    assert comparison["sender_rmse_max_abs_difference"] <= 1e-12


def test_v4_receipt_labels_same_threshold_comparison_as_pairwise_not_pareto():
    result = run_v4()
    comparison = result["factorized_vs_signed"]
    assert 0 <= comparison["pairwise_better_points"] <= len(THRESHOLDS)
    assert isinstance(comparison["pairwise_improvement_found"], bool)
    assert comparison["pairwise_improvement_found"] == (comparison["pairwise_better_points"] > 0)
    assert "pareto_better_points" not in comparison
    assert "frontier_extension_found" not in comparison


def test_v4_default_operating_point_has_real_receiver_and_message_metrics():
    result = run_v4()
    for policy in ("dense", "delta", "signed", "factorized"):
        metrics = result["default_threshold"][policy]
        assert metrics["receiver_rmse"] >= 0.0
        assert metrics["sender_rmse"] >= 0.0
        assert 0.0 <= metrics["event_fraction"] <= 1.0
        assert 0.0 <= metrics["detector_f1"] <= 1.0
