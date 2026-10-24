'use strict';
// Local CSV queue with the same contract as the Google Sheet. Used for offline runs and tests.
const fs = require('fs');
const path = require('path');
const { parseCsv, serializeCsv } = require('./csv');

class LocalCsvBackend {
  constructor(file) {
    this.file = file;
    this.headerRow = 1;
    this.claimSettleMs = 0;
  }
  async readTable() {
    return parseCsv(fs.readFileSync(this.file, 'utf8'));
  }
  async writeCells(cells) {
    const table = await this.readTable();
    for (const { row, col, value } of cells) {
      while (table.length < row) table.push([]);
      const r = table[row - 1];
      while (r.length < col) r.push('');
      r[col - 1] = value;
    }
    const tmp = this.file + '.tmp';
    fs.writeFileSync(tmp, serializeCsv(table));
    fs.renameSync(tmp, this.file);
  }
}

module.exports = { LocalCsvBackend, resolveLocalFile: (cfg) => path.resolve(cfg.root, process.env.FACTORY_LOCAL_QUEUE || cfg.queue.local.file) };
