# NewMachine v4 Live Receiver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic sender/receiver v4 experiment and a static GitHub Pages lab that visualizes the same equations continuously.

**Architecture:** Add an isolated receiver/simulation module in Python for authoritative receipts, mirror the deterministic equations in a dependency-free ES module, and keep DOM/canvas rendering separate. Compare dense, delta, signed, and factorized policies on identical streams; judge them by downstream reconstruction versus communication rate.

**Tech Stack:** Python 3.11/3.12, NumPy, pytest, vanilla ES modules, Node syntax/runtime checks, HTML/CSS canvas UI, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-09-15-v4-live-receiver-design.md`

## Global Constraints

- No backend and no browser dependencies.
- Python receipts are authoritative; browser code must use matching deterministic equations.
- State repair and publication control must remain independently measurable.
- v4 adds no learning, oscillations, dendritic modes, grown wiring, or model APIs.
- Scientific failure is retained rather than tuned away.

---

### Task 1: Authoritative sender/receiver mechanism

**Files:**
- Create: `tests/test_receiver.py`
- Create: `src/new_machine/receiver.py`

**Interfaces:**
- Produces: `simulate_policy(seed, policy, event_threshold, steps) -> dict[str, object]`
- Produces: `run_frontier(seed, thresholds, steps) -> dict[str, list[dict[str, float]]]`

- [ ] **Step 1: Write failing tests** asserting deterministic replay, receiver coasting, publication suppression preserving sender state, and factorized simultaneous repair+suppress behavior.
- [ ] **Step 2: Run `pytest tests/test_receiver.py -q`** and verify failure is because `new_machine.receiver` does not exist.
- [ ] **Step 3: Implement the minimal deterministic PRNG, stream, four policies, sender state, receiver predictor, event accounting, and metrics.**
- [ ] **Step 4: Run `pytest tests/test_receiver.py -q` and full `pytest -q`; both must pass.**

### Task 2: Frozen v4 scientific receipt

**Files:**
- Create: `tests/test_v4_receipt.py`
- Create: `experiments/run_v4.py`
- Create: `RESULTS_V4.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: `simulate_policy` and `run_frontier` from Task 1.
- Produces: deterministic JSON receipt printed by `python -m experiments.run_v4`.

- [ ] **Step 1: Write a failing receipt regression test** for schema, deterministic seed bank, and honest invariants rather than an assumed scientific winner.
- [ ] **Step 2: Run the focused test and verify failure because `experiments.run_v4` is absent.**
- [ ] **Step 3: Implement the v4 runner, record the measured results in `RESULTS_V4.md`, update README claim boundaries, and add the receipt to CI.**
- [ ] **Step 4: Run the full test suite and v0-v4 receipts.**

### Task 3: Browser simulation core

**Files:**
- Create: `tests/web_sim_test.mjs`
- Create: `web/sim.mjs`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `createWorld(seed)`, `stepPolicy(world, policy, threshold)`, `simulate(policy, seed, threshold, steps)`, `frontier(seed, thresholds, steps)`.

- [ ] **Step 1: Write Node tests** for deterministic replay, private-window suppression, and fixed known stream prefix shared with Python.
- [ ] **Step 2: Add the Node test command to CI and verify it fails because `web/sim.mjs` is absent.**
- [ ] **Step 3: Implement the minimum ES module using the exact v4 equations and explicit PRNG.**
- [ ] **Step 4: Run Node tests and Python tests; both must pass.**

### Task 4: Live GitHub Pages laboratory

**Files:**
- Create: `index.html`
- Create: `web/style.css`
- Create: `web/app.mjs`
- Create: `tests/web_page_test.py`

**Interfaces:**
- Consumes: pure simulation exports from `web/sim.mjs`.
- Produces: static Pages UI at repository root.

- [ ] **Step 1: Write failing structural tests** requiring the root page, module script, policy controls, metric elements, canvas, and no external runtime dependencies.
- [ ] **Step 2: Run the structural test and verify it fails because `index.html` is absent.**
- [ ] **Step 3: Implement an accessible dark live lab** with animated traces for truth/sender/receiver, corruption/privacy bands, transmission flashes, pause/step/reset/seed/policy controls, live metrics, and a frontier canvas.
- [ ] **Step 4: Run Python tests, Node tests, and `node --check web/app.mjs`; all must pass.**

### Task 5: Integration verification

**Files:**
- Modify only if verification exposes a defect.

- [ ] **Step 1: Run all Python tests and v0-v4 receipts.**
- [ ] **Step 2: Run Node simulation tests and syntax checks.**
- [ ] **Step 3: Inspect GitHub Actions on the branch/PR and fix only reproducible failures.**
- [ ] **Step 4: Review the final diff for claim inflation, dependency leakage, and mismatch between browser and Python equations.**
