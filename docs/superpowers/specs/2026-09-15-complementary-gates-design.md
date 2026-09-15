# NewMachine v1 — Complementary Gates Design

## Question

Does a persistent machine benefit from having **both** control locations because different contexts require different operations?

v0 established that state-side and threshold-side inhibition are identical for a memoryless threshold unit and diverge once hidden state persists. v1 tests the stronger engineering hypothesis: one gate should be useful when internal state must be preserved but kept private, while the other should be useful when internal state itself has been corrupted and should be changed.

## Two contexts

A clean latent stream `z_t` drives the reference machine.

### HIDE

The observed input remains clean. The correct operation is:

```text
keep internal state
suppress output events temporarily
```

Threshold-side/chandelier-like control should fit this operation. State-side control should unnecessarily distort the hidden state.

### RESET

The observed input receives a known positive contamination during a control window. The clean reference does not contain that contamination. The correct operation is:

```text
change/correct internal state
suppress output caused by the contamination
```

State-side/basket-like control can cancel the contamination before it is stored. Threshold-side control can hide the output but cannot prevent corrupted state from persisting after the window.

## Policies

Compare three fixed policies:

- `basket_only`: state-side control in HIDE and RESET;
- `chandelier_only`: threshold-side control in HIDE and RESET;
- `hybrid`: chandelier-like control in HIDE, basket-like control in RESET.

The controller is given the context label directly. No context inference or learning is allowed in v1.

## Budget matching

Each policy has one scalar control multiplier chosen from a frozen grid using training seeds only. Select the multiplier closest to a pre-registered target control-window event fraction. Evaluate all scientific metrics on disjoint held-out seeds.

## Metrics

- overall and control-window event fraction;
- hidden-state RMSE versus the clean reference;
- post-HIDE recovery error;
- post-RESET recovery error;
- combined post-context recovery error.

Primary hypothesis:

```text
hybrid combined recovery error < min(basket_only, chandelier_only)
```

with control-window event fractions matched within a fixed tolerance.

A null or reverse result is retained.

## Claim boundary

A positive result would establish only that **two gate locations can be computationally complementary in a persistent state machine**. It would not prove that cortical basket and chandelier cells solve these exact synthetic contexts, nor that the mechanism is attention.
