'use strict';
// Exports a built carousel: PNG per slide (final frame), vector PDF, MP4 (frame-by-frame via
// deterministic timeline seeks piped into FFmpeg), contact sheet, and a render config.
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');
const { serve } = require('./server');

async function openPage(browser, base, canvas, query) {
  const page = await browser.newPage({ viewport: { width: canvas.width, height: canvas.height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`${base}/index.html?${query}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
  const init = await page.evaluate(() => window.__initError || null);
  if (init) throw new Error(`Carousel runtime failed to initialise: ${init}`);
  return { page, errors };
}

function ffmpegEncoder(file, { fps, crf, codec, pixelFormat }) {
  const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', codec, '-preset', 'medium', '-crf', String(crf), '-pix_fmt', pixelFormat, '-r', String(fps), '-movflags', '+faststart', file];
  const proc = spawn('ffmpeg', args, { stdio: ['pipe', 'ignore', 'pipe'] });
  let stderr = '';
  proc.stderr.on('data', (d) => (stderr += d));
  const done = new Promise((resolve, reject) => proc.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}: ${stderr.slice(-500)}`)))));
  const write = (buf) => new Promise((resolve, reject) => (proc.stdin.write(buf, (e) => (e ? reject(e) : resolve())))) ;
  return { write, end: () => { proc.stdin.end(); return done; } };
}

async function exportCarousel({ carouselDir, exportsDir, data, cfg, log, only = ['png', 'pdf', 'mp4', 'contact'] }) {
  const { canvas } = data;
  fs.mkdirSync(path.join(exportsDir, 'png'), { recursive: true });
  const server = await serve(carouselDir);
  const browser = await chromium.launch();
  const result = { png: [], pdf: null, mp4: null, contact: null, pageErrors: [], segments: [] };
  try {
    // PNG: final frame of each slide.
    if (only.includes('png')) {
      for (const s of data.slides) {
        const { page, errors } = await openPage(browser, server.url, canvas, `slide=${s.index}&state=final`);
        await page.evaluate((i) => window.__seek(i, 'end'), s.index);
        const file = path.join(exportsDir, 'png', `slide-${String(s.index).padStart(2, '0')}.png`);
        await page.screenshot({ path: file, type: 'png' });
        result.png.push(file);
        result.pageErrors.push(...errors.map((e) => `slide ${s.index}: ${e}`));
        await page.close();
      }
      log.info('export.png', { count: result.png.length });
    }

    // PDF: all slides, final state, one page each, text kept as vector glyphs.
    if (only.includes('pdf')) {
      const { page } = await openPage(browser, server.url, canvas, 'all=1&state=final');
      result.pdf = path.join(exportsDir, 'carousel.pdf');
      await page.pdf({ path: result.pdf, width: `${canvas.width}px`, height: `${canvas.height}px`, printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true });
      await page.close();
      log.info('export.pdf', { file: path.basename(result.pdf) });
    }

    // MP4: clean cuts between slides; each slide's frames come from seeking its timeline.
    if (only.includes('mp4')) {
      const r = cfg.render;
      result.mp4 = path.join(exportsDir, 'carousel.mp4');
      const enc = ffmpegEncoder(result.mp4, { fps: r.fps, crf: r.crf, codec: r.videoCodec, pixelFormat: r.pixelFormat });
      let frameCursor = 0;
      for (const s of data.slides) {
        const { page } = await openPage(browser, server.url, canvas, `slide=${s.index}&state=start`);
        const duration = await page.evaluate((i) => window.__duration(i), s.index);
        const frames = Math.round(duration * r.fps);
        result.segments.push({ slide: s.index, startFrame: frameCursor, frames, seconds: frames / r.fps });
        for (let fr = 0; fr < frames; fr++) {
          // Last frame is the exact final state so the video and the PNG agree.
          await page.evaluate(([i, t]) => window.__seek(i, t), [s.index, fr === frames - 1 ? 'end' : fr / r.fps]);
          await enc.write(await page.screenshot({ type: 'png' }));
        }
        frameCursor += frames;
        await page.close();
        log.info('export.mp4.slide', { slide: s.index, frames });
      }
      await enc.end();
      log.info('export.mp4', { file: path.basename(result.mp4), frames: frameCursor });
    }

    // Contact sheet for quick review/approval.
    if (only.includes('contact') && result.png.length) {
      const cols = Math.min(4, result.png.length), thumbW = 360, thumbH = Math.round((thumbW * canvas.height) / canvas.width), gap = 16;
      const rows = Math.ceil(result.png.length / cols);
      const page = await browser.newPage({ viewport: { width: cols * thumbW + (cols + 1) * gap, height: rows * thumbH + (rows + 1) * gap } });
      const imgs = result.png.map((f) => `<img src="data:image/png;base64,${fs.readFileSync(f).toString('base64')}" style="width:${thumbW}px;height:${thumbH}px">`).join('');
      await page.setContent(`<body style="margin:0;background:#000;padding:${gap}px;display:grid;grid-template-columns:repeat(${cols},${thumbW}px);gap:${gap}px">${imgs}</body>`);
      result.contact = path.join(exportsDir, 'contact-sheet.png');
      await page.screenshot({ path: result.contact, fullPage: true });
      await page.close();
    }
  } finally {
    await browser.close();
    await server.close();
  }
  return result;
}

module.exports = { exportCarousel, openPage };
