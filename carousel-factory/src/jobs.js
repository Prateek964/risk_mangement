'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { sha256File, writeJsonAtomic, readJson, safeId } = require('./util');

const STAGES = ['claim', 'moodboard', 'transfer', 'approval', 'build', 'render', 'qa', 'publish'];

class Job {
  constructor(cfg, topicId) {
    this.cfg = cfg;
    this.topicId = safeId(topicId);
    this.dir = path.join(cfg.jobsDir, this.topicId);
    this.file = path.join(this.dir, 'job.json');
    this.state = readJson(this.file, null) || {
      topicId: this.topicId,
      createdAt: new Date().toISOString(),
      row: null,
      stages: {},
      history: [],
    };
  }

  path(...p) {
    return path.join(this.dir, ...p);
  }

  rel(abs) {
    return path.relative(this.dir, abs).split(path.sep).join('/');
  }

  save() {
    this.state.updatedAt = new Date().toISOString();
    writeJsonAtomic(this.file, this.state);
  }

  // A stage counts as done only if every artifact it recorded still hashes the same.
  isDone(stage) {
    const s = this.state.stages[stage];
    if (!s || s.status !== 'done') return false;
    for (const [rel, hash] of Object.entries(s.artifacts || {})) {
      const abs = this.path(rel);
      if (!fs.existsSync(abs) || sha256File(abs) !== hash) return false;
    }
    return true;
  }

  complete(stage, { artifacts = [], details = {} } = {}) {
    if (!STAGES.includes(stage)) throw new Error(`Unknown stage ${stage}`);
    const hashed = {};
    for (const a of artifacts) {
      const abs = path.isAbsolute(a) ? a : this.path(a);
      if (!fs.existsSync(abs)) throw new Error(`Cannot complete ${stage}: missing artifact ${a}`);
      hashed[this.rel(abs)] = sha256File(abs);
    }
    this.state.stages[stage] = { status: 'done', at: new Date().toISOString(), artifacts: hashed, details };
    this.state.history.push({ at: new Date().toISOString(), stage, status: 'done' });
    this.save();
  }

  fail(stage, error, details = {}) {
    const prev = this.state.stages[stage] || {};
    this.state.stages[stage] = {
      status: 'failed',
      at: new Date().toISOString(),
      attempts: (prev.attempts || 0) + 1,
      error: String(error && error.message ? error.message : error),
      details,
    };
    this.state.history.push({ at: new Date().toISOString(), stage, status: 'failed', error: this.state.stages[stage].error });
    this.save();
  }

  // Invalidate a stage and every stage after it (e.g. after a mood-board revision).
  reset(fromStage) {
    const i = STAGES.indexOf(fromStage);
    for (const s of STAGES.slice(i)) delete this.state.stages[s];
    this.state.history.push({ at: new Date().toISOString(), stage: fromStage, status: 'reset' });
    this.save();
  }

  nextStage() {
    return STAGES.find((s) => !this.isDone(s)) || null;
  }
}

// Exclusive file lock (O_EXCL). Stale locks from dead local processes are reclaimed.
function acquireLock(cfg, name) {
  const dir = path.join(cfg.outputDir, 'locks');
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${name}.lock`);
  const token = `${os.hostname()}:${process.pid}:${Date.now()}`;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const fd = fs.openSync(file, 'wx');
      fs.writeSync(fd, JSON.stringify({ token, host: os.hostname(), pid: process.pid, at: new Date().toISOString() }));
      fs.closeSync(fd);
      return { token, release: () => { try { if (JSON.parse(fs.readFileSync(file, 'utf8')).token === token) fs.unlinkSync(file); } catch {} } };
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
      const held = readJson(file, {});
      let alive = held.host !== os.hostname();
      if (!alive) { try { process.kill(held.pid, 0); alive = true; } catch {} }
      if (alive) return null;
      fs.unlinkSync(file); // stale
    }
  }
  return null;
}

module.exports = { Job, STAGES, acquireLock };
