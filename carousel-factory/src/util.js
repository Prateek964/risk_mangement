'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function sha256File(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function writeJsonAtomic(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2) + '\n');
  fs.renameSync(tmp, file);
}

function readJson(file, fallback) {
  if (!fs.existsSync(file)) return fallback;
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

// Topic IDs come from the sheet: restrict to a safe filename alphabet.
function safeId(id) {
  const s = String(id || '').trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(s)) throw new Error(`Unsafe or empty Topic ID: ${JSON.stringify(s)}`);
  return s;
}

async function withRetry(fn, { attempts = 3, baseMs = 1000, log, label = 'op' } = {}) {
  let lastErr;
  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn(i);
    } catch (err) {
      lastErr = err;
      if (log) log.warn('retry', { label, attempt: i, error: err.message });
      if (i < attempts) await sleep(baseMs * 2 ** (i - 1));
    }
  }
  throw lastErr;
}

async function withTimeout(promise, ms, label) {
  let t;
  const timeout = new Promise((_, rej) => (t = setTimeout(() => rej(new Error(`${label} timed out after ${ms}ms`)), ms)));
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(t);
  }
}

// Magic-byte sniffing so a "mood board" is only accepted if it is a real image/PDF.
function sniffFile(file) {
  const buf = fs.readFileSync(file);
  const head = buf.subarray(0, 16);
  let type = 'unknown';
  let width, height;
  if (head[0] === 0x89 && head.toString('ascii', 1, 4) === 'PNG') {
    type = 'png';
    width = buf.readUInt32BE(16);
    height = buf.readUInt32BE(20);
  } else if (head[0] === 0xff && head[1] === 0xd8) {
    type = 'jpeg';
    for (let i = 2; i < buf.length - 9; ) {
      if (buf[i] !== 0xff) { i++; continue; }
      const marker = buf[i + 1];
      const len = buf.readUInt16BE(i + 2);
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        height = buf.readUInt16BE(i + 5);
        width = buf.readUInt16BE(i + 7);
        break;
      }
      i += 2 + len;
    }
  } else if (head.toString('ascii', 0, 4) === 'RIFF' && head.toString('ascii', 8, 12) === 'WEBP') {
    type = 'webp';
  } else if (head.toString('ascii', 0, 5) === '%PDF-') {
    type = 'pdf';
  }
  return { type, bytes: buf.length, width, height };
}

module.exports = { sleep, sha256File, writeJsonAtomic, readJson, safeId, withRetry, withTimeout, sniffFile };
