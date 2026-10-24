'use strict';
// Shared queue logic over a "table" backend exposing readTable() -> string[][] and
// writeCells([{row, col, value}]) (1-based row/col, header at cfg.headerRow).
const { sleep } = require('../util');

const MAX_ERROR_LOG = 1000;

class TableQueue {
  constructor(cfg, backend, log) {
    this.cfg = cfg;
    this.cols = cfg.queue.columns;
    this.statuses = cfg.queue.statuses;
    this.backend = backend;
    this.log = log;
    this.headerRow = backend.headerRow || 1;
  }

  async rows() {
    const table = await this.backend.readTable();
    const header = (table[this.headerRow - 1] || []).map((h) => String(h).trim());
    const index = {};
    for (const [field, name] of Object.entries(this.cols)) {
      const i = header.indexOf(name);
      if (i >= 0) index[field] = i;
    }
    for (const required of ['topicId', 'topic', 'status']) {
      if (index[required] === undefined) throw new Error(`Sheet is missing required column "${this.cols[required]}"`);
    }
    this.index = index;
    return table.slice(this.headerRow).map((cells, i) => {
      const fields = {};
      for (const [field, col] of Object.entries(index)) fields[field] = (cells[col] ?? '').toString().trim();
      return { rowNumber: this.headerRow + 1 + i, fields };
    }).filter((r) => r.fields.topicId || r.fields.topic);
  }

  async findByTopicId(topicId) {
    const matches = (await this.rows()).filter((r) => r.fields.topicId === topicId);
    if (matches.length > 1) throw new Error(`Duplicate Topic ID ${topicId} in rows ${matches.map((m) => m.rowNumber).join(', ')}`);
    return matches[0] || null;
  }

  // Write, then re-read and verify the written values before reporting success.
  async update(topicId, patch) {
    const row = await this.findByTopicId(topicId);
    if (!row) throw new Error(`Topic ${topicId} not found in queue`);
    const cells = [];
    for (const [field, value] of Object.entries(patch)) {
      if (this.index[field] === undefined) {
        this.log.warn('queue.column_missing', { field, column: this.cols[field] });
        continue;
      }
      let v = value == null ? '' : String(value);
      if (field === 'errorLog' && v.length > MAX_ERROR_LOG) v = v.slice(0, MAX_ERROR_LOG - 1) + '…';
      cells.push({ row: row.rowNumber, col: this.index[field] + 1, value: v, field });
    }
    if (!cells.length) return row;
    await this.backend.writeCells(cells);
    const after = await this.findByTopicId(topicId);
    for (const c of cells) {
      if (after.fields[c.field] !== c.value.trim()) throw new Error(`Queue write not verified for ${topicId}.${c.field}`);
    }
    this.log.info('queue.updated', { topicId, patch: Object.fromEntries(cells.map((c) => [c.field, c.value])) });
    return after;
  }

  // Claim = conditional write + read-back of the lock token. Sheets has no compare-and-swap,
  // so we re-read after a short delay; a concurrent claimer's token would overwrite ours.
  async claimNext(token, { topicId } = {}) {
    const rows = await this.rows();
    const eligible = rows.filter((r) => r.fields.status === this.statuses.ready && (!topicId || r.fields.topicId === topicId));
    for (const row of eligible) {
      const id = row.fields.topicId;
      const dupes = rows.filter((r) => r.fields.topicId === id);
      if (dupes.length > 1) { this.log.warn('queue.duplicate_topic_id', { topicId: id }); continue; }
      const patch = { status: this.statuses.processing, errorLog: '' };
      if (this.index.lockedBy !== undefined) patch.lockedBy = token;
      await this.update(id, patch);
      await sleep(this.backend.claimSettleMs ?? 1500);
      const check = await this.findByTopicId(id);
      if (this.index.lockedBy !== undefined && check.fields.lockedBy !== token) {
        this.log.warn('queue.claim_lost', { topicId: id });
        continue;
      }
      return check;
    }
    return null;
  }
}

function colLetter(n) {
  let s = '';
  while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

module.exports = { TableQueue, colLetter };
