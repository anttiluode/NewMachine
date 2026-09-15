export const AMBIENT_DIM = 6;
export const SHARED_DIM = 2;
export const PUBLIC_ALPHA = 0.96;
export const PRIVATE_ALPHA = 0.40;
export const PUBLIC_DRIVE = 0.035;
export const PRIVATE_DRIVE = 0.15;
export const OBSERVATION_NOISE = 0.01;
export const CORRUPTION_MAGNITUDE = 1.0;
export const SENDER_ALPHA = 0.75;
export const RECEIVER_ALPHA = PUBLIC_ALPHA;
export const MAD_SCALE = 1.4826;
export const DETECTOR_MAD_GAIN = 6.0;
export const ONLINE_LEARNING_RATE = 0.20;
export const ONLINE_MEAN_ALPHA = 0.01;

const UINT32 = 4294967296;

class Lcg32 {
  constructor(seed) {
    this.state = Number(seed) >>> 0;
  }

  uniform() {
    this.state = (Math.imul(1664525, this.state) + 1013904223) >>> 0;
    return this.state / UINT32;
  }

  signed() {
    return 2 * this.uniform() - 1;
  }
}

function zeros(n) {
  return new Array(n).fill(0);
}

function identity(n) {
  return Array.from({ length: n }, (_, row) =>
    Array.from({ length: n }, (_, column) => (row === column ? 1 : 0)));
}

function dot(a, b) {
  let value = 0;
  for (let i = 0; i < a.length; i += 1) value += a[i] * b[i];
  return value;
}

function norm(vector) {
  return Math.sqrt(dot(vector, vector));
}

function subtract(a, b) {
  return a.map((value, index) => value - b[index]);
}

function scale(vector, amount) {
  return vector.map((value) => amount * value);
}

function axpby(a, x, b, y) {
  return x.map((value, index) => a * value + b * y[index]);
}

function matVec(matrix, vector) {
  return matrix.map((row) => dot(row, vector));
}

function combine(columns, coefficients) {
  const output = zeros(columns[0].length);
  for (let j = 0; j < columns.length; j += 1) {
    for (let i = 0; i < output.length; i += 1) {
      output[i] += columns[j][i] * coefficients[j];
    }
  }
  return output;
}

function normalize(vector) {
  const magnitude = norm(vector);
  if (magnitude < 1e-12) throw new Error('cannot normalize a near-zero vector');
  return vector.map((value) => value / magnitude);
}

function orthonormalize(columns) {
  const output = [];
  for (let j = 0; j < columns.length; j += 1) {
    let vector = columns[j].slice();
    for (const previous of output) {
      const projection = dot(previous, vector);
      vector = vector.map((value, i) => value - projection * previous[i]);
    }

    if (norm(vector) < 1e-10) {
      vector = zeros(columns[0].length);
      vector[j % vector.length] = 1;
      for (const previous of output) {
        const projection = dot(previous, vector);
        vector = vector.map((value, i) => value - projection * previous[i]);
      }
    }
    output.push(normalize(vector));
  }
  return output;
}

function deterministicBasis(seed) {
  const rng = new Lcg32((Number(seed) ^ 0xa511e9b3) >>> 0);
  const columns = [];

  for (let j = 0; j < AMBIENT_DIM; j += 1) {
    let vector = Array.from({ length: AMBIENT_DIM }, () => rng.signed());
    for (const previous of columns) {
      const projection = dot(previous, vector);
      vector = vector.map((value, i) => value - projection * previous[i]);
    }

    if (norm(vector) < 1e-10) {
      vector = zeros(AMBIENT_DIM);
      vector[j] = 1;
      for (const previous of columns) {
        const projection = dot(previous, vector);
        vector = vector.map((value, i) => value - projection * previous[i]);
      }
    }

    vector = normalize(vector);
    let largest = 0;
    for (let i = 1; i < vector.length; i += 1) {
      if (Math.abs(vector[i]) > Math.abs(vector[largest])) largest = i;
    }
    if (vector[largest] < 0) vector = scale(vector, -1);
    columns.push(vector);
  }
  return columns;
}

function projectorFromColumns(columns) {
  return Array.from({ length: AMBIENT_DIM }, (_, i) =>
    Array.from({ length: AMBIENT_DIM }, (_, j) => {
      let value = 0;
      for (const column of columns) value += column[i] * column[j];
      return value;
    }));
}

function projectorAlignment(projector, target) {
  let trace = 0;
  for (let i = 0; i < AMBIENT_DIM; i += 1) {
    for (let j = 0; j < AMBIENT_DIM; j += 1) {
      trace += projector[i][j] * target[j][i];
    }
  }
  return Math.max(0, Math.min(1, trace / SHARED_DIM));
}

function median(values) {
  if (!values.length) return 0;
  const sorted = values.slice().sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : 0.5 * (sorted[middle - 1] + sorted[middle]);
}

function robustThreshold(history) {
  if (history.length < 32) return Number.POSITIVE_INFINITY;
  const center = median(history);
  const mad = median(history.map((value) => Math.abs(value - center)));
  return Math.max(1e-9, center + DETECTOR_MAD_GAIN * MAD_SCALE * mad);
}

function f1(tp, fp, fn) {
  const denominator = 2 * tp + fp + fn;
  return denominator === 0 ? 0 : (2 * tp) / denominator;
}

class StreamingVectorWorld {
  constructor(seed) {
    this.seed = Number(seed) >>> 0;
    this.basis = deterministicBasis(this.seed);
    this.publicColumns = this.basis.slice(0, 2);
    this.senderPrivateColumns = this.basis.slice(2, 4);
    this.peerPrivateColumns = this.basis.slice(4, 6);
    this.publicProjector = projectorFromColumns(this.publicColumns);

    let corruptionDirection = zeros(AMBIENT_DIM);
    const weights = [0.60, 0.20, 0.77];
    const directions = [this.basis[0], this.basis[2], this.basis[5]];
    for (let j = 0; j < directions.length; j += 1) {
      corruptionDirection = corruptionDirection.map(
        (value, i) => value + weights[j] * directions[j][i],
      );
    }
    this.corruptionDirection = normalize(corruptionDirection);

    this.rng = new Lcg32((this.seed ^ 0xc0ffee11) >>> 0);
    this.publicLatent = zeros(2);
    this.senderPrivate = zeros(2);
    this.peerPrivate = zeros(2);
    this.clock = 0;
  }

  randomVector(n, amount) {
    return Array.from({ length: n }, () => amount * this.rng.signed());
  }

  step() {
    const publicDrive = this.randomVector(2, PUBLIC_DRIVE);
    const senderDrive = this.randomVector(2, PRIVATE_DRIVE);
    const peerDrive = this.randomVector(2, PRIVATE_DRIVE);

    if (this.clock === 0) {
      this.publicLatent = publicDrive;
      this.senderPrivate = senderDrive;
      this.peerPrivate = peerDrive;
    } else {
      this.publicLatent = axpby(PUBLIC_ALPHA, this.publicLatent, 1, publicDrive);
      this.senderPrivate = axpby(PRIVATE_ALPHA, this.senderPrivate, 1, senderDrive);
      this.peerPrivate = axpby(PRIVATE_ALPHA, this.peerPrivate, 1, peerDrive);
    }

    const publicTruth = combine(this.publicColumns, this.publicLatent);
    const senderClean = axpby(
      1,
      publicTruth,
      1,
      combine(this.senderPrivateColumns, this.senderPrivate),
    );
    const peerView = axpby(
      1,
      axpby(1, publicTruth, 1, combine(this.peerPrivateColumns, this.peerPrivate)),
      1,
      this.randomVector(AMBIENT_DIM, OBSERVATION_NOISE),
    );

    const corrupt = ((this.clock + ((this.seed * 13) % 127)) % 127) < 17;
    let senderObserved = axpby(
      1,
      senderClean,
      1,
      this.randomVector(AMBIENT_DIM, OBSERVATION_NOISE),
    );
    if (corrupt) {
      senderObserved = axpby(
        1,
        senderObserved,
        CORRUPTION_MAGNITUDE,
        this.corruptionDirection,
      );
    }

    this.clock += 1;
    return { publicTruth, senderClean, senderObserved, peerView, corrupt };
  }
}

class LiveVectorMachine {
  constructor(seed, options = {}) {
    this.seed = Number(seed) >>> 0;
    this.eventThreshold = Number(options.eventThreshold ?? 0.10);
    this.repairEnabled = options.repair ?? true;
    this.publication = options.publication ?? 'learned';
    this.learningRate = Number(options.learningRate ?? ONLINE_LEARNING_RATE);
    this.meanAlpha = Number(options.meanAlpha ?? ONLINE_MEAN_ALPHA);

    if (!Number.isFinite(this.eventThreshold) || this.eventThreshold < 0) {
      throw new Error('eventThreshold must be finite and nonnegative');
    }
    if (!['learned', 'raw'].includes(this.publication)) {
      throw new Error(`unknown publication mode: ${this.publication}`);
    }

    this.world = new StreamingVectorWorld(this.seed);
    this.learnedColumns = [
      [1, 0, 0, 0, 0, 0],
      [0, 1, 0, 0, 0, 0],
    ];
    this.meanSender = zeros(AMBIENT_DIM);
    this.meanPeer = zeros(AMBIENT_DIM);
    this.senderState = zeros(AMBIENT_DIM);
    this.receiverState = zeros(AMBIENT_DIM);
    this.previousObserved = null;
    this.innovationHistory = [];
    this.detectorThreshold = Number.POSITIVE_INFINITY;

    this.count = 0;
    this.senderSq = 0;
    this.receiverSq = 0;
    this.events = 0;
    this.tp = 0;
    this.fp = 0;
    this.fn = 0;
  }

  learnedProjector() {
    return projectorFromColumns(this.learnedColumns);
  }

  publicationProjector() {
    return this.publication === 'raw'
      ? identity(AMBIENT_DIM)
      : this.learnedProjector();
  }

  learn(senderObserved, peerView) {
    if (this.publication === 'raw') return;

    this.meanSender = axpby(
      1 - this.meanAlpha,
      this.meanSender,
      this.meanAlpha,
      senderObserved,
    );
    this.meanPeer = axpby(
      1 - this.meanAlpha,
      this.meanPeer,
      this.meanAlpha,
      peerView,
    );

    const x = subtract(senderObserved, this.meanSender);
    const y = subtract(peerView, this.meanPeer);
    const updated = [];

    for (const column of this.learnedColumns) {
      const yOnW = dot(y, column);
      const xOnW = dot(x, column);
      const gradient = x.map(
        (value, i) => 0.5 * (value * yOnW + y[i] * xOnW),
      );
      updated.push(
        column.map((value, i) => value + this.learningRate * gradient[i]),
      );
    }
    this.learnedColumns = orthonormalize(updated);
  }

  updateDetector(senderObserved) {
    this.detectorThreshold = robustThreshold(this.innovationHistory);
    const residual = norm(subtract(senderObserved, this.senderState));
    const detected = residual > this.detectorThreshold;

    if (this.previousObserved !== null) {
      this.innovationHistory.push(norm(subtract(senderObserved, this.previousObserved)));
      if (this.innovationHistory.length > 256) this.innovationHistory.shift();
    }
    this.previousObserved = senderObserved.slice();
    return detected;
  }

  metrics() {
    const learned = this.learnedProjector();
    return {
      steps: this.count,
      receiverRmse: this.count
        ? Math.sqrt(this.receiverSq / (this.count * AMBIENT_DIM))
        : 0,
      senderRmse: this.count
        ? Math.sqrt(this.senderSq / (this.count * AMBIENT_DIM))
        : 0,
      eventFraction: this.count ? this.events / this.count : 0,
      detectorF1: f1(this.tp, this.fp, this.fn),
      sharedAlignment: projectorAlignment(learned, this.world.publicProjector),
      detectorThreshold: this.detectorThreshold,
    };
  }

  step() {
    const worldStep = this.world.step();
    const { publicTruth, senderClean, senderObserved, peerView, corrupt } = worldStep;

    // Relevance is learned from paired experience. Sender-only corruption has
    // no label here; because it is not shared with the peer it should wash out
    // of the cross-view objective over time.
    this.learn(senderObserved, peerView);

    const detectedCorrupt = this.updateDetector(senderObserved);
    const repaired = Boolean(this.repairEnabled && detectedCorrupt);

    if (repaired) {
      this.senderState = scale(this.senderState, RECEIVER_ALPHA);
    } else {
      this.senderState = axpby(
        SENDER_ALPHA,
        this.senderState,
        1 - SENDER_ALPHA,
        senderObserved,
      );
    }

    const receiverPrediction = scale(this.receiverState, RECEIVER_ALPHA);
    const projector = this.publicationProjector();
    const publishedState = matVec(projector, this.senderState);
    const event = norm(subtract(publishedState, receiverPrediction)) >= this.eventThreshold;
    this.receiverState = event ? publishedState.slice() : receiverPrediction;

    this.count += 1;
    if (event) this.events += 1;
    if (corrupt && detectedCorrupt) this.tp += 1;
    else if (!corrupt && detectedCorrupt) this.fp += 1;
    else if (corrupt && !detectedCorrupt) this.fn += 1;

    const senderError = subtract(this.senderState, senderClean);
    const receiverError = subtract(this.receiverState, publicTruth);
    this.senderSq += dot(senderError, senderError);
    this.receiverSq += dot(receiverError, receiverError);

    const evaluatorAxis = this.world.publicColumns[0];
    return {
      step: this.count,
      publicTruth: publicTruth.slice(),
      senderClean: senderClean.slice(),
      senderObserved: senderObserved.slice(),
      peerView: peerView.slice(),
      senderState: this.senderState.slice(),
      receiverState: this.receiverState.slice(),
      publicationProjector: projector.map((row) => row.slice()),
      corrupt,
      detectedCorrupt,
      repaired,
      event,
      truthCoordinate: dot(publicTruth, evaluatorAxis),
      senderCoordinate: dot(publishedState, evaluatorAxis),
      receiverCoordinate: dot(this.receiverState, evaluatorAxis),
      metrics: this.metrics(),
    };
  }
}

export function createLiveVectorMachine(seed, options = {}) {
  return new LiveVectorMachine(seed, options);
}
