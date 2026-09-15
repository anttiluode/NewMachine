from __future__ import annotations

import numpy as np

from new_machine.receiver import simulate_policy


def test_simulation_is_deterministic_for_same_seed():
    first = simulate_policy(seed=7, policy="factorized", event_threshold=0.08, steps=600)
    second = simulate_policy(seed=7, policy="factorized", event_threshold=0.08, steps=600)

    assert first["metrics"] == second["metrics"]
    for key in (
        "truth",
        "local_truth",
        "observed",
        "sender",
        "receiver",
        "private",
        "corrupt",
        "events",
    ):
        assert np.array_equal(first["trace"][key], second["trace"][key])


def test_private_windows_can_contain_valid_local_only_state():
    result = simulate_policy(seed=13, policy="factorized", event_threshold=0.04, steps=700)
    trace = result["trace"]
    private_clean = trace["private"] & ~trace["corrupt"]

    assert np.any(private_clean)
    assert np.any(np.abs(trace["local_truth"][private_clean] - trace["truth"][private_clean]) > 0.05)

    sender_rmse = float(np.sqrt(np.mean((trace["sender"] - trace["local_truth"]) ** 2)))
    receiver_rmse = float(np.sqrt(np.mean((trace["receiver"] - trace["truth"]) ** 2)))
    assert np.isclose(result["metrics"]["sender_rmse"], sender_rmse)
    assert np.isclose(result["metrics"]["receiver_rmse"], receiver_rmse)


def test_factorized_policy_can_repair_and_suppress_on_same_step():
    result = simulate_policy(seed=11, policy="factorized", event_threshold=0.0, steps=900)
    trace = result["trace"]
    overlap = trace["private"] & trace["detected_corrupt"]

    assert np.any(overlap)
    assert np.all(trace["repaired"][overlap])
    assert not np.any(trace["events"][overlap])


def test_publication_suppression_does_not_change_sender_state():
    factorized = simulate_policy(seed=19, policy="factorized", event_threshold=0.0, steps=900)
    signed = simulate_policy(seed=19, policy="signed", event_threshold=0.0, steps=900)

    f = factorized["trace"]
    s = signed["trace"]
    same_repair_decision = f["repaired"] == s["repaired"]

    assert np.all(same_repair_decision)
    assert np.allclose(f["sender"], s["sender"], atol=0.0, rtol=0.0)


def test_receiver_coasts_when_no_event_is_published():
    result = simulate_policy(seed=23, policy="factorized", event_threshold=0.12, steps=700)
    trace = result["trace"]

    silent = ~trace["events"]
    assert np.any(silent[1:])
    expected = 0.995 * trace["receiver"][:-1] + 0.005 * 0.55
    mask = silent[1:]
    assert np.allclose(trace["receiver"][1:][mask], expected[mask])


def test_dense_policy_publishes_every_step():
    result = simulate_policy(seed=3, policy="dense", event_threshold=999.0, steps=240)
    assert np.all(result["trace"]["events"])
    assert result["metrics"]["event_fraction"] == 1.0
