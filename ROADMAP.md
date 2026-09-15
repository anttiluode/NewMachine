# NewMachine Roadmap

The repository keeps measured evidence (`RESULTS_V*.md`), runnable receipts (`experiments/run_v*.py`), tests, and the live Pages laboratory. Merged implementation-plan/spec scaffolding is intentionally removed after each gate.

## Current spine

```text
v0  memory makes state-side and publication-side control diverge
v1  the useful intervention site depends on context
v2  one signed command can route between mutually exclusive interventions
v3  independent objectives can require both interventions at once
v4  a predictive receiver makes silence and publication measurable downstream
v5  paired experience infers a shared publication subspace without relevance labels
```

The strongest v4 effect is state repair before sparse communication. v5 then removes the supplied relevance bit: cross-view structure recovers a receiver-relevant vector subspace that sender-only PCA misses in the frozen world.

## Live organism

The Pages laboratory now contains a streaming extension of v5. It does not replay the batch eigendecomposition from the scientific receipt. Instead, two orthonormal publication directions receive a small symmetric cross-view update every step and are re-orthogonalized online.

The page exposes an evaluator-only alignment score and the actual 6 × 6 publication projector so the representation can be watched while it changes. State repair, sparse publication, and the predictive receiver remain active while the subspace is developing.

The frozen Python v5 receipt remains the scientific authority; the browser learner is separately regression-tested as a developmental mechanism.

## v6 — shared is not necessarily relevant

v5 intentionally equates cross-view sharedness with receiver relevance. That is the next assumption to attack.

Construct paired views containing three factors:

```text
receiver-relevant shared latent
+ shared nuisance latent
+ independent local latents
```

Pure cross-view correlation should now fail by mixing useful shared state with shared nuisance. The receiver loss must provide the missing causal criterion.

The next gate should compare:

1. cross-view shared-subspace learning alone;
2. receiver-error-driven selection inside the shared subspace;
3. sender-only PCA and raw sparse delta controls;
4. an oracle receiver-relevant subspace upper bound.

A positive v6 result requires the system to discard shared nuisance without being handed nuisance labels. If it cannot, the correct conclusion is that NewMachine learned *common structure*, not relevance.

## Later, only if v6 survives

Then ask whether batch/global or paired-view machinery can be replaced by more local mechanisms: rank adaptation, Oja/Hebbian approximations, asynchronous peers, grown routing, or oscillatory control. Those are downstream questions, not assumptions to pile onto the current result.
