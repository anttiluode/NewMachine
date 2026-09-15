# v5 — infer a shared vector publication subspace

v4 still received an explicit `private` relevance bit. v5 removes that bit and makes the state six-dimensional.

The sender and a peer each observe a mixture of:

```text
shared public latent + independent local latent
```

The two-dimensional public latent occupies the same unknown ambient subspace in both views. Sender-local and peer-local activity occupy different directions and are independent. Local variance is deliberately larger than public variance, so sender-only PCA is an adversarial control: the largest-variance directions are mostly *not* the directions that should propagate.

No private/public label is used by the controller.

## Inference

The first 420 steps are an unlabeled calibration prefix.

### Relevance

The machine centers the sender and peer streams and forms their symmetric cross-covariance:

```text
C_shared = (X_sender^T X_peer + X_peer^T X_sender) / (2T)
```

The leading two eigenvectors define a publication projector. Independent local components average away; the common latent contributes correlated structure.

A sender-only PCA projector of the same rank is the control.

### Reliability

A corruption threshold is obtained without corruption labels from the median and MAD of sender step-innovation norms:

```text
threshold = median + 6 * 1.4826 * MAD
```

During evaluation, a repair-enabled sender refuses innovations whose norm relative to resident state exceeds that threshold and lets resident state coast instead.

The returned corruption labels are used only to score detector F1 after the fact.

## Frozen experiment

Seeds:

```text
3, 7, 11, 19, 23, 31, 47, 59
```

Event thresholds:

```text
0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20
```

Default reporting threshold: `0.10`.

### Did the unlabeled shared estimator find the right directions?

Across the eight worlds:

| estimator | mean alignment with true public subspace |
| --- | ---: |
| sender-only PCA | 0.233967 |
| **sender/peer cross-view** | **0.894349** |

Alignment is `trace(P_est P_true) / 2`, so `1` is exact subspace recovery and `0` is orthogonal.

The cross-view advantage is `0.660382`. This is the first NewMachine gate where publication relevance is inferred from data rather than supplied as a context bit.

### Default downstream operating point

| policy | receiver RMSE | event fraction | sender RMSE |
| --- | ---: | ---: | ---: |
| raw delta | 0.134430 | 0.208514 | 0.139919 |
| sender PCA delta | 0.136749 | 0.148732 | 0.139919 |
| learned shared delta | 0.087040 | 0.100000 | 0.139919 |
| **learned shared + repair** | **0.031979** | **0.022283** | **0.045881** |
| oracle shared + repair | 0.029785 | 0.024728 | 0.045881 |

At the default threshold, replacing sender-only PCA with the learned cross-view publication subspace reduces receiver RMSE by about **36.4%** and event traffic by about **32.8%**.

Adding state repair on top of that learned subspace reduces receiver RMSE by another **63.3%** and event traffic by about **77.7%** in this constructed world.

The learned repair system's receiver RMSE is only about **7.36%** above the oracle-projector upper bound at this operating point.

### Threshold bank

At every one of the seven frozen threshold settings:

- `shared_delta` has lower receiver RMSE and no more traffic than `pca_delta`;
- `shared_repair` has lower receiver RMSE and no more traffic than `shared_delta`.

These are paired same-threshold comparisons, not a claim that threshold values correspond to identical communication budgets or that one policy globally dominates every possible operating point.

## What v5 earns

The useful abstraction has moved again:

```text
paired experience
      -> infer shared directions

local innovation geometry
      -> infer unreliable observations

shared projection
      -> decide which state directions may propagate

state repair
      -> protect the resident computation before propagation

predictive receiver
      -> coast while silent, correct on sparse events
```

The important change from v4 is that **publication relevance is no longer a supplied Boolean variable**. It is represented as a learned geometric object: a subspace that captures what survives across views.

That is much closer to the original intuition behind selective routes than a hand-coded output gate.

## Claim boundary

v5 is still a controlled toy.

- The shared dimension (`2`) is supplied.
- Sender and peer share the same ambient public basis by construction.
- The publication subspace is estimated in a batch calibration prefix, not learned continuously.
- Cross-view eigendecomposition is a global operation, not a local Oja/Hebbian rule.
- The corruption burst is intentionally easy; the repair loop reaches detector F1 `1.0` in this frozen setup. That is not a general anomaly-detection result.
- The peer view is available during calibration; this is a multi-view/self-supervised setting, not single-stream inference from nothing.
- There is no task model, language model, grown routing, gradient-trained controller, or biological claim.

The next worthwhile step is therefore specific: replace the batch cross-covariance eigendecomposition with a slow online shared-subspace learner and expose that learner in the Pages organism so its publication geometry visibly develops while it runs.
