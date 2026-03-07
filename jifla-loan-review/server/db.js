// db.js - SQLite database setup and migrations
// NOTE: For production deployment, replace better-sqlite3 with @journeyapps/sqlcipher
// and set the encryption key from DB_ENCRYPTION_KEY env var for data-at-rest encryption.
// This is required by GLBA Safeguards Rule and Georgia data breach law.
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = process.env.DATABASE_PATH
  ? path.resolve(process.env.DATABASE_PATH)
  : path.join(__dirname, '../data/jifla.db');

// Ensure data directory exists
const dataDir = path.dirname(dbPath);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const db = new Database(dbPath);

// Enable WAL mode for better concurrent performance
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

function migrate() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now')),
      last_login TEXT
    );

    CREATE TABLE IF NOT EXISTS access_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      application_id INTEGER,
      action TEXT NOT NULL,
      accessed_at TEXT DEFAULT (datetime('now')),
      ip_address TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS loan_policies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      version INTEGER NOT NULL,
      uploaded_at TEXT DEFAULT (datetime('now')),
      filename TEXT NOT NULL,
      full_text TEXT NOT NULL,
      structured_fields TEXT DEFAULT '{}',
      is_active INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS applications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now')),
      closed_at TEXT,
      status TEXT DEFAULT 'Draft',

      -- Applicant Information
      applicant_name TEXT NOT NULL,
      address TEXT,
      phone TEXT,
      email TEXT,
      household_size INTEGER,
      employment_status TEXT,
      employer TEXT,
      monthly_income REAL,
      monthly_expenses_json TEXT DEFAULT '{}',
      existing_debts_json TEXT DEFAULT '[]',

      -- Loan Request
      loan_amount_requested REAL,
      loan_purpose_category TEXT,
      loan_purpose_description TEXT,
      repayment_term_months INTEGER,

      -- References / Guarantors
      references_json TEXT DEFAULT '[]',

      -- Staff Notes
      staff_notes TEXT,

      -- Privacy Notice Acknowledgment (GLBA required)
      privacy_notice_acknowledged INTEGER DEFAULT 0,
      privacy_notice_date TEXT,
      privacy_notice_method TEXT,

      -- Decision and Adverse Action (ECOA/FCRA)
      decision TEXT,
      decision_date TEXT,
      denial_reasons_json TEXT DEFAULT '[]',
      credit_report_used INTEGER DEFAULT 0,
      cra_name TEXT,
      cra_address TEXT,
      cra_phone TEXT,
      credit_score_used INTEGER DEFAULT 0,
      credit_score_value INTEGER,
      credit_score_range TEXT,
      credit_score_date TEXT,
      credit_score_key_factors_json TEXT DEFAULT '[]',
      adverse_action_notice_generated_at TEXT,
      adverse_action_notice_sent_at TEXT,
      adverse_action_notice_method TEXT
    );

    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      application_id INTEGER NOT NULL,
      uploaded_at TEXT DEFAULT (datetime('now')),
      filename TEXT NOT NULL,
      file_path TEXT NOT NULL,
      document_label TEXT,
      extracted_text TEXT,
      is_credit_report INTEGER DEFAULT 0,
      credit_summary_json TEXT,
      retention_category TEXT DEFAULT 'pii_documents',
      purged_at TEXT,
      FOREIGN KEY (application_id) REFERENCES applications(id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      application_id INTEGER NOT NULL,
      reviewed_at TEXT DEFAULT (datetime('now')),
      rule_check_results TEXT DEFAULT '[]',
      ai_review_text TEXT,
      ai_review_raw_response TEXT,
      memo_generated_at TEXT,
      FOREIGN KEY (application_id) REFERENCES applications(id)
    );

    CREATE TABLE IF NOT EXISTS memo_exports (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      review_id INTEGER NOT NULL,
      exported_at TEXT DEFAULT (datetime('now')),
      format TEXT,
      file_path TEXT,
      FOREIGN KEY (review_id) REFERENCES reviews(id)
    );

    CREATE TABLE IF NOT EXISTS api_call_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      application_id INTEGER,
      called_at TEXT DEFAULT (datetime('now')),
      payload_size_bytes INTEGER,
      payload_hash TEXT,
      model_used TEXT,
      response_status TEXT
    );

    CREATE TABLE IF NOT EXISTS purge_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      purged_at TEXT DEFAULT (datetime('now')),
      application_id INTEGER,
      data_type TEXT,
      records_affected INTEGER,
      initiated_by TEXT DEFAULT 'auto'
    );
  `);

  console.log('Database migrations complete.');
}

migrate();

export default db;
