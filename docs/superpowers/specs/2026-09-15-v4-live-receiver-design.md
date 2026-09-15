# NewMachine v4 Live Receiver Design

## Purpose

Turn NewMachine from a sender-only control toy into a sender/receiver dynamical system that can answer the missing question: does separating state repair from publication control improve downstream reconstruction at a matched communication cost?

A static GitHub Pages lab must expose the same mechanism so the system can be watched continuously in-browser with no backend.

## Scientific object

The world has two related legitimate state variables rather than one overloaded target:

- `truth_t`: slowly evolving **public truth** that the receiver should reconstruct.
- `local_truth_t`: the sender's legitimate local state. It equals public truth normally and includes a fixed local-only excursion during `private_t` windows.

The sender observes `local_truth_t` through a stream that may independently become corrupted, and maintains persistent state `x_t`. The receiver maintains its own prediction `xhat_t` of **public truth** and only receives explicit correction events.

Two independent world facts can overlap:

- `corrupt_t`: the sender observation is unreliable and may damage resident state.
- `private_t`: the sender has valid local-only state that should temporarily not influence this receiver.

This distinction was tightened during the v4 RED/GREEN cycle. Scoring the receiver against the sender's full local state would make publication suppression look harmful by definition. A separate public target makes relevance operational rather than a bookkeeping mask.

The factorized policy can therefore act at two distinct sites in one step:

- state-side repair/protection alters the sender update;
- publication-side gating blocks the correction event without erasing sender state.

The receiver is the authority for whether sparse publication is useful.

## Policies

Four policies run on the same deterministic stream and at the same event threshold:

1. `dense`: publish sender state every step; no publication sparsity.
2. `delta`: publish only when receiver innovation magnitude exceeds the threshold.
3. `signed`: one mutually exclusive action chooses state repair or publication suppression; repair has priority when both are required.
4. `factorized`: state repair and publication suppression are independently actuable and may happen together.

The signed and factorized policies use the same corruption detector and make identical state-repair decisions, so any difference between them is caused by action geometry, not detection quality or sender dynamics.

## Sender and receiver

Sender state uses a fixed persistent update. During detected corruption, repair is implemented as a local hold/predict step rather than ingesting the contaminated observation.

Receiver coasts with a one-state predictor between events. When a publication event is allowed, the receiver is resynchronized to the sender state.

The scientific metrics are:

- receiver RMSE against public truth;
- sender RMSE against local truth;
- transmitted event fraction;
- recovery RMSE after corruption windows;
- private/overlap-window event fractions;
- an error-versus-traffic summary across event thresholds.

The primary question is not whether factorized control sends fewer events by definition. It is whether it reaches a better receiver-error / message-rate frontier than `delta` and `signed`.

## Browser lab

GitHub Pages serves a self-contained lab from repository root `index.html` with browser-native JavaScript and no dependencies.

The page shows:

- animated public truth, sender state, and receiver estimate;
- corruption and local-only indicators;
- event flashes when corrections are transmitted;
- live receiver RMSE, sender RMSE, message-rate and detector-F1 counters;
- policy, seed, threshold, pause, step and reset controls;
- a continuously updating recent-history canvas;
- a frontier panel comparing all policies over a frozen bank of thresholds.

The browser runs indefinitely by moving through deterministic seeded epochs. The live animation is an inspection instrument, but it uses the same equations and seeded generator as the deterministic JavaScript scientific simulation. Python receipts remain the repository authority.

## Determinism and parity

Both Python and JavaScript use an explicitly specified LCG and matching stream-generation equations rather than language-default RNGs. This makes frozen seed receipts and browser runs reproducible.

The JS simulation core is isolated in `web/sim.mjs`, importable by Node for tests. DOM/rendering logic is isolated in `web/app.mjs`. CI checks a fixed stream prefix plus mechanism invariants.

## Scope boundaries

v4 does not add learning, gradients, neural oscillations, Oja updates, dendritic eigenmodes, grown wiring, vector-valued units, model APIs, or a server. Relevance is supplied by the world schedule, and the corruption detector is hand-specified.

A global factorized-control win is not required. If factorized publication control is neutral or harmful at some operating points, that is retained. The larger v4 success criterion is that receiver-side metrics replace sender event counting and expose which part of the mechanism actually buys downstream performance.
