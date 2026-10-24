'use strict';
// Original 2D vector illustrations, generated from primitives with a seeded RNG so every
// render is byte-identical. Generators NEVER emit <text>: labels are returned as anchor
// points and rendered in the static HTML text layer. Each generator returns
//   { svg, timeline: [{ sel, preset, at, dur, stagger?, ease?, from? }], labels: [...] }
// where `sel` is a CSS selector scoped to the illustration root.

const f = (n) => (Math.round(n * 10) / 10).toString();
const pathFrom = (pts) => pts.map(([x, y], i) => `${i ? 'L' : 'M'}${f(x)} ${f(y)}`).join('');

function rng(seed = 1) {
  let a = seed >>> 0;
  const next = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  next.normal = () => {
    let u = 0;
    while (u === 0) u = next();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * next());
  };
  return next;
}

const phi = (x) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
// Acklam's inverse normal CDF (relative error < 1.2e-9).
function invNorm(p) {
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
  const pl = 0.02425;
  if (p < pl) { const q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
  if (p > 1 - pl) return -invNorm(1 - p);
  const q = p - 0.5, r = q * q;
  return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

const label = (text, x, y, opts = {}) => ({ text, x, y, anchor: opts.anchor || 'middle', valign: opts.valign || 'middle', size: opts.size || 24, color: opts.color || 'muted', weight: opts.weight || 700 });
const pick = (labels, i, fallback) => (labels && labels[i]) || fallback;

// --- Generators -----------------------------------------------------------------------

function gbmBand({ w, h, palette: P, params, labels }) {
  const r = rng(params.seed ?? 11);
  const n = Math.min(params.paths ?? 120, 200), steps = params.steps ?? 220;
  const mu = params.mu ?? 0.05, sigma = params.sigma ?? 0.4, dt = 1 / steps;
  const series = [];
  for (let k = 0; k < n; k++) {
    let x = 0; const s = [0];
    for (let i = 1; i <= steps; i++) { x += (mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * r.normal(); s.push(x); }
    series.push(s);
  }
  const all = series.flat();
  const lo = Math.min(...all), hi = Math.max(...all), pad = 18;
  const X = (i) => (i / steps) * w, Y = (v) => pad + (1 - (v - lo) / (hi - lo)) * (h - 2 * pad);
  const hl = series.reduce((best, s) => (Math.abs(s[steps] - 0.4) < Math.abs(best[steps] - 0.4) ? s : best), series[0]);
  const paths = series.filter((s) => s !== hl).map((s) => `<path class="p" d="${pathFrom(s.map((v, i) => [X(i), Y(v)]))}"/>`).join('');
  const drift = pathFrom([[0, Y(0)], [w, Y((mu - 0.5 * sigma * sigma))]]);
  return {
    svg: `<rect class="band" x="0" y="0" width="${w}" height="${h}" fill="${P.surface}"/>
<g class="paths" fill="none" stroke="${P.accent2}" stroke-width="1" stroke-opacity="0.22">${paths}</g>
<path class="drift" d="${drift}" fill="none" stroke="${P.accent}" stroke-width="2" stroke-dasharray="7 7"/>
<path class="hl" d="${pathFrom(hl.map((v, i) => [X(i), Y(v)]))}" fill="none" stroke="${P.accent2}" stroke-width="2.6"/>`,
    timeline: [
      { sel: '.paths .p', preset: 'draw', at: 0, dur: 1.6, stagger: { amount: 1.4 }, ease: 'power1.inOut' },
      { sel: '.drift', preset: 'fade', at: 1.4, dur: 0.6 },
      { sel: '.hl', preset: 'draw', at: 1.0, dur: 2.2, ease: 'power1.inOut' },
    ],
    labels: labels.length ? [label(labels[0], 56, 14, { anchor: 'start', valign: 'top', size: 16, color: 'muted', weight: 600 })] : [],
  };
}

function normalTail({ w, h, palette: P, params, labels }) {
  const alpha = params.alpha ?? 0.05, showES = params.showES ?? false;
  const z = invNorm(alpha); // negative
  const es = -phi(z) / alpha; // left-tail ES in sigma units
  const padX = 24, top = 70, bottom = 70;
  const xmin = -4, xmax = 4, ymax = phi(0);
  const X = (v) => padX + ((v - xmin) / (xmax - xmin)) * (w - 2 * padX);
  const Y = (v) => top + (1 - v / ymax) * (h - top - bottom);
  const base = Y(0);
  const curvePts = []; for (let i = 0; i <= 160; i++) { const v = xmin + (i / 160) * (xmax - xmin); curvePts.push([X(v), Y(phi(v))]); }
  const tailPts = []; for (let i = 0; i <= 60; i++) { const v = xmin + (i / 60) * (z - xmin); tailPts.push([X(v), Y(phi(v))]); }
  const bodyPts = []; for (let i = 0; i <= 120; i++) { const v = z + (i / 120) * (xmax - z); bodyPts.push([X(v), Y(phi(v))]); }
  const tail = `${pathFrom(tailPts)}L${f(X(z))} ${f(base)}L${f(X(xmin))} ${f(base)}Z`;
  const body = `${pathFrom(bodyPts)}L${f(X(xmax))} ${f(base)}L${f(X(z))} ${f(base)}Z`;
  // Markers rise into the empty band above the left shoulder; labels sit on top of them and
  // never touch the curve. ES (if shown) is a shorter marker with its label left-aligned to it.
  const varTop = top + 30, esTop = top + 96;
  const out = {
    svg: `<path class="axis" d="M${f(padX)} ${f(base)}H${f(w - padX)}" stroke="${P.muted}" stroke-width="2" fill="none"/>
<path class="body" d="${body}" fill="${P.accent2}" fill-opacity="0.14"/>
<path class="tail" d="${tail}" fill="${P.danger}" fill-opacity="0.9" data-origin="100% 100%"/>
<path class="curve" d="${pathFrom(curvePts)}" fill="none" stroke="${P.text}" stroke-width="3"/>
<path class="var" d="M${f(X(z))} ${f(base)}V${f(varTop)}" stroke="${P.accent}" stroke-width="3" stroke-dasharray="8 6" fill="none"/>
${showES ? `<path class="es" d="M${f(X(es))} ${f(base)}V${f(esTop)}" stroke="${P.danger}" stroke-width="3" fill="none"/>` : ''}`,
    timeline: [
      { sel: '.axis', preset: 'draw', at: 0, dur: 0.6 },
      { sel: '.curve', preset: 'draw', at: 0.3, dur: 1.4, ease: 'power2.inOut' },
      { sel: '.body', preset: 'fade', at: 1.3, dur: 0.6 },
      { sel: '.tail', preset: 'scale', at: 1.6, dur: 0.8, ease: 'power2.out' },
      { sel: '.var', preset: 'draw', at: 2.2, dur: 0.7 },
      ...(showES ? [{ sel: '.es', preset: 'draw', at: 2.9, dur: 0.6 }] : []),
    ],
    labels: [
      label(pick(labels, 0, 'VaR'), X(z), varTop - 12, { valign: 'bottom', color: 'accent', size: 26 }),
      label(pick(labels, 1, `${+(alpha * 100).toFixed(1)}% tail`), X((xmin + z) / 2), base + 16, { valign: 'top', color: 'danger', size: 22 }),
      label(pick(labels, 2, '1 − α'), X(0.6), Y(ymax) - 14, { valign: 'bottom', anchor: 'start', color: 'text', size: 24 }),
    ],
  };
  if (showES) out.labels.push(label(pick(labels, 3, 'ES'), X(es) + 8, esTop - 12, { valign: 'bottom', anchor: 'end', color: 'danger', size: 24 }));
  return out;
}

function covMatrix({ w, h, palette: P, params, labels }) {
  const n = Math.max(3, Math.min(params.n ?? 5, 8));
  const r = rng(params.seed ?? 5);
  // Random one-factor loadings -> valid correlation matrix.
  const beta = Array.from({ length: n }, () => 0.35 + 0.55 * r());
  const C = beta.map((bi, i) => beta.map((bj, j) => (i === j ? 1 : bi * bj)));
  const headerH = labels.length ? 44 : 0;
  const size = Math.min(w, h - headerH - 10);
  const gap = 6, cell = (size - gap * (n - 1)) / n;
  const ox = (w - size) / 2, oy = headerH + (h - headerH - size) / 2;
  const mix = (t) => {
    const a = [0x16, 0x18, 0x1d], b = [parseInt(P.accent2.slice(1, 3), 16), parseInt(P.accent2.slice(3, 5), 16), parseInt(P.accent2.slice(5, 7), 16)];
    return '#' + a.map((v, k) => Math.round(v + (b[k] - v) * t).toString(16).padStart(2, '0')).join('');
  };
  let cells = '';
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const fill = i === j ? P.accent : mix(0.2 + 0.8 * C[i][j]);
    cells += `<rect class="c" x="${f(ox + j * (cell + gap))}" y="${f(oy + i * (cell + gap))}" width="${f(cell)}" height="${f(cell)}" rx="6" fill="${fill}"/>`;
  }
  return {
    svg: `<g class="cells">${cells}</g>`,
    timeline: [{ sel: '.cells .c', preset: 'scale', at: 0.1, dur: 0.5, stagger: { grid: [n, n], from: 0, amount: 1.6 }, ease: 'power2.out' }],
    labels: labels.slice(0, n).map((t, j) => label(t, ox + j * (cell + gap) + cell / 2, headerH / 2, { size: 20, color: 'muted' })),
  };
}

function sortedReturns({ w, h, palette: P, params, labels }) {
  const n = Math.min(params.n ?? 60, 120), worst = params.worst ?? 5;
  const r = rng(params.seed ?? 3);
  // Student-t(4)-like draws for fat tails.
  const t4 = () => { const zz = r.normal(); let chi = 0; for (let k = 0; k < 4; k++) { const g = r.normal(); chi += g * g; } return zz / Math.sqrt(chi / 4); };
  const rets = Array.from({ length: n }, () => 0.01 * t4()).sort((a, b) => a - b);
  const top = 56, bottom = 46, padX = 8;
  const lo = rets[0], hi = rets[n - 1];
  const Y = (v) => top + ((hi - v) / (hi - lo)) * (h - top - bottom);
  const y0 = Y(0), bw = (w - 2 * padX) / n;
  let bars = '';
  rets.forEach((v, i) => {
    const x = padX + i * bw + bw * 0.15, bwi = bw * 0.7;
    const yTop = Math.min(Y(v), y0), hh = Math.max(Math.abs(Y(v) - y0), 1.5);
    const color = i < worst ? P.danger : v < 0 ? P.muted : P.accent2;
    bars += `<rect class="b" x="${f(x)}" y="${f(yTop)}" width="${f(bwi)}" height="${f(hh)}" fill="${color}" data-origin="${v < 0 ? '50% 0%' : '50% 100%'}"/>`;
  });
  const mx = padX + worst * bw;
  return {
    svg: `<path class="zero" d="M${padX} ${f(y0)}H${f(w - padX)}" stroke="${P.grid}" stroke-width="2"/>
<g class="bars">${bars}</g>
<path class="cut" d="M${f(mx)} ${f(h - bottom + 6)}V${f(top - 10)}" stroke="${P.accent}" stroke-width="3" stroke-dasharray="8 6" fill="none"/>`,
    timeline: [
      { sel: '.zero', preset: 'draw', at: 0, dur: 0.5 },
      { sel: '.bars .b', preset: 'scale', at: 0.3, dur: 0.5, stagger: { amount: 1.6 }, ease: 'power2.out' },
      { sel: '.cut', preset: 'draw', at: 2.3, dur: 0.7 },
    ],
    labels: [
      label(pick(labels, 0, `${worst}th worst → VaR`), Math.min(mx + 10, w - 10), top - 30, { anchor: 'start', color: 'accent', size: 24 }),
      label(pick(labels, 1, 'worst day'), padX, h - 18, { anchor: 'start', size: 20 }),
      label(pick(labels, 2, 'best day'), w - padX, h - 18, { anchor: 'end', size: 20 }),
    ],
  };
}

function mcPaths({ w, h, palette: P, params, labels }) {
  const r = rng(params.seed ?? 21);
  const n = Math.min(params.paths ?? 40, 120), steps = params.steps ?? 120;
  const mu = params.mu ?? 0.06, sigma = params.sigma ?? 0.3, dt = 1 / steps;
  const series = [];
  for (let k = 0; k < n; k++) { let x = 0; const s = [0]; for (let i = 1; i <= steps; i++) { x += (mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * r.normal(); s.push(x); } series.push(s); }
  const left = 56, top = 52, bottom = 24, histW = w * 0.24, plotR = w - histW - 18;
  const all = series.flat(); const lo = Math.min(...all), hi = Math.max(...all);
  const X = (i) => left + (i / steps) * (plotR - left), Y = (v) => top + (1 - (v - lo) / (hi - lo)) * (h - top - bottom);
  const paths = series.map((s) => `<path class="p" d="${pathFrom(s.map((v, i) => [X(i), Y(v)]))}"/>`).join('');
  const bins = 14, counts = Array(bins).fill(0);
  const ends = series.map((s) => s[steps]);
  ends.forEach((v) => { counts[Math.min(bins - 1, Math.floor(((v - lo) / (hi - lo)) * bins))]++; });
  const maxC = Math.max(...counts), bh = (h - top - bottom) / bins;
  let hist = '';
  counts.forEach((c, b) => {
    const y = top + (bins - 1 - b) * bh;
    hist += `<rect class="hb" x="${f(plotR + 18)}" y="${f(y + 1.5)}" width="${f(Math.max(2, (c / maxC) * (histW - 6)))}" height="${f(bh - 3)}" fill="${P.accent2}" fill-opacity="0.85" data-origin="0% 50%"/>`;
  });
  const q = [...ends].sort((a, b) => a - b)[Math.floor(0.05 * n)];
  return {
    svg: `<g class="paths" fill="none" stroke="${P.accent2}" stroke-width="1.4" stroke-opacity="0.45">${paths}</g>
<circle class="s0" cx="${f(X(0))}" cy="${f(Y(0))}" r="6" fill="${P.accent}"/>
<g class="hist">${hist}</g>
<path class="q" d="M${f(plotR + 10)} ${f(Y(q))}H${f(w - 4)}" stroke="${P.danger}" stroke-width="3" stroke-dasharray="7 5" fill="none"/>`,
    timeline: [
      { sel: '.paths .p', preset: 'draw', at: 0.2, dur: 1.8, stagger: { amount: 0.8 }, ease: 'power1.inOut' },
      { sel: '.hist .hb', preset: 'scale', at: 2.2, dur: 0.5, stagger: { amount: 0.5 }, ease: 'power2.out' },
      { sel: '.q', preset: 'draw', at: 3.0, dur: 0.5 },
    ],
    labels: [
      label(pick(labels, 0, 'S₀'), X(0) - 16, Y(0), { anchor: 'end', color: 'accent', size: 24 }),
      label(pick(labels, 1, 'paths'), left, 18, { anchor: 'start', size: 20 }),
      label(pick(labels, 2, 'S_T'), plotR + 18 + histW / 2, 18, { size: 20 }),
    ],
  };
}

function backtest({ w, h, palette: P, params, labels }) {
  const days = Math.min(params.days ?? 250, 400), exc = Math.max(0, Math.min(params.exceptions ?? 3, 15));
  const r = rng(params.seed ?? 8);
  const z = 2.326;
  const vol = []; let v = 1;
  for (let d = 0; d < days; d++) { v = Math.max(0.6, Math.min(1.6, v + 0.05 * r.normal())); vol.push(v); }
  const pnl = vol.map((s) => s * Math.max(-z * 0.97, Math.min(3.2, r.normal())));
  const picks = new Set(); while (picks.size < exc) picks.add(10 + Math.floor(r() * (days - 20)));
  for (const d of picks) pnl[d] = -vol[d] * (z + 0.25 + 0.6 * r());
  const stripH = 22, stripGap = 58, top = 20, plotB = h - stripH - stripGap - 30;
  const lo = Math.min(...pnl, ...vol.map((s) => -z * s)) * 1.05, hi = Math.max(...pnl) * 1.05;
  const padX = 6, bw = (w - 2 * padX) / days;
  const Y = (x) => top + ((hi - x) / (hi - lo)) * (plotB - top); const y0 = Y(0);
  let bars = '', dots = '';
  pnl.forEach((x, d) => {
    const yT = Math.min(Y(x), y0), hh = Math.max(Math.abs(Y(x) - y0), 1);
    const color = picks.has(d) ? P.danger : x < 0 ? P.muted : P.accent2;
    bars += `<rect class="b" x="${f(padX + d * bw)}" y="${f(yT)}" width="${f(Math.max(bw * 0.75, 1))}" height="${f(hh)}" fill="${color}" data-origin="${x < 0 ? '50% 0%' : '50% 100%'}"/>`;
    if (picks.has(d)) dots += `<circle class="x" cx="${f(padX + d * bw + bw / 2)}" cy="${f(Y(x) + 11)}" r="6" fill="none" stroke="${P.danger}" stroke-width="2.5"/>`;
  });
  const varLine = pathFrom(vol.map((s, d) => [padX + d * bw + bw / 2, Y(-z * s)]));
  const sy = plotB + stripGap, segW = (w - 2 * padX - 16) / 3;
  const zone = (i, c) => `<rect class="z" x="${f(padX + i * (segW + 8))}" y="${f(sy)}" width="${f(segW)}" height="${stripH}" rx="4" fill="${c}" data-origin="0% 50%"/>`;
  const zoneIdx = exc <= 4 ? 0 : exc <= 9 ? 1 : 2;
  const mX = padX + zoneIdx * (segW + 8) + (segW * (zoneIdx === 0 ? exc / 4 : zoneIdx === 1 ? (exc - 5) / 4 : 0.5));
  return {
    svg: `<path class="zero" d="M${padX} ${f(y0)}H${f(w - padX)}" stroke="${P.grid}" stroke-width="1.5"/>
<g class="bars">${bars}</g>
<path class="varline" d="${varLine}" fill="none" stroke="${P.accent}" stroke-width="2.5"/>
<g class="dots">${dots}</g>
<g class="zones">${zone(0, P.positive)}${zone(1, P.accent)}${zone(2, P.danger)}</g>
<path class="marker" d="M${f(mX)} ${f(sy - 4)}l-9 -14h18z" fill="${P.text}" data-origin="50% 100%"/>`,
    timeline: [
      { sel: '.zero', preset: 'draw', at: 0, dur: 0.4 },
      { sel: '.bars .b', preset: 'scale', at: 0.2, dur: 0.3, stagger: { amount: 1.6 }, ease: 'power1.out' },
      { sel: '.varline', preset: 'draw', at: 1.0, dur: 1.4, ease: 'none' },
      { sel: '.dots .x', preset: 'scale', at: 2.4, dur: 0.4, stagger: { amount: 0.4 }, ease: 'power2.out' },
      { sel: '.zones .z', preset: 'scale', at: 2.6, dur: 0.5, stagger: { amount: 0.3 }, ease: 'power2.out' },
      { sel: '.marker', preset: 'scale', at: 3.3, dur: 0.4, ease: 'power2.out' },
    ],
    labels: [
      label(pick(labels, 0, 'green 0–4'), padX + segW / 2, sy + stripH + 22, { size: 20, color: 'positive' }),
      label(pick(labels, 1, 'amber 5–9'), padX + segW * 1.5 + 8, sy + stripH + 22, { size: 20, color: 'accent' }),
      label(pick(labels, 2, 'red 10+'), padX + segW * 2.5 + 16, sy + stripH + 22, { size: 20, color: 'danger' }),
    ],
  };
}

function sqrtTime({ w, h, palette: P, params, labels }) {
  const H = params.horizon ?? 10;
  const left = 30, right = 30, top = 60, bottom = 50;
  const X = (d) => left + ((d - 0) / H) * (w - left - right), Y = (v) => top + (1 - v / Math.sqrt(H)) * (h - top - bottom);
  const pts = []; for (let i = 0; i <= 100; i++) { const d = 1 + (i / 100) * (H - 1); pts.push([X(d), Y(Math.sqrt(d))]); }
  const b = Y(0);
  return {
    svg: `<path class="axes" d="M${left} ${top - 20}V${f(b)}H${f(w - right + 10)}" fill="none" stroke="${P.muted}" stroke-width="2"/>
<path class="curve" d="${pathFrom(pts)}" fill="none" stroke="${P.accent2}" stroke-width="3.5"/>
<path class="drop" d="M${f(X(1))} ${f(Y(1))}V${f(b)}M${f(X(H))} ${f(Y(Math.sqrt(H)))}V${f(b)}" stroke="${P.accent}" stroke-width="2" stroke-dasharray="6 6" fill="none"/>
<circle class="pt" cx="${f(X(1))}" cy="${f(Y(1))}" r="8" fill="${P.accent}"/><circle class="pt" cx="${f(X(H))}" cy="${f(Y(Math.sqrt(H)))}" r="8" fill="${P.accent}"/>`,
    timeline: [
      { sel: '.axes', preset: 'draw', at: 0, dur: 0.6 },
      { sel: '.curve', preset: 'draw', at: 0.5, dur: 1.4, ease: 'power2.inOut' },
      { sel: '.drop', preset: 'draw', at: 1.9, dur: 0.6 },
      { sel: '.pt', preset: 'scale', at: 2.0, dur: 0.4, stagger: { amount: 0.4 }, ease: 'power2.out' },
    ],
    labels: [
      label(pick(labels, 0, '1 day'), X(1), b + 26, { valign: 'top', size: 22 }),
      label(pick(labels, 1, `${H} days`), X(H), b + 26, { valign: 'top', size: 22 }),
      label(pick(labels, 2, `×√${H} ≈ ${Math.sqrt(H).toFixed(2)}`), X(H) - 14, Y(Math.sqrt(H)) - 24, { anchor: 'end', valign: 'bottom', color: 'accent', size: 26 }),
    ],
  };
}

function payoff({ w, h, palette: P, params, labels }) {
  const kind = params.kind === 'put' ? 'put' : 'call';
  const left = 30, right = 30, top = 40, bottom = 50;
  const K = 0.5, X = (s) => left + s * (w - left - right), Y = (v) => top + (1 - v / 0.55) * (h - top - bottom);
  const pts = kind === 'call' ? [[0, 0], [K, 0], [1, 0.5]] : [[0, 0.5], [K, 0], [1, 0]];
  return {
    svg: `<path class="axes" d="M${left} ${top - 10}V${f(Y(0))}H${f(w - right + 10)}" fill="none" stroke="${P.muted}" stroke-width="2"/>
<path class="pay" d="${pathFrom(pts.map(([s, v]) => [X(s), Y(v)]))}" fill="none" stroke="${P.accent2}" stroke-width="4"/>
<circle class="k" cx="${f(X(K))}" cy="${f(Y(0))}" r="8" fill="${P.accent}"/>`,
    timeline: [
      { sel: '.axes', preset: 'draw', at: 0, dur: 0.6 },
      { sel: '.pay', preset: 'draw', at: 0.5, dur: 1.4, ease: 'power2.inOut' },
      { sel: '.k', preset: 'scale', at: 1.9, dur: 0.4, ease: 'power2.out' },
    ],
    labels: [label(pick(labels, 0, 'K'), X(K), Y(0) + 28, { valign: 'top', color: 'accent', size: 24 }), label(pick(labels, 1, 'S_T'), w - right, Y(0) + 28, { anchor: 'end', valign: 'top', size: 22 })],
  };
}

function network({ w, h, palette: P, params, labels }) {
  const n = Math.max(4, Math.min(params.nodes ?? 7, 12));
  const r = rng(params.seed ?? 4);
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) / 2 - 50;
  const nodes = Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2 - Math.PI / 2; return [cx + R * Math.cos(a), cy + R * Math.sin(a)]; });
  const edges = []; for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (r() < 0.38 || j === i + 1) edges.push([i, j]);
  return {
    svg: `<g class="edges" stroke="${P.accent2}" stroke-width="2" stroke-opacity="0.7" fill="none">${edges.map(([i, j]) => `<path class="e" d="${pathFrom([nodes[i], nodes[j]])}"/>`).join('')}</g>
<g class="nodes">${nodes.map(([x, y], i) => `<circle class="n" cx="${f(x)}" cy="${f(y)}" r="${i === 0 ? 16 : 11}" fill="${i === 0 ? P.danger : P.accent}"/>`).join('')}</g>`,
    timeline: [
      { sel: '.nodes .n', preset: 'scale', at: 0, dur: 0.4, stagger: { amount: 0.6 }, ease: 'power2.out' },
      { sel: '.edges .e', preset: 'draw', at: 0.6, dur: 0.5, stagger: { amount: 1.8 } },
    ],
    labels: labels.slice(0, n).map((t, i) => { const [x, y] = nodes[i]; const out = 34; const a = (i / n) * Math.PI * 2 - Math.PI / 2; return label(t, x + out * Math.cos(a), y + out * Math.sin(a), { size: 20, anchor: Math.cos(a) > 0.3 ? 'start' : Math.cos(a) < -0.3 ? 'end' : 'middle' }); }),
  };
}

function flow({ w, h, palette: P, labels }) {
  const steps = Math.max(2, Math.min(labels.length || 4, 6));
  const boxH = Math.min(84, (h - (steps - 1) * 36) / steps), boxW = w - 40;
  const gap = (h - steps * boxH) / (steps - 1);
  let boxes = '', arrows = '';
  const out = [];
  for (let i = 0; i < steps; i++) {
    const y = i * (boxH + gap);
    boxes += `<rect x="20" y="${f(y)}" width="${f(boxW)}" height="${f(boxH)}" rx="12" fill="none" stroke="${P.grid}" stroke-width="2"/>`;
    if (i < steps - 1) arrows += `<path class="a" d="M${f(w / 2)} ${f(y + boxH + 4)}V${f(y + boxH + gap - 6)}" stroke="${P.accent}" stroke-width="3" fill="none"/>`;
    out.push(label(labels[i] || `Step ${i + 1}`, w / 2, y + boxH / 2, { size: 24, color: 'text' }));
  }
  return {
    svg: `<g class="boxes">${boxes}</g><g class="arrows">${arrows}</g>`,
    timeline: [{ sel: '.arrows .a', preset: 'draw', at: 0.3, dur: 0.5, stagger: { each: 0.6 } }],
    labels: out,
  };
}

const GENERATORS = {
  'gbm-band': gbmBand, 'normal-tail': normalTail, 'cov-matrix': covMatrix, 'sorted-returns': sortedReturns,
  'mc-paths': mcPaths, backtest, 'sqrt-time': sqrtTime, payoff, network, flow,
};

function renderIllustration(type, ctx) {
  const gen = GENERATORS[type];
  if (!gen) return null;
  const out = gen({ labels: [], params: {}, ...ctx });
  if (/<text[\s>]|<foreignObject/i.test(out.svg)) throw new Error(`Illustration ${type} emitted text: forbidden in the animated layer`);
  return out;
}

module.exports = { renderIllustration, GENERATORS, invNorm, phi, rng };
