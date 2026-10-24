'use strict';
const { TableQueue } = require('./base');
const { LocalCsvBackend, resolveLocalFile } = require('./local');
const { SheetsBackend } = require('./sheets');

function createQueue(cfg, log) {
  const q = cfg.queue;
  if (q.adapter === 'local') return new TableQueue(cfg, new LocalCsvBackend(resolveLocalFile(cfg)), log);
  if (q.adapter === 'sheets') {
    return new TableQueue(cfg, new SheetsBackend({
      spreadsheetId: process.env[q.sheets.spreadsheetIdEnv],
      tab: q.sheets.tab,
      headerRow: q.sheets.headerRow,
      credentialsFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
      log,
    }), log);
  }
  throw new Error(`Unknown queue adapter ${q.adapter}`);
}

module.exports = { createQueue };
