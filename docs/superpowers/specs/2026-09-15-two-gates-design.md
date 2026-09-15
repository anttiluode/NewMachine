# NewMachine v0 — Two Gates Design

## Question

When are soma/state-side inhibition and AIS/output-threshold inhibition computationally different?

The biological inspiration is deliberately reduced to two operations:

- **basket-like control** changes the persistent state before output;
- **chandelier-like control** changes only the output threshold.

The experiment must first prove they are equivalent when persistence and slope sensitivity are absent. It then adds those ingredients one at a time and measures the divergence.

## Minimal unit

For input `u_t`, persistent state `x_t`, basket control `b_t`, chandelier control `c_t`:

```text
x_t = alpha * x_(t-1) + (1-alpha) * u_t - b_t
slope_t = x_t - x_(t-1)
theta_t = theta0 + c_t - slope_gain * max(slope_t, 0)
e_t = 1[x_t > theta_t]
```

Basket control therefore changes the state trajectory. Chandelier control leaves the state untouched and changes only whether the current state becomes an event.

## Frozen gates

### Gate 0 — static identity control

Set `alpha=0` and `slope_gain=0`. For matched `b_t=c_t=q_t`, compare:

```text
1[u_t - q_t > theta0]
1[u_t > theta0 + q_t]
```

They must be exactly identical for arbitrary deterministic inputs. If not, the implementation is wrong.

### Gate 1 — persistence separation

Set `alpha>0`, `slope_gain=0`. Give both units the same input and the same one-step inhibitory pulse chosen to suppress the same output event on that step.

After inhibition is removed, basket control must leave a decaying state scar while chandelier control leaves the hidden state equal to the unperturbed reference. Measure integrated absolute state error during recovery.

### Gate 2 — slope-sensitive knee

Hold peak activation fixed and compare a slow ramp with a fast step. With `slope_gain=0`, equal peak states have the same threshold relation. With positive `slope_gain`, the fast-rising event can cross threshold at a lower absolute state than the slow ramp.

This is an engineering abstraction of a rate-sensitive output knee, not a claim that the equation is a biophysical AIS model.

### Gate 3 — matched-budget task

Create a deterministic stream containing persistent slow background, mute-context windows, and brief target transients immediately after some mute windows. A controller marks mute windows.

Compare basket-like and chandelier-like gating over a frozen grid of control strengths. For each mechanism choose the operating point closest to a pre-registered event budget using **training seeds only**, then evaluate on held-out seeds.

Metrics:

- event fraction;
- target-event precision/recall/F1;
- hidden-state RMSE against an ungated reference;
- post-mute recovery error.

Primary hypothesis: at matched event budget, threshold-side gating preserves hidden state and therefore recovers target-event performance faster after muted intervals. A null result is retained.

## Claim boundary

A positive result would show only that **where a gate acts matters once state persists and output is dynamic**. It would not establish that basket or chandelier cells implement these exact equations, that this is transformer attention, or that oscillations are required.

## Deliberate omissions

No learned controller, no Oja rule, no eigenmodes, no phase/gamma machinery, no network graph, no growth, and no backpropagation in v0. Those are later questions only if the two-gate distinction survives the minimal test.