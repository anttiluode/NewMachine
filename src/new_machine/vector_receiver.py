from __future__ import annotations

from dataclasses import dataclass

import numpy as np


UINT32 = 2**32
AMBIENT_DIM = 6
SHARED_DIM = 2
PUBLIC_ALPHA = 0.96
PRIVATE_ALPHA = 0.40
PUBLIC_DRIVE = 0.035
PRIVATE_DRIVE = 0.15
OBSERVATION_NOISE = 0.01
CORRUPTION_MAGNITUDE = 1.0
SENDER_ALPHA = 0.75
RECEIVER_ALPHA = PUBLIC_ALPHA
MAD_SCALE = 1.4826
DETECTOR_MAD_GAIN = 6.0

POLICIES = {
    "raw_delta",
    "pca_delta",
    "shared_delta",
    "shared_repair",
    "oracle_repair",
}


@dataclass
class Lcg32:
    state: int

    def __post_init__(self) -> None:
        self.state = int(self.state) & 0xFFFFFFFF

    def uniform(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / UINT32

    def signed(self) -> float:
        return 2.0 * self.uniform() - 1.0


def _orthonormal_basis(seed: int, dim: int = AMBIENT_DIM) -> np.ndarray:
    """Deterministic modified Gram-Schmidt basis with canonical column signs."""
    rng = Lcg32(int(seed) ^ 0xA511E9B3)
    columns: list[np.ndarray] = []

    for j in range(dim):
        vector = np.asarray([rng.signed() for _ in range(dim)], dtype=float)
        for previous in columns:
            vector -= previous * float(previous @ vector)

        norm = float(np.linalg.norm(vector))
        if norm < 1e-10:
            vector = np.zeros(dim, dtype=float)
            vector[j] = 1.0
            for previous in columns:
                vector -= previous * float(previous @ vector)
            norm = float(np.linalg.norm(vector))
        vector /= norm

        largest = int(np.argmax(np.abs(vector)))
        if vector[largest] < 0.0:
            vector = -vector
        columns.append(vector)

    return np.column_stack(columns)


def make_vector_world(seed: int, steps: int = 1800) -> dict[str, object]:
    """Create a deterministic two-view vector world.

    Both views contain the same two-dimensional public latent in a common
    ambient space. Sender-local and peer-local latents are independent and
    occupy disjoint directions. Local variance is intentionally larger than
    public variance so sender-only PCA is not a relevance detector.

    No public/private or corruption label is required by the controller. The
    labels returned here exist only for evaluation.
    """
    if steps < 64:
        raise ValueError("steps must be at least 64")

    basis = _orthonormal_basis(int(seed))
    public_basis = basis[:, :2]
    sender_private_basis = basis[:, 2:4]
    peer_private_basis = basis[:, 4:6]
    public_projector = public_basis @ public_basis.T

    corruption_direction = (
        0.60 * basis[:, 0]
        + 0.20 * basis[:, 2]
        + 0.77 * basis[:, 5]
    )
    corruption_direction /= np.linalg.norm(corruption_direction)

    rng = Lcg32(int(seed) ^ 0xC0FFEE11)
    public_latent = np.zeros((steps, 2), dtype=float)
    sender_private = np.zeros((steps, 2), dtype=float)
    peer_private = np.zeros((steps, 2), dtype=float)

    public_truth = np.zeros((steps, AMBIENT_DIM), dtype=float)
    sender_clean = np.zeros_like(public_truth)
    sender_observed = np.zeros_like(public_truth)
    peer_view = np.zeros_like(public_truth)
    corrupt = np.zeros(steps, dtype=bool)

    for t in range(steps):
        public_drive = PUBLIC_DRIVE * np.asarray([rng.signed(), rng.signed()])
        sender_drive = PRIVATE_DRIVE * np.asarray([rng.signed(), rng.signed()])
        peer_drive = PRIVATE_DRIVE * np.asarray([rng.signed(), rng.signed()])

        if t:
            public_latent[t] = PUBLIC_ALPHA * public_latent[t - 1] + public_drive
            sender_private[t] = PRIVATE_ALPHA * sender_private[t - 1] + sender_drive
            peer_private[t] = PRIVATE_ALPHA * peer_private[t - 1] + peer_drive
        else:
            public_latent[t] = public_drive
            sender_private[t] = sender_drive
            peer_private[t] = peer_drive

        public_truth[t] = public_basis @ public_latent[t]
        sender_clean[t] = public_truth[t] + sender_private_basis @ sender_private[t]
        peer_view[t] = public_truth[t] + peer_private_basis @ peer_private[t]
        peer_view[t] += OBSERVATION_NOISE * np.asarray(
            [rng.signed() for _ in range(AMBIENT_DIM)]
        )

        corrupt[t] = ((t + (int(seed) * 13) % 127) % 127) < 17
        sender_observed[t] = sender_clean[t]
        sender_observed[t] += OBSERVATION_NOISE * np.asarray(
            [rng.signed() for _ in range(AMBIENT_DIM)]
        )
        if corrupt[t]:
            sender_observed[t] += CORRUPTION_MAGNITUDE * corruption_direction

    return {
        "seed": int(seed),
        "public_truth": public_truth,
        "sender_clean": sender_clean,
        "sender_observed": sender_observed,
        "peer_view": peer_view,
        "corrupt": corrupt,
        "public_projector": public_projector,
        "basis": basis,
    }


def _top_projector(matrix: np.ndarray, rank: int) -> np.ndarray:
    symmetric = 0.5 * (matrix + matrix.T)
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    order = np.argsort(eigenvalues)[::-1][:rank]
    vectors = eigenvectors[:, order]
    return vectors @ vectors.T


def _subspace_alignment(projector: np.ndarray, target: np.ndarray, rank: int) -> float:
    value = float(np.trace(projector @ target) / rank)
    return float(np.clip(value, 0.0, 1.0))


def calibrate_world(
    world: dict[str, object],
    calibration_steps: int = 420,
    shared_dim: int = SHARED_DIM,
) -> dict[str, object]:
    """Infer relevance and reliability scales without evaluation labels.

    Relevance comes from sender/peer cross-covariance. Reliability scale comes
    from a robust median/MAD statistic on sender step innovations. Ground-truth
    projector alignment is reported after calibration for evaluation only.
    """
    sender = np.asarray(world["sender_observed"], dtype=float)
    peer = np.asarray(world["peer_view"], dtype=float)
    public_projector = np.asarray(world["public_projector"], dtype=float)

    if calibration_steps < 64 or calibration_steps >= len(sender):
        raise ValueError("calibration_steps must be at least 64 and smaller than the world")
    if not 1 <= shared_dim < sender.shape[1]:
        raise ValueError("shared_dim must be between 1 and ambient_dim - 1")

    x = sender[:calibration_steps]
    y = peer[:calibration_steps]
    xc = x - np.mean(x, axis=0, keepdims=True)
    yc = y - np.mean(y, axis=0, keepdims=True)

    # The common latent contributes a positive symmetric component. Independent
    # local states average away in cross-view covariance.
    cross = (xc.T @ yc + yc.T @ xc) / (2.0 * calibration_steps)
    shared_projector = _top_projector(cross, shared_dim)

    sender_covariance = (xc.T @ xc) / calibration_steps
    pca_projector = _top_projector(sender_covariance, shared_dim)

    step_norms = np.linalg.norm(np.diff(x, axis=0), axis=1)
    median = float(np.median(step_norms))
    mad = float(np.median(np.abs(step_norms - median)))
    detector_threshold = median + DETECTOR_MAD_GAIN * MAD_SCALE * mad
    if detector_threshold <= 0.0:
        detector_threshold = max(1e-9, 2.0 * median)

    return {
        "shared_projector": shared_projector,
        "pca_projector": pca_projector,
        "detector_threshold": float(detector_threshold),
        "shared_alignment": _subspace_alignment(
            shared_projector, public_projector, shared_dim
        ),
        "pca_alignment": _subspace_alignment(
            pca_projector, public_projector, shared_dim
        ),
    }


def _binary_f1(target: np.ndarray, prediction: np.ndarray) -> float:
    target = np.asarray(target, dtype=bool)
    prediction = np.asarray(prediction, dtype=bool)
    tp = int(np.sum(target & prediction))
    fp = int(np.sum(~target & prediction))
    fn = int(np.sum(target & ~prediction))
    denominator = 2 * tp + fp + fn
    return 0.0 if denominator == 0 else float((2 * tp) / denominator)


def simulate_vector_policy(
    seed: int,
    policy: str,
    event_threshold: float = 0.10,
    steps: int = 1800,
    calibration_steps: int = 420,
) -> dict[str, object]:
    """Run a held-out vector sender/receiver policy after unlabeled calibration."""
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    if not np.isfinite(event_threshold) or event_threshold < 0.0:
        raise ValueError("event_threshold must be finite and nonnegative")

    world = make_vector_world(seed=seed, steps=steps)
    calibration = calibrate_world(
        world, calibration_steps=calibration_steps, shared_dim=SHARED_DIM
    )

    if policy == "raw_delta":
        projector = np.eye(AMBIENT_DIM)
        repair_enabled = False
    elif policy == "pca_delta":
        projector = np.asarray(calibration["pca_projector"])
        repair_enabled = False
    elif policy == "shared_delta":
        projector = np.asarray(calibration["shared_projector"])
        repair_enabled = False
    elif policy == "shared_repair":
        projector = np.asarray(calibration["shared_projector"])
        repair_enabled = True
    else:  # oracle_repair
        projector = np.asarray(world["public_projector"])
        repair_enabled = True

    observed = np.asarray(world["sender_observed"])
    clean = np.asarray(world["sender_clean"])
    public_truth = np.asarray(world["public_truth"])
    corrupt = np.asarray(world["corrupt"], dtype=bool)
    detector_threshold = float(calibration["detector_threshold"])

    evaluation_steps = steps - calibration_steps
    sender_trace = np.zeros((evaluation_steps, AMBIENT_DIM), dtype=float)
    receiver_trace = np.zeros_like(sender_trace)
    detected = np.zeros(evaluation_steps, dtype=bool)
    repaired = np.zeros(evaluation_steps, dtype=bool)
    events = np.zeros(evaluation_steps, dtype=bool)

    sender_state = np.zeros(AMBIENT_DIM, dtype=float)
    receiver_state = np.zeros(AMBIENT_DIM, dtype=float)

    for out_t, t in enumerate(range(calibration_steps, steps)):
        innovation_norm = float(np.linalg.norm(observed[t] - sender_state))
        detected[out_t] = innovation_norm > detector_threshold
        repaired[out_t] = bool(repair_enabled and detected[out_t])

        if repaired[out_t]:
            # The controller does not know the clean target; it only refuses a
            # large unreliable innovation and lets resident state coast.
            sender_state = RECEIVER_ALPHA * sender_state
        else:
            sender_state = (
                SENDER_ALPHA * sender_state
                + (1.0 - SENDER_ALPHA) * observed[t]
            )
        sender_trace[out_t] = sender_state

        receiver_prediction = RECEIVER_ALPHA * receiver_state
        published_state = projector @ sender_state
        publish = bool(
            np.linalg.norm(published_state - receiver_prediction) >= event_threshold
        )
        events[out_t] = publish
        receiver_state = published_state if publish else receiver_prediction
        receiver_trace[out_t] = receiver_state

    eval_slice = slice(calibration_steps, steps)
    eval_public = public_truth[eval_slice]
    eval_clean = clean[eval_slice]
    eval_corrupt = corrupt[eval_slice]

    metrics = {
        "sender_rmse": float(np.sqrt(np.mean((sender_trace - eval_clean) ** 2))),
        "receiver_rmse": float(
            np.sqrt(np.mean((receiver_trace - eval_public) ** 2))
        ),
        "event_fraction": float(np.mean(events)),
        "detector_f1": _binary_f1(eval_corrupt, detected),
        "repair_fraction": float(np.mean(repaired)),
        "shared_alignment": float(calibration["shared_alignment"]),
        "pca_alignment": float(calibration["pca_alignment"]),
        "detector_threshold": detector_threshold,
    }

    return {
        "seed": int(seed),
        "policy": policy,
        "event_threshold": float(event_threshold),
        "calibration_steps": int(calibration_steps),
        "calibration": calibration,
        "metrics": metrics,
        "trace": {
            "public_truth": eval_public,
            "sender_clean": eval_clean,
            "sender": sender_trace,
            "receiver": receiver_trace,
            "corrupt": eval_corrupt,
            "detected_corrupt": detected,
            "repaired": repaired,
            "events": events,
        },
    }
