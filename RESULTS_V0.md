# NewMachine v0 Results — Two Gates

v0 asks one narrow question: **when do state-side inhibition and output-threshold inhibition become computationally different?**

The answer is: not in a memoryless threshold unit, but immediately once hidden state persists.

## Gate 0 — exact static equivalence

With `alpha=0` and no slope sensitivity,

```text
1[u - q > theta]
```

and

```text
1[u > theta + q]
```

produce exactly the same event decisions over the frozen sweep.

Result: **equivalent = true**.

This is the critical control. The two mechanisms are not declared different by notation.

## Gate 1 — persistence breaks the equivalence

A matched one-step control pulse is applied after the recurrent state has settled.

Mean recovery error over the following 12 steps:

| gate | recovery error |
| --- | ---: |
| basket/state-side | **0.093128** |
| chandelier/threshold-side | **0.000000** |

Basket-like inhibition changes the recurrent state, so its effect decays through future time. Threshold-side inhibition leaves the hidden state exactly on the ungated trajectory.

## Gate 2 — dynamic knee

Two inputs reach the same peak activation `0.75`:

- a slow ramp to 0.75;
- a fast step from 0 to 0.75.

With a positive slope term in the event boundary:

- slow ramp produces no event;
- fast step produces an event.

This is an engineering abstraction of a rate-sensitive output knee. It is not claimed as a biophysical AIS equation.

## Gate 3 — frozen matched-suppression task

The task contains slow persistent background, mute-context windows, and short target transients immediately after mute windows. Control strengths are selected on training seeds only to approach a mute-window event fraction of `0.10`; metrics below are from held-out seeds 100–111.

| metric | basket-like | chandelier-like |
| --- | ---: | ---: |
| selected strength | 0.02 | 0.12 |
| overall event fraction | 0.46278 | 0.49188 |
| mute-window event fraction | 0.18240 | 0.12470 |
| target F1 | 0.03986 | **0.07237** |
| hidden-state RMSE vs ungated | 0.05426 | **0.00000** |
| post-mute recovery error | 0.07837 | **0.00000** |

The absolute F1 values are low, so Gate 3 is **not** an attention-performance claim. It is a mechanism probe. The useful result is that output-threshold gating suppresses publication without corrupting the resident state, whereas state-side inhibition changes the future trajectory.

The event budgets are only approximately matched on held-out seeds, so the F1 difference should be treated as suggestive rather than decisive.

## What v0 supports

```text
stateless unit:
    subtract from state == raise threshold, for output decisions

persistent unit:
    subtract from state != raise threshold
```

That means the anatomical placement of a gate can correspond to a real computational distinction once a unit has persistent internal state.

## What v0 does not support

- It does not show that chandelier cells are transformer attention.
- It does not show that threshold-side gating is always superior; tasks that require removing irrelevant content from state may favor state-side inhibition.
- It does not model oscillations, basket/chandelier networks, dendritic eigenmodes, Oja learning, or developmental wiring.
- It does not establish a biological mechanism from these normalized equations.

The next useful question is whether the two gates become **complementary** when the task sometimes requires preserving a hidden representation and sometimes requires actively erasing or suppressing it.