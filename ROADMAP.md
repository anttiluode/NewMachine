# NewMachine Roadmap

The repository keeps measured evidence (`RESULTS_V*.md`), runnable receipts (`experiments/run_v*.py`), tests, and the live Pages laboratory. Merged implementation-plan/spec scaffolding is intentionally removed after each gate.

## Current spine

```text
v0  persistent state makes state-side and publication-side control diverge
v1  the useful intervention site depends on context
v2  one signed command can route between mutually exclusive interventions
v3  independent objectives can require both interventions at once
v4  a predictive receiver makes silence and publication measurable downstream
```

The strongest v4 effect is state repair before sparse communication. Independent publication control adds only a small, threshold-dependent improvement.

## v5 — infer what is shared

The next gate removes the supplied `private` relevance bit and makes the state vector-valued.

A sender and a peer each observe:

```text
shared public latent + independent local latent
```

in the same ambient vector space. Local variance is deliberately larger than shared variance, so sender-only PCA is an adversarial control rather than an automatic solution.

During an unlabeled calibration prefix, the machine estimates the sender/peer cross-covariance. The leading shared subspace becomes the publication projection. No private/public labels are used to learn it.

During held-out evaluation:

- a robust innovation detector infers observation corruption without corruption labels;
- state repair protects the sender's persistent vector state;
- the learned shared projection decides which state directions may propagate;
- a predictive receiver coasts while silent and is corrected by sparse shared-state events.

Primary comparisons:

1. learned shared subspace vs sender-only PCA;
2. shared projection with and without state repair;
3. learned shared projection vs an oracle public-subspace upper bound;
4. receiver error vs communication rate, not sender event count alone.

A positive v5 result requires the shared projection to recover the true public subspace on held-out worlds and repair to improve receiver reconstruction without being handed reliability or relevance labels.

## After v5

If v5 survives, move the same estimator into the browser as a slow online learner so the Pages organism visibly develops its publication subspace while it runs. Only after that should we consider grown routing, Oja-style local approximations, oscillatory control, or larger learned models.
