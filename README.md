# NewMachine

> AI inspired by random thoughts on neurons, with the biology stripped down until the computation can fail cleanly.

NewMachine asks whether a persistent internal state and its permission to become an output event should be controlled at the same place.

The biological inspiration is the contrast between perisomatic/basket-like inhibition and AIS/chandelier-like inhibition. This repository does **not** claim those cell types literally implement these equations.

The live v4 sender/receiver laboratory is served from the repository root on GitHub Pages.

## Core unit

A unit has persistent state:

```text
x_t = alpha * x_(t-1) + (1-alpha) * u_t - basket_t
```

and a simple dynamic output knee:

```text
slope_t = x_t - x_(t-1)
theta_t = theta0 + chandelier_t - slope_gain * max(slope_t, 0)
event_t = 1[x_t > theta_t]
```

So there are two intervention sites:

```text
basket-like      -> change resident state
chandelier-like  -> change whether resident state is published
```

## v0 — when do the two gates differ?

If there is no memory (`alpha=0`) and no slope-sensitive knee, the distinction disappears exactly:

```text
1[u - q > theta] == 1[u > theta + q]
```

v0 verifies this directly. Persistence then breaks the equivalence.

| gate | result |
| --- | --- |
| static identity | exact equivalence |
| basket recovery scar | **0.093128** |
| chandelier hidden-state scar | **0.000000** |
| slow ramp to 0.75 | no event |
| fast step to 0.75 | event |

See [`RESULTS_V0.md`](RESULTS_V0.md).

## v1 — oracle context specialists

v1 gives the machine explicit HIDE and RESET labels. Threshold-side control preserves resident state in HIDE; state-side control repairs resident state in RESET. The oracle hybrid simply selects the appropriate specialist.

| metric | basket only | chandelier only | oracle hybrid |
| --- | ---: | ---: | ---: |
| state RMSE | 0.09446 | 0.10206 | **0.04914** |
| HIDE recovery error | 0.15603 | **0.0000016** | **0.0000008** |
| RESET recovery error | **0.10148** | 0.21077 | **0.10148** |

The old mean-recovery percentages are arithmetic restatements, not separate evidence. The earned statement is only:

> **Once the gated variable has memory, intervention site changes future computation. Given an oracle context label, the appropriate specialist is context-dependent.**

See [`RESULTS_V1.md`](RESULTS_V1.md).

## v2 — attack the framing

v2 asks whether the controller itself really needs two channels.

A single signed scalar reproduces the v1 oracle hybrid exactly:

```text
q < 0  -> state-side intervention
q > 0  -> publication-side intervention
```

Across held-out seeds: zero state difference, zero threshold difference, zero event mismatches.

Then v2 tests both sites simultaneously during RESET. Extra publication gating can reduce event exposure from about `0.171` toward `0`, but disagreement with the clean reference event stream rises from about `0.365` toward `0.536`; hidden-state recovery remains fixed. So there is no free simultaneous-gating win in that task.

See [`RESULTS_V2.md`](RESULTS_V2.md).

## v3 — independent reliability and publication constraints

v3 changes the geometry of the problem. Publication relevance and input reliability are now **independent factors** that can overlap:

```text
public + clean      -> no control
private + clean     -> publication gate
public + corrupt    -> state repair
private + corrupt   -> both simultaneously
```

The private/relevance bit is supplied as context. Corruption is inferred from a simple local prediction residual; a threshold selected only on training seeds reaches held-out corruption F1 `0.812810`.

The key comparison is against a one-signed-scalar reset-priority controller. `factorized` and `reset_priority_signed` make the same state-repair decisions, so their state RMSE and public-event mismatch are exactly equal. But factorized control can still suppress publication when privacy and corruption overlap:

| policy | state RMSE | private event fraction | public event mismatch | overlap event fraction |
| --- | ---: | ---: | ---: | ---: |
| reset-priority signed | **0.084754** | 0.074726 | 0.147544 | 0.125606 |
| **factorized** | **0.084754** | **0.055449** | 0.147544 | **0.033585** |

That is a **25.8%** reduction in private-window events and a **73.3%** reduction in overlap events with no change in state RMSE or public-event fidelity.

This is the first gate where simultaneously available state-side and output-side control does something the exclusive sign router cannot reproduce in one step.

See [`RESULTS_V3.md`](RESULTS_V3.md).

## v4 — give publication a receiver

v4 adds the consumer missing from v0-v3. A predictive receiver advances its own state while silent and is corrected only when a sender event is published.

The world also makes relevance concrete rather than merely scoring an event mask:

```text
public truth   -> state the receiver should reconstruct
local truth    -> public truth + valid sender-only state during private windows
corruption     -> independently contaminates the sender observation
```

At the frozen default event threshold `0.04`, averaged over eight seeds:

| policy | receiver RMSE | event fraction | recovery RMSE |
| --- | ---: | ---: | ---: |
| dense | 0.145569 | 1.000000 | 0.228492 |
| delta | 0.146279 | 0.150000 | 0.242894 |
| signed repair-first | 0.038569 | 0.027292 | 0.037005 |
| factorized repair + publication | **0.038210** | **0.027083** | **0.036623** |

The large effect is **state repair before communication**: receiver RMSE falls by about `73.6%` versus ordinary delta triggering for `signed`, and `73.9%` for `factorized` in this constructed world.

The extra publication site is a smaller result. `factorized` extends the receiver-error/message-rate frontier over `signed` at **4 of 7** frozen thresholds, but it does not dominate everywhere. Its best RMSE improvement is about `0.000588`, and at one operating point it is about `0.000151` worse.

So v4 earns a narrower statement:

> **Persistent-state repair can sit underneath sparse delta communication and substantially improve what a receiver reconstructs when observations are intermittently corrupt. Independent publication control can add a small, threshold-dependent frontier extension when valid local-only state should not propagate.**

See [`RESULTS_V4.md`](RESULTS_V4.md).

## Live Pages laboratory

The repository root is now a dependency-free browser lab using the same deterministic v4 equations. It runs continuously through seeded epochs and shows:

- public truth, resident sender state, and predictive receiver state;
- corruption windows and valid local-only windows;
- repair decisions and sparse correction events;
- live sender/receiver error, message rate, and detector F1;
- the receiver-error versus message-rate frontier for all four policies.

The page is an inspection instrument. Python receipts remain the scientific authority, and the JavaScript mechanism is regression-tested against a fixed deterministic stream prefix.

## What this currently means

The useful abstraction is no longer merely "AIS = attention." It is a stateful sender/receiver machine in which **reliability**, **resident computation**, and **causal publication** are distinct variables:

```text
observation reliability -> repair/protect resident state
resident state           -> keeps evolving locally
publication relevance    -> decide whether influence propagates
receiver                  -> predicts while silent, corrects on events
```

Threshold event triggering and remote estimation already have mature literatures. NewMachine's narrower question is whether state repair and publication control remain separately useful around persistent AI state.

Oscillatory timing, fast controller networks, dendritic modes, Oja specialization, sparse grown routing, vector-valued models, and biological claims remain deliberately outside v4.

## Lineage

```text
AnttisNeuron
    dendritic modes / persistent physical state

GrowingAnttisNeuron
    grow sparse wiring and physical operators

ActiveVectorNN
    state can remain resident while only changes are communicated

NewMachine
    separate resident-state repair from publication, then give it a receiver
```

## Run

```bash
python -m pip install -e ".[test]"
pytest -q
node tests/web_sim_test.mjs
python -m experiments.run_v0
python -m experiments.run_v1
python -m experiments.run_v2
python -m experiments.run_v3
python -m experiments.run_v4
```

## Repository map

- `src/new_machine/core.py` — persistent scalar state + two intervention sites + dynamic knee
- `src/new_machine/task.py` — deterministic v0-v3 streams, residuals, and recovery metrics
- `src/new_machine/receiver.py` — deterministic v4 sender/receiver world, repair and sparse publication policies
- `experiments/run_v0.py` through `experiments/run_v4.py` — frozen scientific receipts
- `index.html` — GitHub Pages live laboratory
- `web/sim.mjs` — deterministic browser mirror of v4 equations
- `web/app.mjs` — live animation, metrics and frontier rendering
- `web/style.css` — static lab presentation
- `tests/` — mechanism, receipt, browser-parity and Pages-structure regressions
- `RESULTS_V0.md` through `RESULTS_V4.md` — measured results and claim boundaries
- `docs/superpowers/` — frozen designs and implementation plans
