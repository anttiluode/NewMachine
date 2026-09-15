# NewMachine v3 Results — Factorized Context and Reliability Control

v2 showed that the oracle HIDE/RESET switch could be collapsed into one signed scalar because those contexts were mutually exclusive. v3 asks whether that collapse survives when two independent control requirements can occur at the same time.

## Four regimes

The stream contains two independent factors:

- `private`: publication should be suppressed;
- `corrupt`: the observed input is unreliable and resident state should be repaired.

They can overlap:

```text
public + clean      -> no control
private + clean     -> publication gate
public + corrupt    -> state repair
private + corrupt   -> both simultaneously
```

The `private` bit is provided as an exogenous context signal. The corruption label is hidden from the controller.

## Corruption detector

A one-state passive predictor computes the causal residual

```text
residual_t = observed_t - predictor_state_(t-1)
```

A scalar threshold is selected on training seeds 20–29 from a frozen grid. The selected threshold is:

```text
0.08
```

On held-out seeds 200–219 the corruption detector reaches mean F1:

```text
0.812810
```

This is deliberately not presented as a sophisticated learned controller. One scalar local residual already carries most of the corruption information in this toy.

## Policies

All policies use the same fixed magnitudes:

- state repair: `0.08`;
- publication gate: `0.16`.

Compared policies:

- `none`;
- `innovation_only`;
- `context_only`;
- `reset_priority_signed` — one signed scalar, repair wins on overlap;
- `hide_priority_signed` — one signed scalar, publication suppression wins on overlap;
- `factorized` — reliability controls state repair and privacy context controls publication independently, so both can be active in the same step.

## Held-out result

| policy | state RMSE | private event fraction | public event mismatch | overlap event fraction | overlap state abs. error |
| --- | ---: | ---: | ---: | ---: | ---: |
| none | 0.142363 | 0.705617 | **0.144601** | 0.983986 | 0.279162 |
| innovation only | 0.084754 | 0.456095 | 0.147544 | 0.216127 | **0.116918** |
| context only | 0.142363 | 0.282681 | **0.144601** | 0.839166 | 0.279162 |
| reset-priority signed | **0.084754** | 0.074726 | 0.147544 | 0.125606 | **0.116918** |
| hide-priority signed | 0.096645 | 0.201244 | 0.152960 | 0.685585 | 0.206143 |
| **factorized** | **0.084754** | **0.055449** | 0.147544 | **0.033585** | **0.116918** |

## Primary comparison

`factorized` and `reset_priority_signed` use the **same corruption detector and the same state-repair decision on every step**. Therefore their state trajectories and all public-window behavior are expected to match exactly.

They do:

```text
state RMSE difference              = 0
public event mismatch difference   = 0
```

But in private windows, the factorized controller can still apply publication suppression even when state repair is also active.

That yields:

```text
private-window event reduction = 25.80%
overlap event reduction        = 73.26%
```

The pre-registered v3 gate required at least 10% and 25%, respectively, while preserving state RMSE and public-event mismatch. **Passed.**

## What v3 earns

This is the first NewMachine result where the two-site architecture does something the one-signed-scalar exclusive router cannot reproduce in one step.

The reason is not mysterious: the objectives are independent.

```text
reliability signal  -> repair resident state
privacy/context     -> suppress publication
```

When both conditions hold, both interventions are needed at once.

So the surviving architectural statement becomes:

> **Independent reliability and publication constraints can require simultaneous access to state-side and output-side control, even when each individual decision is simple.**

## Limits

This is still a toy. The private/relevance context bit is given directly; it is not inferred. Corruption detection is a calibrated scalar threshold. Control-actuation cost is not modeled. The benchmark is not a claim of superiority over established event-triggered estimation or remote-estimation methods.

The relevant prior-art boundary is explicit: threshold event triggering for remote estimation under communication cost is already well developed. The narrower object here is the coexistence of a reliability-driven state intervention and a context-driven publication intervention.

No gamma/theta, Oja specialization, dendritic modes, grown routing, or biological validation is introduced in v3.
