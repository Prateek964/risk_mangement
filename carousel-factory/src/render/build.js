'use strict';
// Builds the editable carousel project from a validated design spec:
//   carousel/index.html            all slides, layered (bg / art / text)
//   carousel/assets/...            fonts, KaTeX, GSAP, runtime, styles (vendored, offline)
//   carousel/slides.json           structured slide content + animation timelines
//   carousel/illustrations/*.svg   standalone SVG source for each illustration
const fs = require('fs');
const path = require('path');
const katex = require('katex');
const { renderIllustration } = require('./illustrations');

const NM = path.resolve(__dirname, '..', '..', 'node_modules');
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function tex(src, displayMode) {
  return katex.renderToString(src, { displayMode, output: 'html', throwOnError: false, trust: false, strict: 'ignore' });
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}

function vendorAssets(dir) {
  const a = path.join(dir, 'assets');
  fs.mkdirSync(a, { recursive: true });
  fs.copyFileSync(path.join(NM, 'gsap/dist/gsap.min.js'), path.join(a, 'gsap.min.js'));
  copyDir(path.join(NM, 'katex/dist/fonts'), path.join(a, 'katex/fonts'));
  fs.copyFileSync(path.join(NM, 'katex/dist/katex.min.css'), path.join(a, 'katex/katex.min.css'));
  const fontCss = [];
  for (const [pkg, weights] of [['inter', [500, 600, 700, 800]], ['inter-tight', [700, 800]]]) {
    const files = path.join(a, 'fonts', pkg, 'files');
    fs.mkdirSync(files, { recursive: true });
    for (const w of weights) {
      const css = fs.readFileSync(path.join(NM, '@fontsource', pkg, `${w}.css`), 'utf8');
      for (const m of css.matchAll(/url\(\.\/files\/([^)]+)\)/g)) fs.copyFileSync(path.join(NM, '@fontsource', pkg, 'files', m[1]), path.join(files, m[1]));
      fontCss.push(css.replace(/url\(\.\/files\//g, `url(./${pkg}/files/`));
    }
  }
  fs.writeFileSync(path.join(a, 'fonts', 'fonts.css'), fontCss.join('\n'));
  fs.copyFileSync(path.join(__dirname, 'assets', 'runtime.js'), path.join(a, 'runtime.js'));
  fs.copyFileSync(path.join(__dirname, 'assets', 'styles.css'), path.join(a, 'styles.css'));
}

// ---- Layout geometry (px). Regions are fixed per layout; text fits into them at load. ----
function geometry(layout, side, W, H) {
  const M = 56;
  const g = {
    M,
    decor: {
      'top-left': { x: M, y: 64, w: 470, align: 'left' },
      'top-right': { x: W - M - 470, y: 64, w: 470, align: 'right' },
      'bottom-left': { x: M, y: H - 210, w: 470, align: 'left' },
      'bottom-right': { x: W - M - 470, y: H - 210, w: 470, align: 'right' },
    },
    headline: { x: M, y: 178, w: W - 2 * M, h: 128 },
    footer: { y: H - 74 },
  };
  if (layout === 'cover') {
    Object.assign(g.decor, {
      'mid-left': { x: M, y: 250, w: 470, align: 'left' },
      'mid-right': { x: W - M - 470, y: 250, w: 470, align: 'right' },
      'bottom-left': { x: M, y: H - 230, w: 470, align: 'left' },
      'bottom-right': { x: W - M - 470, y: H - 230, w: 470, align: 'right' },
    });
    g.illus = { x: 0, y: 390, w: W, h: 340, fullBleed: true };
    g.kicker = { x: M, y: 790, w: W - 2 * M };
    g.headline = { x: M - 6, y: 850, w: W - 2 * M + 12, h: 150, align: 'left' };
    g.subheadline = { x: M, y: 1010, w: W - 2 * M, align: 'right' };
  } else if (layout === 'closing') {
    g.column = { x: M, y: 340, w: W - 2 * M, h: 300 };
    g.illus = { x: M + 60, y: 670, w: W - 2 * M - 120, h: 330 };
    g.cta = { x: M + 120, y: 1030, w: W - 2 * M - 240, h: 92 };
  } else if (side === 'bottom') {
    g.column = { x: M, y: 340, w: W - 2 * M, h: 390 };
    g.illus = { x: M, y: 760, w: W - 2 * M, h: 360 };
  } else {
    const colW = 488, gap = 36, illW = W - 2 * M - colW - gap;
    const left = side === 'left';
    g.column = { x: left ? W - M - colW : M, y: 350, w: colW, h: 770 };
    g.illus = { x: left ? M : M + colW + gap, y: 380, w: illW, h: 520 };
    g.decor['mid-left'] = { x: M, y: 940, w: illW, align: 'left' };
    g.decor['mid-right'] = { x: W - M - illW, y: 940, w: illW, align: 'right' };
    // The decor slot under the illustration is on the illustration's side only.
    if (left) delete g.decor['mid-right']; else delete g.decor['mid-left'];
    delete g.decor['bottom-left']; delete g.decor['bottom-right'];
    g.decor[left ? 'bottom-left' : 'bottom-right'] = { x: left ? M : W - M - illW, y: 1040, w: illW, align: left ? 'left' : 'right' };
  }
  return g;
}

const box = (r, extra = '') => `left:${r.x}px;top:${r.y}px;width:${r.w}px;${r.h ? `height:${r.h}px;` : ''}${extra}`;

function grainSvg(W, H) {
  return `<svg class="grain" xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>`;
}

function buildSlide(slide, spec, total, cfg, warnings) {
  const { width: W, height: H } = spec.canvas;
  const P = spec.palette;
  const g = geometry(slide.layout, slide.side, W, H);
  const n = String(slide.index).padStart(2, '0');
  const text = [];
  let art = '', illusSvg = null, timeline = [];

  // Illustration (art layer) + its labels (text layer).
  if (slide.illustration.type !== 'none' && g.illus) {
    const r = g.illus;
    const out = renderIllustration(slide.illustration.type, { w: r.w, h: r.h, palette: P, params: slide.illustration.params, labels: slide.illustration.labels });
    const inner = out.svg;
    illusSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${r.w} ${r.h}" width="${r.w}" height="${r.h}" id="s${n}-illus" data-type="${slide.illustration.type}"><defs></defs>${inner}</svg>`;
    art = `<div class="illus" style="${box(r)}" data-full-bleed="${r.fullBleed ? 1 : 0}">${illusSvg}</div>`;
    timeline = slide.illustration.animate ? out.timeline : [];
    for (const l of out.labels) {
      const tx = l.anchor === 'middle' ? '-50%' : l.anchor === 'end' ? '-100%' : '0';
      const ty = l.valign === 'middle' ? '-50%' : l.valign === 'bottom' ? '-100%' : '0';
      text.push(`<div class="tb ill-label" data-kind="label" style="left:${r.x + l.x}px;top:${r.y + l.y}px;transform:translate(${tx},${ty});font-size:${l.size}px;font-weight:${l.weight};color:var(--${l.color})">${esc(l.text)}</div>`);
    }
  }

  // Decorative equations (static texture) in fixed slots.
  for (const e of slide.equations.filter((x) => x.role === 'decor')) {
    const s = g.decor[e.slot];
    if (!s) { warnings.push(`slide ${slide.index}: decor slot ${e.slot} unavailable in ${slide.layout}/${slide.side} layout; equation omitted`); continue; }
    text.push(`<div class="tb decor ${s.align === 'right' ? 'right' : ''}" data-kind="equation" style="${box(s)}">${tex(e.tex, false)}</div>`);
  }

  // Headline (+ cover title block).
  if (slide.layout === 'cover') {
    if (slide.kicker) text.push(`<div class="tb kicker" data-kind="kicker" style="${box(g.kicker)}">${esc(slide.kicker)}</div>`);
    text.push(`<div class="tb headline fit-line" data-kind="headline" style="${box(g.headline)}text-align:left;font-size:150px;line-height:${g.headline.h}px">${esc(slide.headline)}</div>`);
    if (slide.subheadline) text.push(`<div class="tb subheadline" data-kind="subheadline" style="${box(g.subheadline)}text-align:right">${esc(slide.subheadline)}</div>`);
  } else {
    text.push(`<div class="tb headline fit-line" data-kind="headline" style="${box(g.headline)}line-height:${g.headline.h}px">${esc(slide.headline)}</div>`);
  }

  // Body column: label, paragraphs, hero equation. Font size shrinks at load if needed.
  if (g.column) {
    const hero = slide.equations.find((x) => x.role === 'hero');
    const parts = [];
    if (slide.label) parts.push(`<div class="label">${esc(slide.label)}</div>`);
    slide.body.forEach((p, i) => {
      parts.push(`<p>${esc(p)}</p>`);
      if (hero && i === 0 && slide.body.length > 1) parts.push(`<div class="hero">${tex(hero.tex, true)}</div>`);
    });
    if (hero && slide.body.length <= 1) parts.push(`<div class="hero">${tex(hero.tex, true)}</div>`);
    const align = slide.layout === 'closing' ? 'justify-content:flex-start;' : '';
    text.push(`<div class="tb column fit-col" data-kind="column" style="${box(g.column)}${align}">${parts.join('')}</div>`);
  } else if (slide.body.length || slide.label) {
    warnings.push(`slide ${slide.index}: ${slide.layout} layout has no body column; body/label omitted`);
  }

  if (g.cta && slide.cta) text.push(`<div class="tb cta" data-kind="cta" style="${box(g.cta)}">${esc(slide.cta)}</div>`);
  if (slide.footnote) text.push(`<div class="tb footnote" data-kind="footnote" style="left:${g.M}px;top:${H - 118}px;width:${W - 2 * g.M}px">${esc(slide.footnote)}</div>`);
  text.push(`<div class="tb footer" data-kind="footer" style="left:${g.M}px;top:${g.footer.y}px">${esc(spec.brand)}</div>`);
  text.push(`<div class="tb footer" data-kind="footer" style="right:${g.M}px;top:${g.footer.y}px">${n} / ${String(total).padStart(2, '0')}</div>`);

  const html = `<section class="slide" data-index="${slide.index}" data-layout="${slide.layout}">
  <div class="layer bg-layer"><div class="wash"></div>${grainSvg(W, H)}</div>
  <div class="layer art-layer">${art}</div>
  <div class="layer text-layer">${text.join('\n    ')}</div>
</section>`;
  return { html, illusSvg, timeline };
}

function buildCarousel(spec, outDir, cfg) {
  const warnings = [];
  const { width: W, height: H } = spec.canvas;
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(path.join(outDir, 'illustrations'), { recursive: true });
  vendorAssets(outDir);

  const total = spec.slides.length;
  const built = spec.slides.map((s) => ({ s, ...buildSlide(s, spec, total, cfg, warnings) }));
  const seconds = (s) => (s.layout === 'cover' ? cfg.render.coverSeconds : cfg.render.slideSeconds);
  const data = {
    topicId: spec.topicId,
    canvas: spec.canvas,
    fonts: ['800 100px "Inter Tight"', '700 100px "Inter Tight"', '700 30px "Inter"', '600 30px "Inter"', '500 30px "Inter"', '400 30px "KaTeX_Main"', 'italic 400 30px "KaTeX_Math"'],
    slides: built.map(({ s, timeline }) => ({ index: s.index, layout: s.layout, seconds: seconds(s), timeline })),
  };
  for (const { s, illusSvg } of built) {
    if (illusSvg) fs.writeFileSync(path.join(outDir, 'illustrations', `slide-${String(s.index).padStart(2, '0')}.svg`), illusSvg + '\n');
  }
  const vars = Object.entries(spec.palette).map(([k, v]) => `--${k}:${v};`).join('');
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${esc(spec.title)} — ${esc(spec.brand)}</title>
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/katex/katex.min.css">
<link rel="stylesheet" href="assets/styles.css">
<style>:root{--w:${W}px;--h:${H}px;${vars}} @page{size:${W}px ${H}px;margin:0}</style>
</head>
<body>
${built.map((b) => b.html).join('\n')}
<script>window.__CAROUSEL__ = ${JSON.stringify(data).replace(/</g, '\\u003c')};</script>
<script src="assets/gsap.min.js"></script>
<script src="assets/runtime.js"></script>
</body>
</html>
`;
  fs.writeFileSync(path.join(outDir, 'index.html'), html);
  fs.writeFileSync(path.join(outDir, 'slides.json'), JSON.stringify({ spec, timelines: data.slides }, null, 2) + '\n');
  return { indexHtml: path.join(outDir, 'index.html'), data, warnings };
}

module.exports = { buildCarousel, geometry };
