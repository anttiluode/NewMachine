import math

from experiments.run_v1 import run_v1


def test_v1_receipt_is_deterministic_and_reports_all_policies():
    a = run_v1()
    b = run_v1()
    assert a == b
    assert set(a["policies"]) == {"basket_only", "chandelier_only", "hybrid"}
    for metrics in a["policies"].values():
        for key in (
            "event_fraction",
            "hide_event_fraction",
            "reset_event_fraction",
            "state_rmse",
            "hide_recovery_error",
            "reset_recovery_error",
            "combined_recovery_error",
            "hide_strength",
            "reset_strength",
        ):
            assert math.isfinite(metrics[key])
        assert 0.0 <= metrics["event_fraction"] <= 1.0
        assert 0.0 <= metrics["hide_event_fraction"] <= 1.0
        assert 0.0 <= metrics["reset_event_fraction"] <= 1.0


def test_v1_context_event_budgets_are_approximately_matched():
    result = run_v1()["policies"]
    hide_rates = [m["hide_event_fraction"] for m in result.values()]
    reset_rates = [m["reset_event_fraction"] for m in result.values()]
    assert max(hide_rates) - min(hide_rates) <= 0.08
    assert max(reset_rates) - min(reset_rates) <= 0.08
