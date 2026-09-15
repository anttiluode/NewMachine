# NewMachine v1 Complementary Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether state-side and output-threshold gates become complementary when one context requires preserving hidden state and another requires correcting hidden state.

**Architecture:** Extend the deterministic task generator with labeled HIDE and RESET windows plus a clean reference stream. Evaluate basket-only, chandelier-only, and context-switched hybrid policies under train-only budget calibration and held-out scientific metrics.

**Tech Stack:** Python 3.11+, NumPy, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-complementary-gates-design.md`

## Global Constraints

- v0 behavior and receipt remain unchanged.
- Tests before implementation.
- Controller receives context labels directly; no learning.
- Policy multipliers are selected on training seeds only.
- Scientific outcome is recorded, not used as CI pass/fail.

---

### Task 1: Complementary task stream

**Files:**
- Modify: `src/new_machine/task.py`
- Test: `tests/test_complementary_task.py`

- [ ] Add failing tests for deterministic clean/observed streams, non-overlapping HIDE/RESET masks, RESET-only contamination, and valid post-context windows.
- [ ] Verify RED.
- [ ] Add `make_complementary_stream(seed, steps)` returning `(clean, observed, hide, reset)`.
- [ ] Verify GREEN and all v0 regressions.

### Task 2: Frozen v1 policy experiment

**Files:**
- Create: `experiments/run_v1.py`
- Test: `tests/test_v1_receipt.py`

- [ ] Add failing tests requiring deterministic policy accounting, finite metrics, disjoint train/test seeds, and approximate event-budget matching.
- [ ] Verify RED.
- [ ] Implement basket-only, chandelier-only, and hybrid policies with train-only multiplier selection.
- [ ] Verify GREEN.

### Task 3: Document and verify

**Files:**
- Create: `RESULTS_V1.md`
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`

- [ ] Run full `pytest -q`, v0 receipt, and v1 receipt fresh.
- [ ] Record the actual held-out result and limitations.
- [ ] Add frozen v1 receipt to CI.
- [ ] Open PR and merge only after Python 3.11 and 3.12 both reproduce tests and both receipts.