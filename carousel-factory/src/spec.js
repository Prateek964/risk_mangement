'use strict';
// design-spec.json schema (v1) and validator. ChatGPT output is untrusted input: it is parsed
// as JSON, checked field by field, and only whitelisted values reach the renderer.

const LAYOUTS = ['cover', 'concept', 'closing'];
const ILLUSTRATIONS = ['gbm-band', 'normal-tail', 'cov-matrix', 'sorted-returns', 'mc-paths', 'backtest', 'sqrt-time', 'payoff', 'network', 'flow', 'none'];
const SIDES = ['right', 'left', 'bottom'];
const DECOR_SLOTS = ['top-left', 'top-right', 'mid-left', 'mid-right', 'bottom-left', 'bottom-right'];
const HEX = /^#[0-9a-fA-F]{6}$/;

const DEFAULT_PALETTE = {
  background: '#0B0C0F', backgroundAlt: '#16181D', surface: '#13213D', text: '#FFFFFF', muted: '#9AA1AD',
  accent: '#F2C14E', accent2: '#4FC3F7', danger: '#FF5C5C', positive: '#3DDC97', grid: '#2A2F38',
};

const LIMITS = { headline: 40, kicker: 60, subheadline: 80, label: 70, paragraph: 420, paragraphs: 3, equations: 6, tex: 220, labels: 8 };

function str(v, max, path, errors, { required = false } = {}) {
  if (v == null || v === '') {
    if (required) errors.push(`${path} is required`);
    return '';
  }
  if (typeof v !== 'string') { errors.push(`${path} must be a string`); return ''; }
  const s = v.replace(/\s+/g, ' ').trim();
  if (s.length > max) errors.push(`${path} is ${s.length} chars (max ${max})`);
  return s;
}

function validateSpec(raw, { slideCount, canvas } = {}) {
  const errors = [];
  const warnings = [];
  if (!raw || typeof raw !== 'object') return { ok: false, errors: ['spec is not an object'], warnings, spec: null };

  const palette = { ...DEFAULT_PALETTE };
  for (const [k, v] of Object.entries(raw.palette || {})) {
    if (!(k in DEFAULT_PALETTE)) { warnings.push(`palette.${k} ignored (unknown key)`); continue; }
    if (typeof v === 'string' && HEX.test(v)) palette[k] = v.toUpperCase();
    else errors.push(`palette.${k} must be a #RRGGBB hex value`);
  }

  const slidesIn = Array.isArray(raw.slides) ? raw.slides : [];
  if (!slidesIn.length) errors.push('slides[] is empty');
  if (slideCount && slidesIn.length !== slideCount) errors.push(`expected ${slideCount} slides, got ${slidesIn.length}`);

  const slides = slidesIn.map((s, i) => {
    const p = `slides[${i}]`;
    const layout = LAYOUTS.includes(s.layout) ? s.layout : (i === 0 ? 'cover' : i === slidesIn.length - 1 ? 'closing' : 'concept');
    if (s.layout && !LAYOUTS.includes(s.layout)) warnings.push(`${p}.layout "${s.layout}" replaced by "${layout}"`);
    const body = (Array.isArray(s.body) ? s.body : s.body ? [s.body] : []).map((b, j) => str(b, LIMITS.paragraph, `${p}.body[${j}]`, errors)).filter(Boolean);
    if (body.length > LIMITS.paragraphs) errors.push(`${p}.body has ${body.length} paragraphs (max ${LIMITS.paragraphs})`);
    const equations = (Array.isArray(s.equations) ? s.equations : []).map((e, j) => {
      const tex = str(e && e.tex, LIMITS.tex, `${p}.equations[${j}].tex`, errors, { required: true });
      const role = ['hero', 'decor'].includes(e && e.role) ? e.role : 'decor';
      let slot = e && e.slot;
      if (role === 'decor' && !DECOR_SLOTS.includes(slot)) { slot = DECOR_SLOTS[j % DECOR_SLOTS.length]; warnings.push(`${p}.equations[${j}].slot defaulted to ${slot}`); }
      return { tex, role, slot: role === 'decor' ? slot : null };
    });
    if (equations.length > LIMITS.equations) errors.push(`${p} has ${equations.length} equations (max ${LIMITS.equations})`);
    const slots = equations.filter((e) => e.role === 'decor').map((e) => e.slot);
    if (new Set(slots).size !== slots.length) errors.push(`${p} uses a decor equation slot twice`);
    if (equations.filter((e) => e.role === 'hero').length > 1) errors.push(`${p} has more than one hero equation`);

    const il = s.illustration || { type: 'none' };
    const type = ILLUSTRATIONS.includes(il.type) ? il.type : 'none';
    if (il.type && !ILLUSTRATIONS.includes(il.type)) errors.push(`${p}.illustration.type "${il.type}" is not in the vector library (${ILLUSTRATIONS.join(', ')})`);
    const params = {};
    for (const [k, v] of Object.entries(il.params || {})) {
      if (typeof v === 'number' && Number.isFinite(v)) params[k] = v;
      else if (typeof v === 'boolean') params[k] = v;
      else if (typeof v === 'string' && v.length <= 40 && /^[\w .,%$€£+\-−–/()]*$/.test(v)) params[k] = v;
      else warnings.push(`${p}.illustration.params.${k} dropped`);
    }
    const labels = (Array.isArray(il.labels) ? il.labels : []).slice(0, LIMITS.labels).map((l, j) => str(l, 40, `${p}.illustration.labels[${j}]`, errors)).filter(Boolean);

    return {
      index: i + 1,
      layout,
      side: SIDES.includes(s.side) ? s.side : layout === 'concept' ? 'right' : 'bottom',
      kicker: str(s.kicker, LIMITS.kicker, `${p}.kicker`, errors),
      headline: str(s.headline, LIMITS.headline, `${p}.headline`, errors, { required: true }),
      subheadline: str(s.subheadline, LIMITS.subheadline, `${p}.subheadline`, errors),
      label: str(s.label, LIMITS.label, `${p}.label`, errors),
      body,
      equations,
      cta: str(s.cta, 60, `${p}.cta`, errors),
      footnote: str(s.footnote, 140, `${p}.footnote`, errors),
      illustration: {
        type,
        params,
        labels,
        animate: il.animate !== false && type !== 'none',
        purpose: str(il.purpose, 200, `${p}.illustration.purpose`, warnings),
      },
    };
  });

  const spec = {
    schemaVersion: 1,
    topicId: raw.topicId || null,
    title: str(raw.title, 120, 'title', errors, { required: true }),
    brand: str(raw.brand, 30, 'brand', errors) || 'RISK HUB',
    creativeDirection: str(raw.creativeDirection, 1200, 'creativeDirection', warnings),
    canvas: canvas || { width: 1080, height: 1350, aspectRatio: '4:5' },
    palette,
    provenance: raw.provenance && typeof raw.provenance === 'object' ? raw.provenance : null,
    slides,
  };
  return { ok: errors.length === 0, errors, warnings, spec };
}

// Pull the first JSON object out of a ChatGPT reply (```json fences preferred).
function extractJson(text) {
  const fences = [...String(text).matchAll(/```(?:json)?\s*([\s\S]*?)```/g)].map((m) => m[1]);
  for (const cand of [...fences, text]) {
    const start = cand.indexOf('{');
    const end = cand.lastIndexOf('}');
    if (start < 0 || end <= start) continue;
    try { return JSON.parse(cand.slice(start, end + 1)); } catch {}
  }
  return null;
}

module.exports = { validateSpec, extractJson, LAYOUTS, ILLUSTRATIONS, DECOR_SLOTS, SIDES, DEFAULT_PALETTE, LIMITS };
