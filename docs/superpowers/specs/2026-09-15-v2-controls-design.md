# NewMachine v2 design — strongest controls before learned context

## Question

v1 showed that once state persists, state-side and threshold-side interventions have different future effects. Its oracle hybrid then chose the appropriate site from an explicit HIDE/RESET label. That result is mechanically expected and the combined metric is arithmetic once the per-context cells are fixed.

v2 therefore attacks the framing rather than extending it.

## Control A — one signed scalar

A controller emits one scalar `q_t`:

- `q_t < 0`: apply `-q_t` at the state-side gate;
- `q_t > 0`: apply `q_t` at the publication-threshold gate;
- `q_t = 0`: do nothing.

On the oracle HIDE/RESET schedule, choose the same magnitudes as the v1 hybrid. The signed-scalar implementation must reproduce the v1 hybrid trajectory, thresholds, and events exactly.

Interpretation:

- if exact: two independent controller output channels are unnecessary for v1; the essential architectural object is access to two intervention sites;
- if not exact: investigate implementation, because by construction it should be equivalent.

## Control B — both sites during RESET

The unique possible benefit of using both sites simultaneously is not improved hidden-state recovery: publication-side gating does not alter hidden state. Instead, test whether it can hide transient/rebound publications while state-side repair proceeds.

Compare:

- `basket_reset`: state-side repair during RESET;
- `both_reset`: identical state-side repair plus publication-side hold during RESET and a frozen short post-RESET recovery window.

The state trajectories must be exactly identical between these two policies. Measure:

1. hidden-state recovery error — expected identical by construction;
2. event/publication fraction during RESET + recovery hold;
3. event/publication count in the post-RESET hold only.

A real two-site interaction in this toy requires `both_reset` to reduce publication exposure without changing the repaired hidden trajectory.

If no publication reduction occurs, simultaneous two-site control adds nothing in this toy.

## Claim repair from v1

Amend README/RESULTS_V1 to state only what v1 earns:

> Once the gated variable has memory, intervention site changes future computation. Given an oracle context label, the appropriate specialist is context-dependent.

Do not present the 60.6% / 51.9% arithmetic restatement as an independent measured gain. Keep the raw per-context cells and state that the oracle hybrid simply selects the specialist cell in each context.

## Deliberately absent

No learned context controller yet. No gamma/theta, Oja, dendritic modes, grown routing, biology claim, or task-performance headline. v2 is an adversarial control layer.
