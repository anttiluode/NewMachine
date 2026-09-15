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

v1 gives the machine two explicit contexts.

**HIDE:** the current internal representation is correct, but output should be muted temporarily.

**RESET:** the input is contaminated, so the internal state itself should be corrected rather than merely hidden.

The result is deliberately interpreted narrowly. Threshold-side control preserves resident state in HIDE; state-side control repairs resident state in RESET. The oracle hybrid is handed the context label and simply selects the appropriate specialist.

| metric | basket only | chandelier only | oracle hybrid |
| --- | ---: | ---: | ---: |
| state RMSE | 0.09446 | 0.10206 | **0.04914** |
| HIDE recovery error | 0.15603 | **0.0000016** | **0.0000008** |
| RESET recovery error | **0.10148** | 0.21077 | **0.10148** |

The earlier mean recovery summary and percentage reductions are arithmetic restatements of these context cells, not independent evidence. v1 therefore earns only:

> **Once the gated variable has memory, intervention site changes future computation. Given an oracle context label, the appropriate specialist is context-dependent.**

See [`RESULTS_V1.md`](RESULTS_V1.md).

## v2 — attack the framing

Before adding a learned controller, v2 adds the cheapest controls that could collapse the story.

### One signed scalar

A single command `q_t` can route by sign:

```text
q < 0  -> state-side intervention
q > 0  -> publication-side intervention
q = 0  -> no-op
```

The frozen control asks whether this one-dimensional controller signal reproduces the v1 oracle hybrid exactly. If it does, two independent controller output channels are unnecessary; the essential object is still access to two intervention sites.

### Both sites at RESET

The publication gate cannot improve hidden-state recovery because it does not alter hidden state. Its only possible extra value is to suppress publications while state-side repair is settling.

v2 therefore keeps basket repair identical and sweeps an additional publication hold through RESET plus a fixed post-RESET recovery window. The strict comparison is against the clean reference event stream, so simply muting everything cannot count as a free win.

See [`RESULTS_V2.md`](RESULTS_V2.md) once the frozen receipt is run.

## What this currently means

The useful abstraction is not "AIS = attention." It is a stateful machine in which **changing computation** and **changing publication** are distinct interventions once memory exists.

Whether those interventions require two independently controlled channels, whether they have a simultaneous-use advantage, and whether context can be inferred rather than handed in are separate questions. v2 handles the first two before any learned controller is introduced.

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
```

## Repository map

- `src/new_machine/core.py` — persistent state + two intervention sites + signed control router + dynamic knee
- `src/new_machine/task.py` — deterministic streams, recovery metrics, and recovery-hold masks
- `experiments/run_v0.py` — equivalence/divergence receipt
- `experiments/run_v1.py` — oracle context-specialist receipt
- `experiments/run_v2.py` — signed-scalar and simultaneous-control adversarial receipt
- `tests/` — mechanism and receipt regressions
- `RESULTS_V0.md`, `RESULTS_V1.md`, `RESULTS_V2.md` — measured results and claim boundaries
- `docs/superpowers/` — frozen designs and implementation plans
