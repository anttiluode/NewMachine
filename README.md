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

## v1 — why have both gates?

v1 gives the machine two explicit contexts.

**HIDE:** the current internal representation is correct, but output should be muted temporarily.

**RESET:** the input is contaminated, so the internal state itself should be corrected rather than merely hidden.

Three policies are compared at approximately matched control-window event budgets:

- basket-only: state-side control everywhere;
- chandelier-only: threshold-side control everywhere;
- hybrid: threshold-side in HIDE, state-side in RESET.

Held-out result:

| metric | basket only | chandelier only | hybrid |
| --- | ---: | ---: | ---: |
| state RMSE | 0.09446 | 0.10206 | **0.04914** |
| HIDE recovery error | 0.15603 | **0.0000016** | **0.0000008** |
| RESET recovery error | **0.10148** | 0.21077 | **0.10148** |
| combined recovery error | 0.12875 | 0.10538 | **0.05074** |

The policies cross by context exactly as the mechanism predicts. Threshold-side control wins when the hidden state should survive; state-side control wins when the hidden state should be altered. The hybrid uses each at the appropriate context and roughly halves combined recovery error versus either single-gate policy.

See [`RESULTS_V1.md`](RESULTS_V1.md).

## What this currently means

The useful abstraction is no longer "AIS = attention." It is a machine with separate **state plane** and **publication-control plane**:

```text
persistent representation
        |
        +-- state-side control: alter computation
        |
        +-- output-side control: alter publication
```

v0 establishes that these are not distinct operations in a stateless threshold unit. v1 establishes that once state persists, having both intervention sites can be useful because different contexts require opposite actions.

The controller in v1 is handed the HIDE/RESET label. It does not learn context. Oscillatory timing, fast controller networks, dendritic modes, Oja specialization, sparse grown routing, and learned gate selection remain future questions.

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
```

## Repository map

- `src/new_machine/core.py` — persistent state + two control locations + dynamic knee
- `src/new_machine/task.py` — v0 and v1 deterministic streams and metrics
- `experiments/run_v0.py` — equivalence/divergence receipt
- `experiments/run_v1.py` — complementary-gate receipt
- `tests/` — mechanism and receipt regressions
- `RESULTS_V0.md`, `RESULTS_V1.md` — measured results and claim boundaries
- `docs/superpowers/` — frozen designs and implementation plans
