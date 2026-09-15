# NewMachine v3 design — factorized context and reliability control

## Why v3 exists

v2 showed two things:

1. the v1 oracle switch can be encoded in one signed scalar because HIDE and RESET were mutually exclusive;
2. simultaneous state repair + publication hold did not give a free win when the target remained clean-reference event fidelity.

That leaves a more interesting case: two independent requirements can be true at the same time.

## Four regimes

The stream now carries two independent factors:

- **privacy / relevance context**: whether publication should be suppressed;
- **input corruption**: whether the observed value is unreliable and resident state should be repaired.

They create four regimes:

```text
public + clean      -> no control
private + clean     -> publication gate
public + corrupt    -> state repair
private + corrupt   -> both gates simultaneously
```

The private bit is supplied as an exogenous context signal. Corruption is **not** supplied as a label. It must be inferred from a local one-dimensional prediction residual.

## Detector

A passive local predictor tracks the observed stream with the same persistence constant. Before each update:

```text
residual_t = observed_t - predictor_state_(t-1)
```

A positive threshold is selected on training seeds only from a frozen grid to maximize corruption-mask F1. The detector is intentionally simple; if one scalar residual threshold is sufficient, report that rather than pretending the controller learned a rich representation.

## Policies

Use the same fixed intervention magnitudes as v1/v2:

- state repair magnitude: `0.08`;
- publication gate magnitude: `0.16`.

Compare:

- `none`;
- `innovation_only`: inferred corruption -> state repair;
- `context_only`: private context -> publication gate;
- `reset_priority_signed`: one-site-at-a-time signed controller; repair wins on overlap;
- `hide_priority_signed`: one-site-at-a-time signed controller; publication gate wins on overlap;
- `factorized`: inferred corruption controls state repair and private context independently controls publication, so both may be active simultaneously.

## Held-out metrics

Report:

- corruption detector F1;
- state RMSE versus clean reference;
- event fraction during private windows;
- event mismatch versus clean reference on public windows only;
- event fraction in private+corrupt overlap;
- state error in private+corrupt overlap.

The primary comparison is `factorized` versus `reset_priority_signed`, because both use exactly the same corruption detector and therefore have identical state-repair decisions. Any difference in state trajectory or public-event mismatch is a bug.

## Pre-registered primary gate

On held-out seeds, require:

1. factorized state RMSE equals reset-priority state RMSE within `1e-12`;
2. factorized public-event mismatch equals reset-priority within `1e-12`;
3. factorized private-window event fraction is at least 10% lower than reset-priority;
4. factorized overlap event fraction is at least 25% lower than reset-priority.

This tests whether simultaneous access to both intervention sites adds a capability that one signed scalar with exclusive routing cannot reproduce when two independent control objectives overlap.

## Limits

The private/relevance context bit is given; this is not autonomous attention. The corruption detector is a calibrated scalar threshold, not a neural controller. Gate actuation cost is not modeled. No oscillations, Oja rule, dendritic modes, grown routing, or biological validation are added here.

## Prior-art boundary

Threshold event-triggering and remote estimation under communication cost are established control-theory topics. v3 therefore does not claim novelty for residual thresholding. The narrower question is whether independent reliability and publication constraints create a useful reason to keep state-side and output-side actuation separately available.
