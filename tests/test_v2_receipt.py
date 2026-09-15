from experiments.run_v2 import run_v2


def test_v2_signed_scalar_is_exact_hybrid_control():
    result = run_v2()
    signed = result["signed_scalar_control"]
    assert signed["max_state_difference"] == 0.0
    assert signed["max_threshold_difference"] == 0.0
    assert signed["event_mismatch_count"] == 0


def test_v2_simultaneous_gate_does_not_change_repaired_state():
    result = run_v2()
    sweep = result["simultaneous_reset_sweep"]
    assert all(row["max_state_difference_vs_basket"] == 0.0 for row in sweep)
    recoveries = [row["reset_recovery_error"] for row in sweep]
    assert max(recoveries) - min(recoveries) < 1e-15


def test_v2_extra_output_gating_trades_events_for_clean_event_fidelity():
    result = run_v2()
    sweep = result["simultaneous_reset_sweep"]
    baseline = sweep[0]
    strongest = sweep[-1]
    assert strongest["exposure_event_fraction"] < baseline["exposure_event_fraction"]
    assert strongest["clean_event_mismatch_fraction"] > baseline["clean_event_mismatch_fraction"]
    assert result["simultaneous_free_win_found"] is False
