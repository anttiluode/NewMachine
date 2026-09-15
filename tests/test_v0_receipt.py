import math

from experiments.run_v0 import run_v0


def test_v0_receipt_is_deterministic_and_contains_frozen_gates():
    a = run_v0()
    b = run_v0()
    assert a == b
    assert a["gate0_static_equivalent"] is True
    assert a["gate1_basket_recovery_error"] > 0.0
    assert a["gate1_chandelier_recovery_error"] == 0.0
    assert a["gate2_fast_step_event"] is True
    assert a["gate2_slow_ramp_any_event"] is False


def test_v0_task_metrics_are_finite_and_budget_matched_reasonably():
    result = run_v0()
    task = result["gate3"]
    for mechanism in ("basket", "chandelier"):
        metrics = task[mechanism]
        assert 0.0 <= metrics["event_fraction"] <= 1.0
        assert 0.0 <= metrics["mute_event_fraction"] <= 1.0
        assert 0.0 <= metrics["f1"] <= 1.0
        assert math.isfinite(metrics["state_rmse"])
        assert math.isfinite(metrics["recovery_error"])
        assert math.isfinite(metrics["strength"])
    assert abs(task["basket"]["mute_event_fraction"] - task["chandelier"]["mute_event_fraction"]) <= 0.08
