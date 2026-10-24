'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// Minimal .env loader: KEY=VALUE lines, no interpolation. Existing env wins.
function loadEnv(file = path.join(ROOT, '.env')) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (!m || process.env[m[1]] !== undefined) continue;
    process.env[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
}

function loadConfig(file = process.env.FACTORY_CONFIG || path.join(ROOT, 'config', 'factory.config.json')) {
  loadEnv();
  const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
  cfg.root = ROOT;
  cfg.outputDir = path.resolve(ROOT, process.env.FACTORY_OUTPUT_DIR || 'output');
  cfg.jobsDir = path.join(cfg.outputDir, 'jobs');
  if (process.env.FACTORY_QUEUE_ADAPTER) cfg.queue.adapter = process.env.FACTORY_QUEUE_ADAPTER;
  if (process.env.FACTORY_APPROVAL_MODE) cfg.approval.mode = process.env.FACTORY_APPROVAL_MODE;
  return cfg;
}

// "4:5" -> {width,height}; long edge of portrait kept at 1350 so the default stays 1080x1350.
function dimensionsFor(aspectRatio, defaults) {
  const m = String(aspectRatio || defaults.aspectRatio).match(/^\s*(\d+(?:\.\d+)?)\s*[:x/]\s*(\d+(?:\.\d+)?)\s*$/);
  if (!m) return { width: defaults.width, height: defaults.height, aspectRatio: defaults.aspectRatio };
  const [w, h] = [Number(m[1]), Number(m[2])];
  if (w === 4 && h === 5) return { width: 1080, height: 1350, aspectRatio: '4:5' };
  const width = 1080;
  const height = Math.round((width * h) / w / 2) * 2; // even for H.264
  return { width, height, aspectRatio: `${w}:${h}` };
}

module.exports = { ROOT, loadConfig, dimensionsFor };
