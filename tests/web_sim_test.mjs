import assert from 'node:assert/strict';

import { generateWorld, simulate } from '../web/sim.mjs';


function close(actual, expected, tolerance = 1e-12) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);
}

const world = generateWorld(5, 5);
const expectedTruth = [
  0.5404864738415928,
  0.5358238716455549,
  0.5439477762996894,
  0.5531124422405792,
  0.5507769905098026,
];
const expectedObserved = [
  0.5278003697935493,
  0.5353709399732203,
  0.5371138781912368,
  0.5341451973547173,
  0.567071698072577,
];
for (let i = 0; i < expectedTruth.length; i += 1) {
  close(world.truth[i], expectedTruth[i]);
  close(world.observed[i], expectedObserved[i]);
}

const first = simulate('factorized', 11, 0.04, 900);
const second = simulate('factorized', 11, 0.04, 900);
assert.deepEqual(first, second);

let overlapCount = 0;
for (let i = 0; i < first.trace.events.length; i += 1) {
  if (first.trace.private[i] && first.trace.detectedCorrupt[i]) {
    overlapCount += 1;
    assert.equal(first.trace.repaired[i], true);
    assert.equal(first.trace.events[i], false);
  }
}
assert.ok(overlapCount > 0);

const signed = simulate('signed', 19, 0.0, 900);
const factorized = simulate('factorized', 19, 0.0, 900);
assert.deepEqual(signed.trace.sender, factorized.trace.sender);

console.log('web simulation tests passed');
