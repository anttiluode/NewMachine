# NewMachine

> AI inspired by random thoughts on neurons, with the biology stripped down until the computation can fail cleanly.

NewMachine asks whether a persistent internal state and its permission to become an output event should be controlled at the same place.

The biological inspiration is the contrast between perisomatic/basket-like inhibition and AIS/chandelier-like inhibition. This repository does **not** claim those cell types literally implement these equations.

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

## What this currently means

The useful abstraction is not "AIS = attention." It is a stateful machine where **reliability** and **publication relevance** can be separate control variables:

```text
reliability signal  -> alter resident state
context/relevance   -> alter publication
```

When those requirements are independent, both interventions may be needed at once.

This is still a toy, and threshold event triggering / remote estimation already have a mature control-theory literature. NewMachine's narrower question is whether a persistent AI unit benefits from separating state repair from publication control.

Oscillatory timing, fast controller networks, dendritic modes, Oja specialization, sparse grown routing, and biological claims remain deliberately outside the current machine.

## Lineage

```text
AnttisNeuron
    dendritic modes / persistent physical state

GrowingAnttisNeuron
    grow sparse wiring and physical operators

ActiveVectorNN
    state can remain resident while only changes are communicated

NewMachine
    separate control of resident state from control of publication
```

## Run

```bash
python -m pip install -e ".[test]"
pytest -q
python -m experiments.run_v0
python -m experiments.run_v1
python -m experiments.run_v2
python -m experiments.run_v3
```

## Repository map

- `src/new_machine/core.py` — persistent state + two intervention sites + signed control router + dynamic knee
- `src/new_machine/task.py` — deterministic streams, residuals, and recovery metrics
- `experiments/run_v0.py` — equivalence/divergence receipt
- `experiments/run_v1.py` — oracle context-specialist receipt
- `experiments/run_v2.py` — adversarial signed-scalar/simultaneous-control receipt
- `experiments/run_v3.py` — factorized context/reliability receipt
- `tests/` — mechanism and receipt regressions
- `RESULTS_V0.md` through `RESULTS_V3.md` — measured results and claim boundaries
- `docs/superpowers/` — frozen designs and implementation plans
