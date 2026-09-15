# NewMachine

> A small stateful AI/control laboratory built by stripping neuron-inspired ideas down until each claim can fail cleanly.

NewMachine separates three questions that ordinary toy units often collapse together:

```text
what state should I keep?
what part of that state matters to someone else?
when should influence actually propagate?
```

The biological inspiration came from basket/perisomatic versus chandelier/AIS control, but the repository does **not** claim those cell types literally implement these equations.

## Current machine

By v5 the computational object is:

```text
paired experience
      -> infer shared directions

observation reliability
      -> repair/protect persistent sender state

shared publication subspace
      -> remove local-only directions

sparse event trigger
      -> transmit only useful corrections

predictive receiver
      -> coast while silent, correct on events
```

The project has moved well beyond the original "two inhibitory gates" framing: publication relevance is now a learned geometric object rather than a supplied Boolean switch.

## Progression

| gate | question | earned result |
| --- | --- | --- |
| v0 | Can state-side and output-side control genuinely differ? | Yes, once the controlled variable has memory. |
| v1 | Is either intervention universally better? | No. Preserving valid state and repairing corrupted state favor different sites. |
| v2 | Do those sites require two controller outputs? | Not when actions are mutually exclusive; one signed command reproduces the oracle switch. |
| v3 | What if reliability and publication relevance overlap? | Independent objectives can require both interventions at once. |
| v4 | Does sparse publication help a real consumer? | State repair before communication gives the large gain; separate publication control adds a smaller threshold-dependent effect. |
| **v5** | Can publication relevance be inferred instead of supplied? | **Yes in the frozen two-view vector world: cross-view structure recovers the shared subspace that sender-only PCA misses.** |

Full measurements and claim boundaries live in `RESULTS_V0.md` through `RESULTS_V5.md`.

## v5 — infer what is shared

The sender and a peer each see a six-dimensional mixture of a two-dimensional shared/public latent plus independent local state. Local variance is deliberately larger than public variance, so plain sender PCA is pointed toward the wrong answer.

During an unlabeled 420-step calibration prefix, NewMachine estimates sender/peer cross-covariance and uses its leading two eigenvectors as the publication subspace. A robust median/MAD innovation threshold separately supplies the reliability signal for state repair. Neither public/private nor corruption labels are used to choose those controls.

Across eight frozen worlds:

| estimator | mean alignment with true public subspace |
| --- | ---: |
| sender-only PCA | 0.233967 |
| **cross-view shared estimator** | **0.894349** |

At the default sparse-event threshold `0.10`:

| policy | receiver RMSE | event fraction |
| --- | ---: | ---: |
| raw delta | 0.134430 | 0.208514 |
| sender PCA delta | 0.136749 | 0.148732 |
| learned shared delta | 0.087040 | 0.100000 |
| **learned shared + repair** | **0.031979** | **0.022283** |
| oracle shared + repair | 0.029785 | 0.024728 |

The learned shared projection beats sender PCA in both receiver error and traffic at all seven frozen same-threshold comparisons. Adding repair beats the un-repaired shared projection at all seven as well. The learned repair system is about 7.4% above the oracle receiver RMSE at the default point.

See [`RESULTS_V5.md`](RESULTS_V5.md) for the exact protocol and limits: shared rank is supplied, calibration is batch/global, a peer view is available, and the corruption task is intentionally easy.

## Live Pages organism

`index.html` is now a dependency-free streaming extension of v5 rather than a replay of the frozen v4 experiment.

The browser creates one six-dimensional world and keeps it running. Two orthonormal publication directions receive a small symmetric cross-view update every step, so the publication projector changes while sender repair, sparse communication and the predictive receiver are already operating.

The page shows:

- the live public/sender/receiver trajectory on an evaluator-only public coordinate;
- shared-subspace alignment as the representation develops;
- the actual changing 6 × 6 publication projector;
- corruption, repair decisions and sparse correction events;
- receiver error, sender error, message rate and detector F1;
- learned+repair, learned-without-repair and raw-delta modes without requiring a backend.

The browser learner is **not** silently substituted for the frozen v5 experiment. Python remains the scientific authority; the online mechanism has its own deterministic Node regression test. On seed 11 that test requires the learner to move from a poor initial subspace to greater than `0.90` alignment after 3,500 unlabeled streaming steps.

## What not to claim

NewMachine is still a controlled research toy. It is not evidence that chandelier cells are attention heads, not a new remote-estimation theorem, and not yet a general learned AI architecture. The frozen v5 result uses paired views, a supplied shared rank, batch eigendecomposition and a deliberately simple corruption regime. The Pages learner is an online developmental extension, not additional frozen scientific evidence.

The current narrow claim is:

> **Persistent state repair and selective publication can remain useful as separate operations, and publication relevance can be represented by an inferred shared subspace rather than an explicit context label.**

The next falsifier is in [`ROADMAP.md`](ROADMAP.md): v6 asks whether the method can distinguish receiver-relevant shared state from a nuisance that is also shared across views.

## Run

```bash
python -m pip install -e ".[test]"
pytest -q
node tests/web_sim_test.mjs
node tests/web_vector_live_test.mjs
python -m experiments.run_v0
python -m experiments.run_v1
python -m experiments.run_v2
python -m experiments.run_v3
python -m experiments.run_v4
python -m experiments.run_v5
```

## Repository map

- `src/new_machine/core.py` — original persistent scalar unit and two intervention sites
- `src/new_machine/task.py` — deterministic v0-v3 task streams and metrics
- `src/new_machine/receiver.py` — v4 scalar sender/predictive-receiver system
- `src/new_machine/vector_receiver.py` — frozen v5 two-view vector world, shared-subspace inference and repair
- `experiments/run_v0.py` … `run_v5.py` — frozen scientific receipts
- `RESULTS_V0.md` … `RESULTS_V5.md` — measurements and claim boundaries
- `web/sim.mjs` — preserved deterministic v4 browser mechanism
- `web/vector_live.mjs` — streaming v5 online shared-subspace learner
- `index.html`, `web/app.mjs`, `web/style.css` — live GitHub Pages laboratory
- `tests/` — mechanism, receipt, browser-development and page-structure regressions
- [`ROADMAP.md`](ROADMAP.md) — current spine and next falsifier; merged build-plan scaffolding is intentionally pruned

## Lineage

```text
AnttisNeuron
    persistent physical/dendritic-state intuition

GrowingAnttisNeuron
    sparse wiring and physical operators

ActiveVectorNN
    resident state with sparse communication

NewMachine
    repair resident state -> infer shared publication geometry -> sparse predictive communication
```
