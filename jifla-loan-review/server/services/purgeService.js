// purgeService.js - Retention enforcement and secure deletion
// Implements FCRA disposal rule (16 CFR 682) and GLBA data lifecycle requirements.

import fs from 'fs';
import db from '../db.js';
import { secureDelete } from './fileEncryption.js';

const RETENTION_CREDIT_REPORTS = parseInt(process.env.RETENTION_CREDIT_REPORTS) || 90;
const RETENTION_PII_DOCUMENTS = parseInt(process.env.RETENTION_PII_DOCUMENTS) || 365;
const RETENTION_APPLICATION_RECORDS = parseInt(process.env.RETENTION_APPLICATION_RECORDS) || 1095;

export function runPurgeService(initiatedBy = 'auto') {
  console.log(`[PurgeService] Running retention check (initiated by: ${initiatedBy})`);

  let totalPurged = 0;

  try {
    totalPurged += purgeCreditReports(initiatedBy);
    totalPurged += purgePIIDocuments(initiatedBy);
    totalPurged += purgeApplicationRecords(initiatedBy);

    // Run VACUUM after purge to ensure deleted data doesn't remain in SQLite file
    if (totalPurged > 0) {
      db.exec('VACUUM');
      console.log(`[PurgeService] VACUUM complete after purging ${totalPurged} records.`);
    } else {
      console.log('[PurgeService] No records due for purging.');
    }
  } catch (err) {
    console.error('[PurgeService] Error during purge:', err.message);
  }

  return totalPurged;
}

function purgeCreditReports(initiatedBy) {
  // Credit reports: purge extracted text and source files 90 days after application closed
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - RETENTION_CREDIT_REPORTS);

  const expiredDocs = db.prepare(`
    SELECT d.id, d.file_path, d.application_id
    FROM documents d
    JOIN applications a ON d.application_id = a.id
    WHERE d.is_credit_report = 1
      AND d.purged_at IS NULL
      AND a.closed_at IS NOT NULL
      AND a.closed_at < ?
  `).all(cutoff.toISOString());

  let count = 0;
  for (const doc of expiredDocs) {
    // Secure delete the file
    if (doc.file_path && fs.existsSync(doc.file_path)) {
      secureDelete(doc.file_path);
    }

    // Null out text fields, mark as purged
    db.prepare(`
      UPDATE documents
      SET extracted_text = NULL, file_path = '', credit_summary_json = NULL, purged_at = datetime('now')
      WHERE id = ?
    `).run(doc.id);

    // Log purge (no PII in log)
    db.prepare(`
      INSERT INTO purge_log (application_id, data_type, records_affected, initiated_by)
      VALUES (?, 'credit_report', 1, ?)
    `).run(doc.application_id, initiatedBy);

    count++;
  }

  if (count > 0) console.log(`[PurgeService] Purged ${count} credit report(s) older than ${RETENTION_CREDIT_REPORTS} days.`);
  return count;
}

function purgePIIDocuments(initiatedBy) {
  // PII documents: delete source files 1 year after application closed
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - RETENTION_PII_DOCUMENTS);

  const expiredDocs = db.prepare(`
    SELECT d.id, d.file_path, d.application_id
    FROM documents d
    JOIN applications a ON d.application_id = a.id
    WHERE d.is_credit_report = 0
      AND d.retention_category = 'pii_documents'
      AND d.purged_at IS NULL
      AND a.closed_at IS NOT NULL
      AND a.closed_at < ?
  `).all(cutoff.toISOString());

  let count = 0;
  for (const doc of expiredDocs) {
    if (doc.file_path && fs.existsSync(doc.file_path)) {
      secureDelete(doc.file_path);
    }

    // Keep extracted text for audit trail, purge the file
    db.prepare(`
      UPDATE documents SET file_path = '', purged_at = datetime('now') WHERE id = ?
    `).run(doc.id);

    db.prepare(`
      INSERT INTO purge_log (application_id, data_type, records_affected, initiated_by)
      VALUES (?, 'pii_document_file', 1, ?)
    `).run(doc.application_id, initiatedBy);

    count++;
  }

  if (count > 0) console.log(`[PurgeService] Purged ${count} PII document file(s) older than ${RETENTION_PII_DOCUMENTS} days.`);
  return count;
}

function purgeApplicationRecords(initiatedBy) {
  // Application records: delete after 3 years
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - RETENTION_APPLICATION_RECORDS);

  const expiredApps = db.prepare(`
    SELECT id FROM applications
    WHERE closed_at IS NOT NULL AND closed_at < ?
  `).all(cutoff.toISOString());

  let count = 0;
  for (const app of expiredApps) {
    // Null out PII fields before delete
    db.prepare(`
      UPDATE applications SET
        applicant_name = '[PURGED]', address = NULL, phone = NULL, email = NULL,
        monthly_expenses_json = '{}', existing_debts_json = '[]',
        references_json = '[]', staff_notes = NULL,
        denial_reasons_json = '[]', cra_name = NULL, cra_address = NULL, cra_phone = NULL
      WHERE id = ?
    `).run(app.id);

    db.prepare(`
      INSERT INTO purge_log (application_id, data_type, records_affected, initiated_by)
      VALUES (?, 'application_record_pii', 1, ?)
    `).run(app.id, initiatedBy);

    count++;
  }

  if (count > 0) {
    db.exec('VACUUM');
    console.log(`[PurgeService] Purged PII from ${count} application record(s) older than ${RETENTION_APPLICATION_RECORDS} days.`);
  }
  return count;
}
