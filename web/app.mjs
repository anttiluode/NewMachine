import { frontier, simulate } from './sim.mjs';

const STEPS = 3600;
const HISTORY = 260;
const TICK_MS = 95;
const FRONTIER_THRESHOLDS = [0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18];

const el = {
  policy: document.querySelector('#policy'),
  seed: document.querySelector('#seed'),
  threshold: document.querySelector('#threshold'),
  thresholdValue: document.querySelector('#threshold-value'),
  runToggle: document.querySelector('#run-toggle'),
  stepOnce: document.querySelector('#step-once'),
  reset: document.querySelector('#reset-world'),
  receiverRmse: document.querySelector('#receiver-rmse'),
  senderRmse: document.querySelector('#sender-rmse'),
  messageRate: document.querySelector('#message-rate'),
  detectorF1: document.querySelector('#detector-f1'),
  status: document.querySelector('#world-status'),
  statusObservation: document.querySelector('#status-observation'),
  statusRelevance: document.querySelector('#status-relevance'),
  statusRepair: document.querySelector('#status-repair'),
  statusPublication: document.querySelector('#status-publication'),
  statusClock: document.querySelector('#status-clock'),
  trace: document.querySelector('#trace-canvas'),
  frontier: document.querySelector('#frontier-canvas'),
  messagePulse: document.querySelector('#message-pulse'),
};

const traceCtx = el.trace.getContext('2d');
const frontierCtx = el.frontier.getContext('2d');

let running = true;
let epoch = 0;
let cursor = 0;
let result = null;
let lastTick = 0;
let sums = null;

function selectedSeed() {
  const value = Number.parseInt(el.seed.value, 10);
  return Number.isFinite(value) ? Math.max(0, value) : 0;
}

function selectedThreshold() {
  return Number.parseFloat(el.threshold.value);
}

function freshSums() {
  return {
    count: 0,
    receiverSq: 0,
    senderSq: 0,
    events: 0,
    tp: 0,
    fp: 0,
    fn: 0,
  };
}

function resetSimulation({ keepEpoch = false } = {}) {
  if (!keepEpoch) epoch = 0;
  cursor = 0;
  sums = freshSums();
  const seed = selectedSeed() + epoch;
  result = simulate(el.policy.value, seed, selectedThreshold(), STEPS);
  el.thresholdValue.value = selectedThreshold().toFixed(2);
  drawFrontier();
  render();
}

function nextEpoch() {
  epoch += 1;
  cursor = 0;
  sums = freshSums();
  result = simulate(el.policy.value, selectedSeed() + epoch, selectedThreshold(), STEPS);
  drawFrontier();
}

function accumulate(index) {
  const t = result.trace;
  const receiverError = t.receiver[index] - t.truth[index];
  const senderError = t.sender[index] - t.localTruth[index];
  sums.receiverSq += receiverError * receiverError;
  sums.senderSq += senderError * senderError;
  sums.events += t.events[index] ? 1 : 0;
  sums.count += 1;

  const target = t.corrupt[index];
  const predicted = t.detectedCorrupt[index];
  if (target && predicted) sums.tp += 1;
  else if (!target && predicted) sums.fp += 1;
  else if (target && !predicted) sums.fn += 1;
}

function step() {
  if (!result) return;
  if (cursor >= STEPS) nextEpoch();
  accumulate(cursor);
  cursor += 1;
  render();
}

function detectorF1() {
  const denom = 2 * sums.tp + sums.fp + sums.fn;
  return denom === 0 ? 0 : (2 * sums.tp) / denom;
}

function renderMetrics() {
  if (!sums.count) {
    el.receiverRmse.textContent = '—';
    el.senderRmse.textContent = '—';
    el.messageRate.textContent = '—';
    el.detectorF1.textContent = '—';
    return;
  }
  el.receiverRmse.textContent = Math.sqrt(sums.receiverSq / sums.count).toFixed(4);
  el.senderRmse.textContent = Math.sqrt(sums.senderSq / sums.count).toFixed(4);
  el.messageRate.textContent = `${(100 * sums.events / sums.count).toFixed(1)}%`;
  el.detectorF1.textContent = detectorF1().toFixed(3);
}

function renderStatus() {
  const i = Math.max(0, Math.min(cursor - 1, STEPS - 1));
  const t = result.trace;
  const corrupt = t.corrupt[i];
  const privateState = t.private[i];
  const repaired = t.repaired[i];
  const event = t.events[i];

  el.statusObservation.textContent = corrupt ? 'CORRUPT' : 'reliable';
  el.statusObservation.className = corrupt ? 'danger-text' : '';
  el.statusRelevance.textContent = privateState ? 'LOCAL ONLY' : 'public';
  el.statusRepair.textContent = repaired ? 'REPAIR / HOLD' : 'integrate';
  el.statusPublication.textContent = event ? 'EVENT SENT' : 'coast silently';
  el.statusClock.textContent = `${epoch} / ${cursor}`;
  el.status.textContent = `${el.policy.value.toUpperCase()} · epoch ${epoch} · step ${cursor}`;
  el.messagePulse.classList.toggle('firing', event);
}

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function drawTrace() {
  const ctx = traceCtx;
  const width = el.trace.width;
  const height = el.trace.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#090d12';
  ctx.fillRect(0, 0, width, height);

  if (cursor <= 0) return;
  const start = Math.max(0, cursor - HISTORY);
  const end = cursor;
  const trace = result.trace;
  const values = [];
  for (let i = start; i < end; i += 1) {
    values.push(trace.truth[i], trace.sender[i], trace.receiver[i], trace.localTruth[i]);
  }
  let min = Math.min(...values);
  let max = Math.max(...values);
  const padding = Math.max(0.035, (max - min) * 0.16);
  min -= padding;
  max += padding;

  const left = 44;
  const right = width - 18;
  const top = 18;
  const bottom = height - 35;
  const span = Math.max(1, end - start - 1);
  const x = (i) => left + ((i - start) / span) * (right - left);
  const y = (v) => bottom - ((v - min) / (max - min)) * (bottom - top);

  for (let i = start; i < end; i += 1) {
    const x0 = x(i);
    const x1 = x(i + 1);
    if (trace.private[i]) {
      ctx.fillStyle = css('--private');
      ctx.fillRect(x0, top, Math.max(2, x1 - x0 + 1), bottom - top);
    }
    if (trace.corrupt[i]) {
      ctx.fillStyle = css('--corrupt');
      ctx.fillRect(x0, top, Math.max(2, x1 - x0 + 1), bottom - top);
    }
  }

  ctx.strokeStyle = '#1f2a36';
  ctx.lineWidth = 1;
  for (let g = 0; g <= 4; g += 1) {
    const gy = top + (g / 4) * (bottom - top);
    ctx.beginPath();
    ctx.moveTo(left, gy);
    ctx.lineTo(right, gy);
    ctx.stroke();
  }

  function line(data, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    for (let i = start; i < end; i += 1) {
      const px = x(i);
      const py = y(data[i]);
      if (i === start) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }

  line(trace.truth, css('--truth'), 2.2);
  line(trace.sender, css('--sender'), 2.1);
  line(trace.receiver, css('--receiver'), 2.3);

  ctx.strokeStyle = css('--event');
  ctx.lineWidth = 1.2;
  for (let i = start; i < end; i += 1) {
    if (!trace.events[i]) continue;
    const px = x(i);
    ctx.beginPath();
    ctx.moveTo(px, top);
    ctx.lineTo(px, top + 14);
    ctx.stroke();
  }

  ctx.fillStyle = '#6f7e91';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText(max.toFixed(2), 7, top + 4);
  ctx.fillText(min.toFixed(2), 7, bottom + 4);
  ctx.fillText(`last ${end - start} steps`, left, height - 11);
}

const policyColors = {
  dense: '#8693a6',
  delta: '#ff7e83',
  signed: '#ffba68',
  factorized: '#86e3ff',
};

function drawFrontier() {
  const ctx = frontierCtx;
  const width = el.frontier.width;
  const height = el.frontier.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#090d12';
  ctx.fillRect(0, 0, width, height);

  const data = frontier(selectedSeed() + epoch, FRONTIER_THRESHOLDS, 1200);
  const points = Object.values(data).flat();
  const maxX = Math.max(0.08, ...points.map((p) => p.eventFraction)) * 1.04;
  const maxY = Math.max(0.05, ...points.map((p) => p.receiverRmse)) * 1.08;
  const left = 72;
  const right = width - 28;
  const top = 28;
  const bottom = height - 55;
  const x = (value) => left + (value / maxX) * (right - left);
  const y = (value) => bottom - (value / maxY) * (bottom - top);

  ctx.strokeStyle = '#263240';
  ctx.fillStyle = '#738399';
  ctx.lineWidth = 1;
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  for (let g = 0; g <= 5; g += 1) {
    const frac = g / 5;
    const gx = left + frac * (right - left);
    const gy = bottom - frac * (bottom - top);
    ctx.beginPath(); ctx.moveTo(gx, top); ctx.lineTo(gx, bottom); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(left, gy); ctx.lineTo(right, gy); ctx.stroke();
    ctx.fillText(`${(frac * maxX * 100).toFixed(0)}%`, gx - 9, bottom + 21);
    ctx.fillText((frac * maxY).toFixed(2), 23, gy + 4);
  }
  ctx.fillStyle = '#91a0b4';
  ctx.fillText('message rate →', right - 105, height - 13);
  ctx.save();
  ctx.translate(14, top + 115);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('receiver RMSE →', 0, 0);
  ctx.restore();

  for (const [policy, series] of Object.entries(data)) {
    ctx.strokeStyle = policyColors[policy];
    ctx.fillStyle = policyColors[policy];
    ctx.lineWidth = policy === el.policy.value ? 3 : 1.6;
    ctx.globalAlpha = policy === el.policy.value ? 1 : 0.7;
    ctx.beginPath();
    series.forEach((point, index) => {
      const px = x(point.eventFraction);
      const py = y(point.receiverRmse);
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    series.forEach((point) => {
      const px = x(point.eventFraction);
      const py = y(point.receiverRmse);
      ctx.beginPath();
      ctx.arc(px, py, policy === el.policy.value ? 4.5 : 3.2, 0, Math.PI * 2);
      ctx.fill();
    });
  }
  ctx.globalAlpha = 1;
}

function render() {
  renderMetrics();
  renderStatus();
  drawTrace();
}

function frame(timestamp) {
  if (running && timestamp - lastTick >= TICK_MS) {
    step();
    lastTick = timestamp;
  }
  requestAnimationFrame(frame);
}

el.runToggle.addEventListener('click', () => {
  running = !running;
  el.runToggle.textContent = running ? 'Pause' : 'Run';
});

el.stepOnce.addEventListener('click', () => {
  if (running) {
    running = false;
    el.runToggle.textContent = 'Run';
  }
  step();
});

el.reset.addEventListener('click', () => resetSimulation());
el.policy.addEventListener('change', () => resetSimulation());
el.seed.addEventListener('change', () => resetSimulation());
el.threshold.addEventListener('input', () => {
  el.thresholdValue.value = selectedThreshold().toFixed(2);
});
el.threshold.addEventListener('change', () => resetSimulation({ keepEpoch: true }));

window.addEventListener('resize', () => {
  drawTrace();
  drawFrontier();
});

resetSimulation();
requestAnimationFrame(frame);
