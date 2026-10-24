'use strict';
const fs = require('fs');
const path = require('path');

const SECRET_KEY = /(token|secret|password|cookie|authorization|private_?key|api_?key|credential)/i;
const SECRET_VALUE = [
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /\bya29\.[\w.-]+/g, // Google OAuth access tokens
  /\bsk-[A-Za-z0-9_-]{16,}/g,
  /\beyJ[\w-]+\.[\w-]+\.[\w-]+/g, // JWTs
];

function redact(value, key = '') {
  if (value == null) return value;
  if (key && SECRET_KEY.test(key)) return '[REDACTED]';
  if (typeof value === 'string') return SECRET_VALUE.reduce((s, re) => s.replace(re, '[REDACTED]'), value);
  if (Array.isArray(value)) return value.map((v) => redact(v));
  if (typeof value === 'object') {
    if (value instanceof Error) return { name: value.name, message: redact(value.message), stack: redact(value.stack) };
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, redact(v, k)]));
  }
  return value;
}

// Structured JSONL logger. Every record carries the topic ID when known.
function createLogger({ files = [], topicId = null, echo = true } = {}) {
  for (const f of files) fs.mkdirSync(path.dirname(f), { recursive: true });
  const write = (level, event, data = {}) => {
    const rec = redact({ ts: new Date().toISOString(), level, topicId, event, ...data });
    const line = JSON.stringify(rec);
    for (const f of files) fs.appendFileSync(f, line + '\n');
    if (echo) {
      const extra = Object.keys(data).length ? ' ' + JSON.stringify(redact(data)) : '';
      (level === 'error' ? console.error : console.log)(`[${level}]${topicId ? ' ' + topicId : ''} ${event}${extra}`);
    }
  };
  return {
    info: (e, d) => write('info', e, d),
    warn: (e, d) => write('warn', e, d),
    error: (e, d) => write('error', e, d),
    child: (extra) => createLogger({ files: [...files, ...(extra.files || [])], topicId: extra.topicId ?? topicId, echo }),
  };
}

module.exports = { createLogger, redact };
