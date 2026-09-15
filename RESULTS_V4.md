# v4 — predictive receiver and live laboratory

v0-v3 measured the sender's state and event stream. v4 adds the missing consumer: a predictive receiver that advances its own state while silent and is corrected only when the sender publishes an event.

The question is now downstream and falsifiable:

> **Can state repair and publication control improve receiver reconstruction at a useful communication rate?**

## World

The deterministic world separates two legitimate targets.

- `truth_t` is the public state the receiver should track.
- `local_truth_t` equals public truth normally, but has a `+0.10` valid local-only component during private windows. The sender should keep tracking this local state even though the receiver should not inherit it.
- independent corruption windows add `+0.45` contamination to the sender observation.

This matters. "Private" no longer means "arbitrarily punish an event." It means the sender can contain valid computation that is not relevant to this receiver.

The receiver coasts between events with the fixed predictor

```text
xhat_t = 0.995 * xhat_(t-1) + 0.005 * 0.55
```

and snaps to the sender state when a correction event is published.

The sender's corruption detector is deliberately simple:

```text
abs(observation_t - sender_state_(t-1)) > 0.20
```

No parameter is trained in v4.

## Policies

All policies see the same seeded worlds and use the same event threshold.

| policy | state repair | sparse innovation | publication suppression |
| --- | --- | --- | --- |
| `dense` | no | no | no |
| `delta` | no | yes | no |
| `signed` | yes | yes | private only when repair is not simultaneously required |
| `factorized` | yes | yes | private independently of repair |

`factorized` and `signed` therefore have **identical sender-state dynamics**. Any difference between them is caused only by the extra ability to suppress publication on a step that is also repairing state.

## Frozen experiment

Seeds:

```text
3, 7, 11, 19, 23, 31, 47, 59
```

Event thresholds:

```text
0.00, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18
```

The default reporting point is `0.04`.

### Default operating point

| policy | sender RMSE | receiver RMSE | event fraction | private event fraction | overlap event fraction | recovery RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dense | 0.133201 | 0.145569 | 1.000000 | 1.000000 | 1.000000 | 0.228492 |
| delta | 0.133201 | 0.146279 | 0.150000 | 0.163915 | 0.563014 | 0.242894 |
| signed | **0.037972** | 0.038569 | 0.027292 | 0.008573 | 0.052468 | 0.037005 |
| factorized | **0.037972** | **0.038210** | **0.027083** | **0.000000** | **0.000000** | **0.036623** |

At this operating point, repair-first control reduces receiver RMSE relative to ordinary delta triggering by about **73.6%** for `signed` and **73.9%** for `factorized`, while also transmitting much less often in this constructed world.

That is the large v4 result. It comes from protecting resident state before deciding what to communicate.

## Does factorized publication control add anything?

A little, but not universally.

Across the seven frozen event thresholds, `factorized` is strictly lower in receiver RMSE while using no more traffic than `signed` at **4 / 7** operating points. Its largest receiver-RMSE improvement over `signed` is about `0.000588`; at its worst threshold it is about `0.000151` worse. The largest event-fraction reduction is about `0.03573`.

So v4 does **not** support:

> "factorized control dominates the one-action controller."

It supports the narrower statement:

> **Once there is a real receiver, state repair carries most of the gain in this toy world. Independently suppressing publication can extend the error/traffic frontier at some operating points, especially when local-only state and repair overlap, but the benefit is small and threshold-dependent.**

That is useful because it moves the project away from counting sender events and toward an actual downstream criterion.

## Live GitHub Pages lab

The repository root now contains a dependency-free browser mirror of the same v4 equations:

```text
index.html
web/sim.mjs
web/app.mjs
web/style.css
```

The page runs indefinitely by moving through deterministic epochs. It shows public truth, sender state, receiver estimate, corruption/local-only windows, published events, live reconstruction metrics, and the receiver-error versus message-rate frontier for all four policies.

The animation is an inspection instrument, not a replacement for the receipt. Python remains the scientific authority; JavaScript parity is regression-tested in CI with a fixed PRNG prefix and mechanism invariants.

## Claim boundary

v4 still has no learned controller, vector-valued representation, task model, adaptive timescale, grown routing, oscillatory control, or biological claim. Relevance is supplied by the world schedule. Corruption detection is a hand-specified local residual threshold.

The next serious question is therefore not "add more brain parts." It is whether the same decomposition remains useful around a competent vector/state model when relevance and reliability must be inferred rather than scheduled.
