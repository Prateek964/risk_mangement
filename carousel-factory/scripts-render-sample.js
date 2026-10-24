'use strict';
// Renders one design spec to output/jobs/<topicId>/: carousel source, PNG/PDF/MP4 exports, QA report.
// Usage: node scripts-render-sample.js moodboards/claude/VAR-001/design-spec.json
const fs = require('fs');
const path = require('path');
const { validateSpec } = require('./src/spec');
const { loadConfig } = require('./src/config');
const { createLogger } = require('./src/log');
const { buildCarousel } = require('./src/render/build');
const { exportCarousel } = require('./src/render/export');
const { runQa } = require('./src/qa');
const { safeId, writeJsonAtomic } = require('./src/util');

(async () => {
  const cfg = loadConfig();
  const raw = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const topicId = safeId(raw.topicId);
  const dir = path.join(cfg.jobsDir, topicId);
  const log = createLogger({ files: [path.join(dir, 'logs', 'render.jsonl')], topicId });
  const v = validateSpec(raw, { slideCount: raw.slides.length });
  if (!v.ok) throw new Error(`Spec invalid: ${v.errors.join('; ')}`);
  fs.mkdirSync(dir, { recursive: true });
  fs.copyFileSync(process.argv[2], path.join(dir, 'design-spec.json'));
  const b = buildCarousel(v.spec, path.join(dir, 'carousel'), cfg);
  const exportsDir = path.join(dir, 'exports');
  fs.rmSync(exportsDir, { recursive: true, force: true });
  const ex = await exportCarousel({ carouselDir: path.join(dir, 'carousel'), exportsDir, data: b.data, cfg, log });
  writeJsonAtomic(path.join(dir, 'carousel', 'render-config.json'), { fps: cfg.render.fps, codec: cfg.render.videoCodec, crf: cfg.render.crf, canvas: v.spec.canvas, segments: ex.segments, node: process.version, playwright: require('playwright/package.json').version });
  const rep = await runQa({ job: { dir, topicId }, spec: v.spec, data: b.data, carouselDir: path.join(dir, 'carousel'), exportsDir, exportResult: ex, cfg, log });
  writeJsonAtomic(path.join(dir, 'qa', 'report.json'), rep);
  for (const c of rep.checks.filter((c) => !c.ok)) log.warn('qa.issue', c);
  console.log(JSON.stringify(rep.totals));
  process.exit(rep.passed ? 0 : 2);
})().catch((e) => { console.error(e); process.exit(1); });
