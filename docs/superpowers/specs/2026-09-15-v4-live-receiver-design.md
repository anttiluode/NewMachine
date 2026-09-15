# NewMachine v4 Live Receiver Design

## Purpose

Turn NewMachine from a sender-only control toy into a sender/receiver dynamical system that can answer the missing question: does separating state repair from publication control improve downstream reconstruction at a matched communication cost?

A static GitHub Pages lab must expose the same mechanism so the system can be watched continuously in-browser with no backend.

## Scientific object

The world has a slowly evolving latent truth `z_t`. A sender observes a potentially corrupted stream `u_t` and maintains persistent state `x_t`. A receiver maintains its own prediction `xhat_t` and only receives explicit correction events.

Two independent world facts can overlap:

- `corrupt_t`: the sender observation is unreliable and may damage resident state.
- `private_t`: even correct sender state should temporarily not influence the receiver.

The factorized policy can therefore act at two distinct sites in one step:

- state-side repair/protection alters the sender update;
- publication-side gating blocks the correction event without erasing sender state.

The receiver is the authority for whether sparse publication is useful.

## Policies

Four policies run on the same deterministic stream and at the same event threshold:

1. `dense`: publish sender state every step; no publication sparsity.
2. `delta`: publish only when receiver innovation magnitude exceeds the threshold.
3. `signed`: one mutually exclusive action chooses state repair or publication suppression.
4. `factorized`: state repair and publication suppression are independently actuable and may happen together.

The signed and factorized policies use the same corruption detector so any difference is caused by action geometry, not detection quality.

## Sender and receiver

Sender state uses the existing persistent update form. During detected corruption, repair is implemented as a local hold/predict step rather than ingesting the contaminated observation.

Receiver coasts with a one-state predictor between events. When a publication event is allowed, the sender transmits the innovation needed to resynchronize the receiver to the sender state.

The scientific metrics are:

- receiver RMSE against latent truth;
- sender RMSE against latent truth;
- transmitted event fraction;
- recovery RMSE after corruption windows;
- overlap-window event fraction;
- an error-versus-traffic summary across event thresholds.

The primary question is not whether factorized control sends fewer events by definition. It is whether it reaches a better receiver-error / message-rate frontier than `delta` and `signed`.

## Browser lab

GitHub Pages serves a self-contained lab from repository root `index.html` with browser-native JavaScript and no dependencies.

The page shows:

- animated latent truth, sender state, and receiver estimate;
- corruption and privacy indicators;
- event flashes when corrections are transmitted;
- live receiver RMSE and message-rate counters;
- policy selector and seed/reset controls;
- a continuously updating recent-history canvas;
- a compact frontier panel comparing all policies over a frozen bank of thresholds.

The live animation is illustrative, but it uses the same equations and seeded generator as the deterministic JavaScript scientific simulation. Python receipts remain the repository authority.

## Determinism and parity

Both Python and JavaScript use an explicitly specified small PRNG and matching stream-generation equations rather than language-default RNGs. This makes frozen seed receipts and browser runs reproducible.

The JS simulation core is isolated in `web/sim.mjs`, importable by Node for tests. DOM/rendering logic is isolated in `web/app.mjs`.

## Scope boundaries

v4 does not add learning, gradients, neural oscillations, Oja updates, dendritic eigenmodes, grown wiring, vector-valued units, model APIs, or a server.

If factorized control does not improve the downstream error/traffic frontier, the result is retained as a negative and later machinery is not justified by v4.
