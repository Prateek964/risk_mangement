'use strict';
// Google Sheets backend via the REST API and a service-account JWT (no SDK dependency).
// The key file path comes from GOOGLE_APPLICATION_CREDENTIALS; nothing secret is logged.
const fs = require('fs');
const crypto = require('crypto');
const { colLetter } = require('./base');
const { withRetry } = require('../util');

const SCOPE = 'https://www.googleapis.com/auth/spreadsheets';
const API = process.env.FACTORY_SHEETS_API_BASE || 'https://sheets.googleapis.com/v4/spreadsheets';

const b64url = (b) => Buffer.from(b).toString('base64').replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');

class SheetsBackend {
  constructor({ spreadsheetId, tab, headerRow = 1, credentialsFile, log }) {
    if (!spreadsheetId) throw new Error('Sheets adapter: spreadsheet ID is not set (FACTORY_SHEET_ID)');
    if (!credentialsFile || !fs.existsSync(credentialsFile)) {
      throw new Error('Sheets adapter: GOOGLE_APPLICATION_CREDENTIALS must point to a service-account JSON key file');
    }
    this.id = spreadsheetId;
    this.tab = tab;
    this.headerRow = headerRow;
    this.creds = JSON.parse(fs.readFileSync(credentialsFile, 'utf8'));
    this.log = log;
    this.token = null;
  }

  async accessToken() {
    if (this.token && this.token.exp - 60 > Date.now() / 1000) return this.token.value;
    const now = Math.floor(Date.now() / 1000);
    const header = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
    const claims = b64url(JSON.stringify({
      iss: this.creds.client_email, scope: SCOPE, aud: this.creds.token_uri || 'https://oauth2.googleapis.com/token', iat: now, exp: now + 3600,
    }));
    const sig = b64url(crypto.createSign('RSA-SHA256').update(`${header}.${claims}`).sign(this.creds.private_key));
    const res = await fetch(this.creds.token_uri || 'https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: `${header}.${claims}.${sig}` }),
    });
    if (!res.ok) throw new Error(`Google token exchange failed: HTTP ${res.status}`);
    const body = await res.json();
    this.token = { value: body.access_token, exp: now + (body.expires_in || 3600) };
    return this.token.value;
  }

  async call(url, init = {}) {
    return withRetry(async () => {
      const res = await fetch(url, { ...init, headers: { ...(init.headers || {}), authorization: `Bearer ${await this.accessToken()}` } });
      if (res.status === 429 || res.status >= 500) throw new Error(`Sheets API HTTP ${res.status}`);
      if (!res.ok) {
        const err = new Error(`Sheets API HTTP ${res.status}: ${(await res.text()).slice(0, 300)}`);
        err.fatal = true;
        throw err;
      }
      return res.json();
    }, { attempts: 4, baseMs: 1000, log: this.log, label: 'sheets' });
  }

  range(a1) {
    return `'${this.tab.replace(/'/g, "''")}'!${a1}`;
  }

  async readTable() {
    const url = `${API}/${encodeURIComponent(this.id)}/values/${encodeURIComponent(this.range('A1:ZZ'))}?majorDimension=ROWS&valueRenderOption=FORMATTED_VALUE`;
    const body = await this.call(url);
    return body.values || [];
  }

  async writeCells(cells) {
    // RAW input: values are stored as text, never evaluated as formulas.
    const data = cells.map(({ row, col, value }) => ({ range: this.range(`${colLetter(col)}${row}`), values: [[value]] }));
    await this.call(`${API}/${encodeURIComponent(this.id)}/values:batchUpdate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ valueInputOption: 'RAW', data }),
    });
  }
}

module.exports = { SheetsBackend };
