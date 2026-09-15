# NewMachine v2 Results — Adversarial Controls

v2 does not add a smarter controller. It first asks whether the v1 framing collapses under cheaper explanations.

## Control A — one signed scalar reproduces the oracle hybrid

The v1 oracle hybrid used threshold-side control in HIDE and state-side control in RESET. v2 encodes that choice in one scalar command:

```text
q < 0  -> state-side gate with magnitude -q
q > 0  -> publication-side gate with magnitude q
q = 0  -> no-op
```

Across held-out seeds 200–211, using the same v1 magnitudes (`+0.16` in HIDE, `-0.08` in RESET) gives:

| diagnostic | result |
| --- | ---: |
| max state difference vs direct oracle hybrid | **0.0** |
| max threshold difference | **0.0** |
| event mismatches | **0** |

So v1 does **not** require two independent controller output channels. One signed scalar can select the intervention site exactly.

This does not erase the architectural distinction between state-side and publication-side actuation: the sign router still needs access to both destinations. What disappears is the need to represent them as two independent controller outputs.

## Control B — simultaneous RESET gating

Claude's proposed `both at once` control needs one correction: an output-threshold gate cannot improve hidden-state recovery if it does not alter hidden state. Its only possible additional value in this toy is to suppress publications while state-side repair settles.

v2 therefore keeps RESET state repair fixed at the v1 basket strength `0.08`, then adds publication-threshold control during RESET plus an 8-step post-RESET hold. The strict fidelity target is the event stream produced by the clean reference system, so muting everything cannot count as a free success.

Held-out means:

| extra publication gate | event fraction during RESET+hold | mismatch vs clean reference events | post-RESET hold event fraction | post-RESET hold mismatch |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0.171031 | **0.364918** | 0.200893 | **0.343750** |
| 0.03 | 0.124854 | 0.411095 | 0.144345 | 0.400298 |
| 0.06 | 0.081991 | 0.453958 | 0.101190 | 0.443452 |
| 0.09 | 0.055239 | 0.480710 | 0.065476 | 0.479167 |
| 0.12 | 0.032956 | 0.502993 | 0.034226 | 0.510417 |
| 0.16 | 0.018815 | 0.517134 | 0.017857 | 0.526786 |
| 0.20 | 0.005628 | 0.530321 | 0.013393 | 0.531250 |
| 0.30 | 0.001429 | 0.534520 | 0.004464 | 0.540179 |
| 0.40 | **0.000000** | 0.535949 | **0.000000** | 0.544643 |
| 0.50 | **0.000000** | 0.535949 | **0.000000** | 0.544643 |

For every point in the sweep:

- max hidden-state difference versus basket-only is exactly `0.0`;
- RESET recovery error remains `0.101481`;
- stronger publication gating suppresses more events;
- clean-event fidelity becomes worse, not better.

So `simultaneous_free_win_found = false` under the frozen criterion: no nonzero publication gate both reduces event exposure and preserves or improves clean-reference event fidelity relative to basket-only.

## What v2 earns

Two useful negatives:

1. **Controller dimensionality collapses.** A single signed scalar is enough to reproduce the oracle switch exactly.
2. **Simultaneous gating is not magic.** In this task it traces a communication/fidelity tradeoff; it does not improve state repair and does not give a free publication-quality win.

The surviving architectural statement is therefore smaller and cleaner:

> **A persistent system can have meaningfully different intervention sites even when one scalar controller is sufficient to select between them.**

## Next question

The remaining nontrivial problem is context inference. v1 was handed HIDE versus RESET. v2 shows there is no need to complicate the controller interface first.

The next experiment should therefore give a controller only local observable features and ask whether it can infer *where* to intervene. It must be compared against simple scalar-threshold baselines and against event-triggered/remote-estimation style policies rather than treated as unexplored territory.

No gamma/theta, Oja, dendritic modes, or grown routing should be added until that oracle-free controller survives.
