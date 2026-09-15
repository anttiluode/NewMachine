import assert from 'node:assert/strict';

import { createLiveVectorMachine } from '../web/vector_live.mjs';


function close(actual, expected, tolerance = 1e-12) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);
}

const first = createLiveVectorMachine(11, { eventThreshold: 0.10, repair: true });
const second = createLiveVectorMachine(11, { eventThreshold: 0.10, repair: true });

const firstPrefix = [];
const secondPrefix = [];
for (let i = 0; i < 64; i += 1) {
  firstPrefix.push(first.step());
  secondPrefix.push(second.step());
}
assert.deepEqual(firstPrefix, secondPrefix);

const learner = createLiveVectorMachine(11, { eventThreshold: 0.10, repair: true });
const initial = learner.metrics().sharedAlignment;
for (let i = 0; i < 3500; i += 1) learner.step();
const learned = learner.metrics();

assert.ok(initial < 0.45, `initial alignment unexpectedly high: ${initial}`);
assert.ok(learned.sharedAlignment > 0.90, `learner did not recover shared subspace: ${learned.sharedAlignment}`);
assert.ok(learned.sharedAlignment > initial + 0.55);
assert.ok(learned.receiverRmse >= 0);
assert.ok(learned.senderRmse >= 0);
assert.ok(learned.eventFraction >= 0 && learned.eventFraction <= 1);
assert.ok(learned.detectorF1 >= 0 && learned.detectorF1 <= 1);
assert.ok(learned.steps === 3500);

const frame = learner.step();
assert.equal(frame.publicTruth.length, 6);
assert.equal(frame.senderState.length, 6);
assert.equal(frame.receiverState.length, 6);
assert.equal(frame.publicationProjector.length, 6);
assert.equal(frame.publicationProjector[0].length, 6);
assert.ok(Number.isFinite(frame.truthCoordinate));
assert.ok(Number.isFinite(frame.senderCoordinate));
assert.ok(Number.isFinite(frame.receiverCoordinate));

const raw = createLiveVectorMachine(11, { eventThreshold: 0.10, repair: false, publication: 'raw' });
for (let i = 0; i < 256; i += 1) raw.step();
const rawMetrics = raw.metrics();
assert.ok(rawMetrics.eventFraction > 0);
close(rawMetrics.sharedAlignment, initial, 1e-12);

console.log('web live vector learner tests passed');
