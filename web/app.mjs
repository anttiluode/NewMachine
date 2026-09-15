import { createLiveVectorMachine } from './vector_live.mjs';

const HISTORY = 320;
const DEVELOPMENT_SAMPLES = 900;
const TICK_MS = 48;
const STEPS_PER_TICK = 4;
const DEVELOPMENT_STRIDE = 5;

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
  sharedAlignment: document.querySelector('#shared-alignment'),
  status: document.querySelector('#world-status'),
  statusObservation: document.querySelector('#status-observation'),
  statusRelevance: document.querySelector('#status-relevance'),
  statusRepair: document.querySelector('#status-repair'),
  statusPublication: document.querySelector('#status-publication'),
  statusClock: document.querySelector('#status-clock'),
  trace: document.querySelector('#trace-canvas'),
  development: document.querySelector('#frontier-canvas'),
  messagePulse: document.querySelector('#message-pulse'),
};

const traceCtx = el.trace.getContext('2d');
const developmentCtx = el.development.getContext('2d');

let running = true;
let machine = null;
let lastFrame = null;
let lastTick = 0;
let history = [];
let development = [];

const policyConfig = {
  'learned-repair': { publication: 'learned', repair: true },
  learned: { publication: 'learned', repair: false },
  raw: { publication: 'raw', repair: false },
};

function selectedSeed() {
  const value = Number.parseInt(el.seed.value, 10);
  return Number.isFinite(value) ? Math.max(0, value) : 0;
}

function selectedThreshold() {
  return Number.parseFloat(el.threshold.value);
}

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function applyPolicy() {
  if (!machine) return;
  const config = policyConfig[el.policy.value] ?? policyConfig['learned-repair'];
  machine.publication = config.publication;
  machine.repairEnabled = config.repair;
}

function resetSimulation() {
  const config = policyConfig[el.policy.value] ?? policyConfig['learned-repair'];
  machine = createLiveVectorMachine(selectedSeed(), {
    eventThreshold: selectedThreshold(),
    publication: config.publication,
    repair: config.repair,
  });
  lastFrame = null;
  history = [];
  development = [{ step: 0, ...machine.metrics() }];
  el.thresholdValue.value = selectedThreshold().toFixed(2);
  render();
}

function remember(frame) {
  history.push(frame);
  if (history.length > HISTORY) history.shift();

  if (frame.step % DEVELOPMENT_STRIDE === 0) {
    development.push({ step: frame.step, ...frame.metrics });
    if (development.length > DEVELOPMENT_SAMPLES) development.shift();
  }
}

function advance(count = 1) {
  for (let i = 0; i < count; i += 1) {
    lastFrame = machine.step();
    remember(lastFrame);
  }
  render();
}

function currentMetrics() {
  return lastFrame?.metrics ?? machine.metrics();
}

function renderMetrics() {
  const metrics = currentMetrics();
  el.receiverRmse.textContent = metrics.steps ? metrics.receiverRmse.toFixed(4) : '—';
  el.senderRmse.textContent = metrics.steps ? metrics.senderRmse.toFixed(4) : '—';
  el.messageRate.textContent = metrics.steps ? `${(100 * metrics.eventFraction).toFixed(1)}%` : '—';
  el.detectorF1.textContent = metrics.steps ? metrics.detectorF1.toFixed(3) : '—';
  el.sharedAlignment.textContent = metrics.sharedAlignment.toFixed(3);
}

function renderStatus() {
  const metrics = currentMetrics();
  if (!lastFrame) {
    el.statusObservation.textContent = 'unseen';
    el.statusObservation.className = '';
    el.statusRelevance.textContent = `${(100 * metrics.sharedAlignment).toFixed(1)}% aligned`;
    el.statusRepair.textContent = 'waiting';
    el.statusPublication.textContent = 'silent';
    el.statusClock.textContent = '0';
    el.status.textContent = `${el.policy.value.toUpperCase()} · newborn`;
    el.messagePulse.classList.remove('firing');
    return;
  }

  el.statusObservation.textContent = lastFrame.corrupt ? 'CORRUPT' : 'reliable';
  el.statusObservation.className = lastFrame.corrupt ? 'danger-text' : '';
  el.statusRelevance.textContent = `${(100 * metrics.sharedAlignment).toFixed(1)}% aligned`;
  el.statusRepair.textContent = lastFrame.repaired ? 'REPAIR / COAST' : 'integrate';
  el.statusPublication.textContent = lastFrame.event ? 'EVENT SENT' : 'receiver predicts';
  el.statusClock.textContent = String(lastFrame.step);
  el.status.textContent = `${el.policy.value.toUpperCase()} · age ${lastFrame.step}`;
  el.messagePulse.classList.toggle('firing', lastFrame.event);
}

function drawTrace() {
  const ctx = traceCtx;
  const width = el.trace.width;
  const height = el.trace.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#090d12';
  ctx.fillRect(0, 0, width, height);

  if (!history.length) return;

  const values = history.flatMap((frame) => [
    frame.truthCoordinate,
    frame.senderCoordinate,
    frame.receiverCoordinate,
  ]);
  let min = Math.min(...values);
  let max = Math.max(...values);
  const padding = Math.max(0.035, (max - min) * 0.16);
  min -= padding;
  max += padding;

  const left = 48;
  const right = width - 18;
  const top = 18;
  const bottom = height - 35;
  const span = Math.max(1, history.length - 1);
  const x = (index) => left + (index / span) * (right - left);
  const y = (value) => bottom - ((value - min) / Math.max(1e-9, max - min)) * (bottom - top);

  for (let i = 0; i < history.length; i += 1) {
    const frame = history[i];
    if (!frame.corrupt) continue;
    const x0 = x(i);
    const x1 = x(Math.min(span, i + 1));
    ctx.fillStyle = css('--corrupt');
    ctx.fillRect(x0, top, Math.max(2, x1 - x0 + 1), bottom - top);
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

  function line(accessor, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    history.forEach((frame, index) => {
      const px = x(index);
      const py = y(accessor(frame));
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  line((frame) => frame.truthCoordinate, css('--truth'), 2.2);
  line((frame) => frame.senderCoordinate, css('--sender'), 2.0);
  line((frame) => frame.receiverCoordinate, css('--receiver'), 2.3);

  ctx.strokeStyle = css('--event');
  ctx.lineWidth = 1.1;
  history.forEach((frame, index) => {
    if (!frame.event) return;
    const px = x(index);
    ctx.beginPath();
    ctx.moveTo(px, top);
    ctx.lineTo(px, top + 14);
    ctx.stroke();
  });

  ctx.fillStyle = '#6f7e91';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText(max.toFixed(2), 8, top + 4);
  ctx.fillText(min.toFixed(2), 8, bottom + 4);
  ctx.fillText(`last ${history.length} steps · evaluator public coordinate`, left, height - 11);
}

function drawProjectorHeatmap(ctx, projector, x0, y0, size) {
  const cell = size / 6;
  ctx.fillStyle = '#91a0b4';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('CURRENT PUBLICATION PROJECTOR', x0, y0 - 13);

  for (let row = 0; row < 6; row += 1) {
    for (let column = 0; column < 6; column += 1) {
      const value = Math.min(1, Math.abs(projector[row][column]));
      ctx.fillStyle = `rgba(134, 227, 255, ${0.08 + 0.84 * value})`;
      ctx.fillRect(x0 + column * cell, y0 + row * cell, cell - 2, cell - 2);
    }
  }
  ctx.strokeStyle = '#334253';
  ctx.strokeRect(x0 - 1, y0 - 1, size + 1, size + 1);
  ctx.fillStyle = '#69798c';
  ctx.fillText('6 × 6 · |Pᵢⱼ|', x0, y0 + size + 20);
}

function drawDevelopment() {
  const ctx = developmentCtx;
  const width = el.development.width;
  const height = el.development.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#090d12';
  ctx.fillRect(0, 0, width, height);

  const left = 58;
  const chartRight = Math.floor(width * 0.69);
  const top = 28;
  const bottom = height - 55;
  const entries = development.length ? development : [{ step: 0, ...machine.metrics() }];
  const minStep = entries[0].step;
  const maxStep = Math.max(minStep + 1, entries[entries.length - 1].step);
  const x = (step) => left + ((step - minStep) / (maxStep - minStep)) * (chartRight - left);
  const y = (value) => bottom - Math.max(0, Math.min(1, value)) * (bottom - top);

  ctx.strokeStyle = '#263240';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#738399';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  for (let g = 0; g <= 4; g += 1) {
    const value = g / 4;
    const gy = y(value);
    ctx.beginPath();
    ctx.moveTo(left, gy);
    ctx.lineTo(chartRight, gy);
    ctx.stroke();
    ctx.fillText(value.toFixed(2), 18, gy + 4);
  }

  function curve(accessor, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    entries.forEach((entry, index) => {
      const px = x(entry.step);
      const py = y(accessor(entry));
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  curve((entry) => entry.sharedAlignment, css('--alignment'), 2.8);
  curve((entry) => entry.eventFraction, css('--traffic'), 1.8);

  ctx.fillStyle = '#718197';
  ctx.fillText(`step ${minStep}`, left, bottom + 22);
  const endLabel = `step ${maxStep}`;
  ctx.fillText(endLabel, chartRight - ctx.measureText(endLabel).width, bottom + 22);
  ctx.fillText('alignment / cumulative message rate', left, height - 12);

  const projector = lastFrame?.publicationProjector ?? machine.publicationProjector();
  const heatSize = Math.min(245, height - 105);
  drawProjectorHeatmap(ctx, projector, width - heatSize - 38, 60, heatSize);
}

function render() {
  renderMetrics();
  renderStatus();
  drawTrace();
  drawDevelopment();
}

function frame(timestamp) {
  if (running && timestamp - lastTick >= TICK_MS) {
    advance(STEPS_PER_TICK);
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
  advance(1);
});

el.reset.addEventListener('click', resetSimulation);
el.seed.addEventListener('change', resetSimulation);
el.policy.addEventListener('change', () => {
  applyPolicy();
  render();
});
el.threshold.addEventListener('input', () => {
  const threshold = selectedThreshold();
  el.thresholdValue.value = threshold.toFixed(2);
  if (machine) machine.eventThreshold = threshold;
});

window.addEventListener('resize', render);

resetSimulation();
requestAnimationFrame(frame);
