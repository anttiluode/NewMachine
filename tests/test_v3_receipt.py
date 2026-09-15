from experiments.run_v3 import run_v3


def test_v3_detector_is_selected_on_training_seeds_only():
    result = run_v3()
    assert result["selected_residual_threshold"] == 0.08
    assert result["test_corruption_detector_f1"] > 0.75


def test_v3_factorized_and_reset_priority_share_state_and_public_behavior():
    result = run_v3()
    policies = result["policies"]
    factorized = policies["factorized"]
    reset_priority = policies["reset_priority_signed"]
    assert abs(factorized["state_rmse"] - reset_priority["state_rmse"]) <= 1e-12
    assert abs(
        factorized["public_event_mismatch_fraction"]
        - reset_priority["public_event_mismatch_fraction"]
    ) <= 1e-12


def test_v3_factorized_control_uses_both_sites_when_objectives_overlap():
    result = run_v3()
    gate = result["primary_gate"]
    assert gate["private_event_reduction_fraction"] >= 0.10
    assert gate["overlap_event_reduction_fraction"] >= 0.25
    assert gate["passed"] is True
