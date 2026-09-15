export const BASELINE = 0.55;
export const SENDER_ALPHA = 0.90;
export const RECEIVER_ALPHA = 0.995;
export const DETECTOR_THRESHOLD = 0.20;
export const LOCAL_ONLY_OFFSET = 0.10;

const POLICIES = new Set(['dense', 'delta', 'signed', 'factorized']);

class Lcg32 {
  constructor(seed) {
    this.state = seed >>> 0;
  }

  uniform() {
    this.state = (Math.imul(1664525, this.state) + 1013904223) >>> 0;
    return this.state / 4294967296;
  }

  signed() {
    return 2 * this.uniform() - 1;
  }
}

export function generateWorld(seed, steps) {
  if (!Number.isInteger(steps) || steps < 1) {
    throw new Error('steps must be a positive integer');
  }

  const rng = new Lcg32((Number(seed) ^ 0x9e3779b9) >>> 0);
  const truth = new Array(steps);
  const localTruth = new Array(steps);
  const observed = new Array(steps);
  const privateMask = new Array(steps);
  const corrupt = new Array(steps);

  truth[0] = BASELINE + 0.02 * rng.signed();
  for (let t = 0; t < steps; t += 1) {
    if (t > 0) {
      truth[t] = 0.992 * truth[t - 1] + 0.008 * BASELINE + 0.012 * rng.signed();
    }

    privateMask[t] = ((t + ((seed * 7) % 83)) % 83) < 18;
    corrupt[t] = ((t + ((seed * 11) % 97)) % 97) < 16;
    localTruth[t] = truth[t] + (privateMask[t] ? LOCAL_ONLY_OFFSET : 0);
    observed[t] = localTruth[t] + 0.02 * rng.signed() + (corrupt[t] ? 0.45 : 0);
  }

  return { truth, localTruth, observed, private: privateMask, corrupt };
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function rmse(a, b) {
  return Math.sqrt(mean(a.map((value, index) => {
    const error = value - b[index];
    return error * error;
  })));
}

function f1(target, prediction) {
  let tp = 0;
  let fp = 0;
  let fn = 0;
  for (let i = 0; i < target.length; i += 1) {
    if (target[i] && prediction[i]) tp += 1;
    else if (!target[i] && prediction[i]) fp += 1;
    else if (target[i] && !prediction[i]) fn += 1;
  }
  const denominator = 2 * tp + fp + fn;
  return denominator === 0 ? 0 : (2 * tp) / denominator;
}

function recoveryRmse(truth, receiver, corrupt, horizon = 12) {
  const errors = [];
  for (let t = 1; t < corrupt.length; t += 1) {
    if (corrupt[t - 1] && !corrupt[t]) {
      const stop = Math.min(t + horizon, truth.length);
      for (let k = t; k < stop; k += 1) {
        errors.push(receiver[k] - truth[k]);
      }
    }
  }
  return errors.length === 0 ? 0 : Math.sqrt(mean(errors.map((value) => value * value)));
}

export function simulate(policy, seed, eventThreshold = 0.08, steps = 1200) {
  if (!POLICIES.has(policy)) throw new Error(`unknown policy: ${policy}`);
  if (!Number.isInteger(steps) || steps < 32) throw new Error('steps must be an integer at least 32');
  if (!Number.isFinite(eventThreshold) || eventThreshold < 0) {
    throw new Error('eventThreshold must be finite and nonnegative');
  }

  const world = generateWorld(seed, steps);
  const sender = new Array(steps);
  const receiver = new Array(steps);
  const detectedCorrupt = new Array(steps).fill(false);
  const repaired = new Array(steps).fill(false);
  const events = new Array(steps).fill(false);

  let senderState = BASELINE;
  let receiverState = BASELINE;

  for (let t = 0; t < steps; t += 1) {
    detectedCorrupt[t] = Math.abs(world.observed[t] - senderState) > DETECTOR_THRESHOLD;
    const wantsRepair = detectedCorrupt[t] && (policy === 'signed' || policy === 'factorized');
    repaired[t] = wantsRepair;

    if (wantsRepair) {
      senderState = RECEIVER_ALPHA * senderState + (1 - RECEIVER_ALPHA) * BASELINE;
    } else {
      senderState = SENDER_ALPHA * senderState + (1 - SENDER_ALPHA) * world.observed[t];
    }
    sender[t] = senderState;

    const receiverPrediction = RECEIVER_ALPHA * receiverState + (1 - RECEIVER_ALPHA) * BASELINE;
    let suppress = false;
    if (policy === 'factorized') suppress = world.private[t];
    else if (policy === 'signed') suppress = world.private[t] && !detectedCorrupt[t];

    let publish = policy === 'dense' || Math.abs(senderState - receiverPrediction) >= eventThreshold;
    publish = publish && !suppress;
    events[t] = publish;

    receiverState = publish ? senderState : receiverPrediction;
    receiver[t] = receiverState;
  }

  const privateEvents = events.filter((_, i) => world.private[i]);
  const overlap = world.private.map((value, i) => value && detectedCorrupt[i]);
  const overlapEvents = events.filter((_, i) => overlap[i]);

  return {
    policy,
    seed: Number(seed),
    eventThreshold: Number(eventThreshold),
    metrics: {
      senderRmse: rmse(sender, world.localTruth),
      receiverRmse: rmse(receiver, world.truth),
      eventFraction: mean(events.map(Number)),
      privateEventFraction: privateEvents.length ? mean(privateEvents.map(Number)) : 0,
      overlapEventFraction: overlapEvents.length ? mean(overlapEvents.map(Number)) : 0,
      recoveryRmse: recoveryRmse(world.truth, receiver, world.corrupt),
      detectorF1: f1(world.corrupt, detectedCorrupt),
    },
    trace: {
      truth: world.truth,
      localTruth: world.localTruth,
      observed: world.observed,
      sender,
      receiver,
      private: world.private,
      corrupt: world.corrupt,
      detectedCorrupt,
      repaired,
      events,
    },
  };
}

export function frontier(seed, thresholds = [0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18], steps = 1200) {
  const output = {};
  for (const policy of POLICIES) {
    output[policy] = thresholds.map((threshold) => {
      const result = simulate(policy, seed, threshold, steps);
      return {
        threshold,
        receiverRmse: result.metrics.receiverRmse,
        eventFraction: result.metrics.eventFraction,
        recoveryRmse: result.metrics.recoveryRmse,
      };
    });
  }
  return output;
}
