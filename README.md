# NewMachine

> AI inspired by random thoughts on neurons, with the biology stripped down until the computation can fail cleanly.

NewMachine starts from one question:

> **Does it matter whether a controller changes a persistent internal state, or only changes whether that state is allowed to become an output event?**

The biological inspiration is the contrast between perisomatic/basket-like inhibition and AIS/chandelier-like inhibition. This repository does **not** claim those cell types literally implement these equations.

## v0 machine

A unit has persistent state:

```text
x_t = alpha * x_(t-1) + (1-alpha) * u_t - basket_t
```

A simple dynamic output knee is:

```text
slope_t = x_t - x_(t-1)
theta_t = theta0 + chandelier_t - slope_gain * max(slope_t, 0)
event_t = 1[x_t > theta_t]
```

So there are two physically different places to act:

```text
basket-like      -> change the state itself
chandelier-like  -> change whether the state is published
```

## The important control

If there is no memory (`alpha=0`) and no slope-sensitive knee, the distinction disappears exactly:

```text
1[u - q > theta] == 1[u > theta + q]
```

v0 verifies this directly.

Persistence then breaks that equivalence. A state-side inhibitory pulse leaves a decaying scar in future state; an output-threshold pulse leaves the hidden trajectory untouched.

## Frozen v0 receipt

| gate | result |
| --- | --- |
| Gate 0: static identity | exact equivalence |
| Gate 1: basket recovery scar | **0.093128** |
| Gate 1: chandelier state scar | **0.000000** |
| Gate 2: slow ramp to 0.75 | no event |
| Gate 2: fast step to 0.75 | event |

The held-out Gate-3 toy task also favored threshold-side gating under approximate matched suppression (`F1 0.07237` vs `0.03986`), but the absolute F1 is low and the held-out event budgets are not perfectly equal. Treat that as a mechanism hint, not an AI-performance claim.

See [`RESULTS_V0.md`](RESULTS_V0.md) for the full interpretation.

## Why this exists

The lineage is:

```text
AnttisNeuron
    dendritic modes / persistent physical state

GrowingAnttisNeuron
    grow the sparse wiring and operator

ActiveVectorNN
    state can remain resident while only changes are communicated

NewMachine
    separate the control that changes resident state
    from the control that permits resident state to broadcast
```

The interesting architectural possibility is not "AIS = transformer attention." It is a system with separate **state plane** and **control plane**:

```text
persistent representation
        |
        +-- state-side control: alter computation
        |
        +-- output-side control: alter publication
```

v0 nails down only that distinction. Oscillatory timing, fast interneuron-like controller networks, dendritic modes, Oja specialization, and sparse grown routing are deliberately absent until this primitive survives.

## Run

```bash
python -m pip install -e ".[test]"
pytest -q
python -m experiments.run_v0
```

## Repository map

- `src/new_machine/core.py` — persistent state + two control locations + dynamic knee
- `src/new_machine/task.py` — deterministic mute/recovery stream and metrics
- `experiments/run_v0.py` — frozen scientific receipt
- `tests/` — mechanism and receipt regressions
- `RESULTS_V0.md` — measured result and claim boundary
- `docs/superpowers/` — frozen design and implementation plan
