'use strict';
// Automated QA for a rendered carousel. Errors fail the job; warnings are reported.
const fs = require('fs');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const { serve } = require('../render/server');
const { openPage } = require('../render/export');
const { sniffFile } = require('../util');

const norm = (s) => String(s).replace(/\s+/g, ' ').replace(/­/g, '').trim();
const intersects = (a, b, pad = 0) => a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;
const clipOf = (r, W, H) => {
  const x = Math.max(0, Math.floor(r.x) - 1), y = Math.max(0, Math.floor(r.y) - 1);
  return { x, y, width: Math.min(W, Math.ceil(r.x + r.w) + 1) - x, height: Math.min(H, Math.ceil(r.y + r.h) + 1) - y };
};

function rawFrame(args, W, H) {
  const out = execFileSync('ffmpeg', ['-loglevel', 'error', ...args, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', `${W}x${H}`, '-'], { maxBuffer: W * H * 3 + 1024 });
  if (out.length !== W * H * 3) throw new Error(`unexpected raw frame size ${out.length}`);
  return out;
}
const meanAbsDiff = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += Math.abs(a[i] - b[i]); return s / a.length; };

function pdfInfo(file) {
  const py = spawnSync('python3', ['-I', '-c', 'import sys,json\nfrom pypdf import PdfReader\nr=PdfReader(sys.argv[1])\nprint(json.dumps({"pages":len(r.pages),"w":float(r.pages[0].mediabox.width),"h":float(r.pages[0].mediabox.height),"text":r.pages[0].extract_text()[:200]}))', file], { encoding: 'utf8' });
  if (py.status === 0) return { ...JSON.parse(py.stdout), method: 'pypdf' };
  const s = fs.readFileSync(file, 'latin1');
  const pages = (s.match(/\/Type\s*\/Page(?!s)/g) || []).length;
  const mb = s.match(/\/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]/);
  return { pages, w: mb ? +mb[1] : null, h: mb ? +mb[2] : null, method: 'regex' };
}

function spellcheck(words, allow) {
  const py = spawnSync('python3', ['-I', '-c', 'import sys,json\nfrom spellchecker import SpellChecker\nw=json.loads(sys.stdin.read())\nprint(json.dumps(sorted(SpellChecker().unknown(w))))'], { input: JSON.stringify(words), encoding: 'utf8' });
  if (py.status !== 0) return { ran: false, unknown: [] };
  return { ran: true, unknown: JSON.parse(py.stdout).filter((w) => !allow.has(w.toLowerCase())) };
}

const DOMAIN_WORDS = new Set(['var', 'vars', 'p&l', 'p&ls', 'pnl', 'frtb', 'basel', 'gbm', 'covariance', 'quantile', 'quantiles', 'backtest', 'backtesting', 'non-linear', 'variance–covariance', 'variance-covariance', 'cut-off', 'ito', 'itô', 'sigma', 'monte', 'carlo', 'shortfall', 'z-score', 'risk', 'hub', 'equal-ish', '√time', '1-day', '10-day', 'σ', 'μ']);

async function runQa({ job, spec, data, carouselDir, exportsDir, exportResult, cfg, log }) {
  const W = spec.canvas.width, H = spec.canvas.height;
  const checks = [];
  const add = (category, name, ok, detail = {}, severity = 'error') => checks.push({ category, name, ok: !!ok, severity: ok ? 'pass' : severity, ...detail });

  // ---------- FILES ----------
  for (const s of data.slides) {
    const f = path.join(exportsDir, 'png', `slide-${String(s.index).padStart(2, '0')}.png`);
    const info = fs.existsSync(f) ? sniffFile(f) : null;
    add('files', `png slide ${s.index}`, info && info.type === 'png' && info.width === W && info.height === H, { file: path.relative(job.dir, f), width: info && info.width, height: info && info.height });
  }
  const pdfFile = path.join(exportsDir, 'carousel.pdf');
  if (fs.existsSync(pdfFile)) {
    const info = pdfInfo(pdfFile);
    const ratioOk = info.w && Math.abs(info.w / info.h - W / H) < 0.01;
    add('files', 'pdf opens with one page per slide', info.pages === data.slides.length && ratioOk, { pages: info.pages, mediabox: [info.w, info.h], method: info.method });
  } else add('files', 'pdf exists', false);

  const mp4File = path.join(exportsDir, 'carousel.mp4');
  let probe = null;
  if (fs.existsSync(mp4File)) {
    probe = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames,pix_fmt:format=duration', '-of', 'json', mp4File], { encoding: 'utf8' }));
    const st = probe.streams[0];
    const expectFrames = exportResult.segments.reduce((a, s) => a + s.frames, 0);
    add('files', 'mp4 is H.264 at configured fps and size', st.codec_name === 'h264' && st.width === W && st.height === H && st.r_frame_rate === `${cfg.render.fps}/1` && st.pix_fmt === 'yuv420p',
      { codec: st.codec_name, size: `${st.width}x${st.height}`, fps: st.r_frame_rate, pix_fmt: st.pix_fmt });
    add('files', 'mp4 frame count matches timeline', Number(st.nb_read_frames) === expectFrames, { frames: Number(st.nb_read_frames), expected: expectFrames, duration: Number(probe.format.duration) });
  } else add('files', 'mp4 exists', false);
  for (const rel of ['index.html', 'slides.json', 'assets/runtime.js', 'assets/styles.css']) add('files', `source ${rel}`, fs.existsSync(path.join(carouselDir, rel)));
  for (const s of spec.slides.filter((x) => x.illustration.type !== 'none')) {
    add('files', `svg source slide ${s.index}`, fs.existsSync(path.join(carouselDir, 'illustrations', `slide-${String(s.index).padStart(2, '0')}.svg`)));
  }

  // ---------- BROWSER CHECKS ----------
  const server = await serve(carouselDir);
  const browser = await chromium.launch();
  const margin = cfg.qa.safeMargin;
  const words = new Set();
  try {
    for (const slide of spec.slides) {
      const i = slide.index;
      const { page, errors } = await openPage(browser, server.url, spec.canvas, `slide=${i}&state=start`);
      const meta = await page.evaluate(() => ({ guard: window.__guardErrors, fit: window.__fitErrors, fonts: window.__fonts }));
      add('animation', `slide ${i}: animation guard (no text targets)`, meta.guard.length === 0, { problems: meta.guard });
      add('design', `slide ${i}: text fits its regions`, meta.fit.length === 0, { problems: meta.fit });
      add('design', `slide ${i}: no runtime errors`, errors.length === 0, { errors });
      if (i === 1) {
        const need = ['Inter:700', 'Inter Tight:800'];
        if (spec.slides.some((s) => s.equations.length)) need.push('KaTeX_Main:400');
        const missing = need.filter((n) => !meta.fonts.includes(n));
        add('design', 'fonts loaded (Inter, Inter Tight, KaTeX)', missing.length === 0, { missing, loaded: [...new Set(meta.fonts)].sort() });
      }

      // Layout at final state.
      await page.evaluate((i) => window.__seek(i, 'end'), i);
      const rep = await page.evaluate((i) => window.__layoutReport(i), i);
      const outside = rep.blocks.filter((b) => b.rect.x < margin - 1 || b.rect.y < margin - 1 || b.rect.x + b.rect.w > W - margin + 1 || b.rect.y + b.rect.h > H - margin + 1);
      add('design', `slide ${i}: text inside safe margins (${margin}px)`, outside.length === 0, { outside: outside.map((b) => ({ kind: b.kind, text: b.text, rect: b.rect })) });
      const overlaps = [];
      for (let a = 0; a < rep.blocks.length; a++) for (let b = a + 1; b < rep.blocks.length; b++) {
        if (intersects(rep.blocks[a].rect, rep.blocks[b].rect)) overlaps.push([rep.blocks[a].text, rep.blocks[b].text]);
      }
      add('design', `slide ${i}: no text-on-text overlap`, overlaps.length === 0, { overlaps });
      if (rep.illustration) {
        const hits = rep.blocks.filter((b) => b.kind !== 'label' && intersects(b.rect, rep.illustration));
        add('design', `slide ${i}: body text clear of illustration region`, hits.length === 0, { hits: hits.map((b) => b.text) });
      }

      // Content preservation.
      const domText = norm(rep.innerText);
      const expected = [slide.headline, slide.kicker, slide.subheadline, slide.label, ...slide.body, slide.cta, slide.footnote, ...slide.illustration.labels].filter(Boolean);
      const missing = expected.filter((t) => !domText.includes(norm(t)));
      add('content', `slide ${i}: all slide text present`, missing.length === 0, { missing });
      add('content', `slide ${i}: equations rendered (${slide.equations.length})`, rep.katexErrors === 0 && rep.katexCount >= slide.equations.length, { katex: rep.katexCount, errors: rep.katexErrors });
      expected.join(' ').split(/[^A-Za-z&'’\-–√σμ0-9]+/).forEach((w) => { if (w && !/\d/.test(w) && !/^[A-Z&]{2,}$/.test(w)) words.add(w.toLowerCase().replace(/^['’]|['’]s?$/g, '')); });

      // STATIC TEXT: DOM snapshot + pixel-identical text regions across sampled frames.
      const duration = await page.evaluate((i) => window.__duration(i), i);
      const times = cfg.qa.sampleFractions.map((fr) => +(fr * duration).toFixed(4));
      await page.evaluate((i) => window.__seek(i, 0), i);
      const snap0 = await page.evaluate((i) => window.__textSnapshot(i), i);
      const rects = rep.blocks.map((b) => clipOf(b.rect, W, H));
      const shots0 = [];
      for (const c of rects) shots0.push(await page.screenshot({ clip: c, type: 'png' }));
      const illusClip = rep.illustration ? clipOf(rep.illustration, W, H) : null;
      const illus0 = illusClip ? await page.screenshot({ clip: illusClip, type: 'png' }) : null;
      const domDiffs = [], pixelDiffs = [];
      let illusChanged = false;
      for (const t of times.slice(1)) {
        await page.evaluate(([i, t]) => window.__seek(i, t), [i, t]);
        const snap = await page.evaluate((i) => window.__textSnapshot(i), i);
        if (JSON.stringify(snap) !== JSON.stringify(snap0)) {
          const changed = snap.filter((s, k) => JSON.stringify(s) !== JSON.stringify(snap0[k])).map((s) => s.text);
          domDiffs.push({ t, changed: changed.slice(0, 5), countBefore: snap0.length, countAfter: snap.length });
        }
        for (let k = 0; k < rects.length; k++) {
          const buf = await page.screenshot({ clip: rects[k], type: 'png' });
          if (!buf.equals(shots0[k])) pixelDiffs.push({ t, block: rep.blocks[k].text });
        }
        if (illusClip && !illusChanged) illusChanged = !(await page.screenshot({ clip: illusClip, type: 'png' })).equals(illus0);
      }
      add('animation', `slide ${i}: text DOM identical at ${times.length} sampled times`, domDiffs.length === 0, { times, diffs: domDiffs });
      add('animation', `slide ${i}: text pixels identical at sampled times (nothing animates over text)`, pixelDiffs.length === 0, { diffs: pixelDiffs.slice(0, 10) });
      if (slide.illustration.animate) add('animation', `slide ${i}: illustration animates`, illusChanged, { duration });

      // Determinism: a fresh page seeked to the same time renders identical pixels.
      const tMid = +(duration * 0.4).toFixed(4);
      await page.evaluate(([i, t]) => window.__seek(i, t), [i, tMid]);
      const a = await page.screenshot({ type: 'png' });
      const { page: page2 } = await openPage(browser, server.url, spec.canvas, `slide=${i}&state=start`);
      await page2.evaluate(([i, t]) => window.__seek(i, t), [i, tMid]);
      const b = await page2.screenshot({ type: 'png' });
      add('animation', `slide ${i}: timeline deterministic (fresh render at t=${tMid}s identical)`, a.equals(b));
      await page2.close();
      await page.close();
    }
  } finally {
    await browser.close();
    await server.close();
  }

  // MP4 sequence: the last frame of each segment must match that slide's PNG.
  if (probe) {
    for (const seg of exportResult.segments) {
      const t = (seg.startFrame + seg.frames - 1) / cfg.render.fps;
      const vid = rawFrame(['-i', mp4File, '-vf', `select=eq(n\\,${seg.startFrame + seg.frames - 1})`, '-vsync', '0'], W, H);
      const png = rawFrame(['-i', path.join(exportsDir, 'png', `slide-${String(seg.slide).padStart(2, '0')}.png`)], W, H);
      const d = meanAbsDiff(vid, png);
      add('animation', `mp4 slide ${seg.slide} final frame matches PNG`, d <= cfg.qa.maxVideoFrameDiff, { meanAbsDiff: +d.toFixed(3), at: +t.toFixed(3) });
    }
  }

  // Spelling (warning only; needs pyspellchecker).
  const sp = spellcheck([...words], DOMAIN_WORDS);
  if (sp.ran) add('content', 'spelling (dictionary check)', sp.unknown.length === 0, { unknown: sp.unknown }, 'warning');
  else add('content', 'spelling (dictionary check)', false, { note: 'pyspellchecker not installed; spelling not machine-checked' }, 'warning');

  const failed = checks.filter((c) => !c.ok && c.severity === 'error');
  const warned = checks.filter((c) => !c.ok && c.severity === 'warning');
  const report = { topicId: job.topicId, at: new Date().toISOString(), passed: failed.length === 0, totals: { checks: checks.length, failed: failed.length, warnings: warned.length }, checks };
  log.info('qa.done', report.totals);
  return report;
}

module.exports = { runQa };
