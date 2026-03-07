// applications.js - CRUD for loan applications
import express from 'express';
import db from '../db.js';

const router = express.Router();

// List all applications
router.get('/', (req, res) => {
  const apps = db.prepare(`
    SELECT
      a.id, a.created_at, a.updated_at, a.status,
      a.applicant_name, a.loan_amount_requested, a.loan_purpose_category,
      a.decision, a.decision_date,
      (SELECT COUNT(*) FROM reviews r WHERE r.application_id = a.id) as review_count,
      (SELECT r.reviewed_at FROM reviews r WHERE r.application_id = a.id ORDER BY r.reviewed_at DESC LIMIT 1) as last_reviewed_at
    FROM applications a
    ORDER BY a.created_at DESC
  `).all();
  return res.json(apps);
});

// Get single application
router.get('/:id', (req, res) => {
  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(req.params.id);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  // Parse JSON fields
  app.monthly_expenses_json = JSON.parse(app.monthly_expenses_json || '{}');
  app.existing_debts_json = JSON.parse(app.existing_debts_json || '[]');
  app.references_json = JSON.parse(app.references_json || '[]');
  app.denial_reasons_json = JSON.parse(app.denial_reasons_json || '[]');
  app.credit_score_key_factors_json = JSON.parse(app.credit_score_key_factors_json || '[]');

  // Get associated documents
  const documents = db.prepare(`
    SELECT id, uploaded_at, filename, document_label, is_credit_report, credit_summary_json, purged_at
    FROM documents WHERE application_id = ? AND purged_at IS NULL
  `).all(req.params.id);

  app.documents = documents.map(d => ({
    ...d,
    credit_summary_json: d.credit_summary_json ? JSON.parse(d.credit_summary_json) : null
  }));

  // Get latest review
  const review = db.prepare(`
    SELECT id, reviewed_at, rule_check_results, ai_review_text, memo_generated_at
    FROM reviews WHERE application_id = ? ORDER BY reviewed_at DESC LIMIT 1
  `).get(req.params.id);

  if (review) {
    review.rule_check_results = JSON.parse(review.rule_check_results || '[]');
    app.latest_review = review;
  }

  return res.json(app);
});

// Create new application
router.post('/', (req, res) => {
  const {
    applicant_name, address, phone, email,
    household_size, employment_status, employer,
    monthly_income, monthly_expenses_json, existing_debts_json,
    loan_amount_requested, loan_purpose_category, loan_purpose_description,
    repayment_term_months, references_json, staff_notes,
    privacy_notice_acknowledged, privacy_notice_date, privacy_notice_method
  } = req.body;

  if (!applicant_name) return res.status(400).json({ error: 'Applicant name is required' });

  const result = db.prepare(`
    INSERT INTO applications (
      applicant_name, address, phone, email,
      household_size, employment_status, employer,
      monthly_income, monthly_expenses_json, existing_debts_json,
      loan_amount_requested, loan_purpose_category, loan_purpose_description,
      repayment_term_months, references_json, staff_notes,
      privacy_notice_acknowledged, privacy_notice_date, privacy_notice_method,
      status
    ) VALUES (
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft'
    )
  `).run(
    applicant_name, address, phone, email,
    household_size, employment_status, employer,
    monthly_income,
    JSON.stringify(monthly_expenses_json || {}),
    JSON.stringify(existing_debts_json || []),
    loan_amount_requested, loan_purpose_category, loan_purpose_description,
    repayment_term_months,
    JSON.stringify(references_json || []),
    staff_notes,
    privacy_notice_acknowledged ? 1 : 0,
    privacy_notice_date, privacy_notice_method
  );

  return res.json({ success: true, id: result.lastInsertRowid });
});

// Update application
router.put('/:id', (req, res) => {
  const existing = db.prepare('SELECT id, status FROM applications WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Application not found' });

  const {
    applicant_name, address, phone, email,
    household_size, employment_status, employer,
    monthly_income, monthly_expenses_json, existing_debts_json,
    loan_amount_requested, loan_purpose_category, loan_purpose_description,
    repayment_term_months, references_json, staff_notes,
    privacy_notice_acknowledged, privacy_notice_date, privacy_notice_method,
    status
  } = req.body;

  db.prepare(`
    UPDATE applications SET
      applicant_name = COALESCE(?, applicant_name),
      address = COALESCE(?, address),
      phone = COALESCE(?, phone),
      email = COALESCE(?, email),
      household_size = COALESCE(?, household_size),
      employment_status = COALESCE(?, employment_status),
      employer = COALESCE(?, employer),
      monthly_income = COALESCE(?, monthly_income),
      monthly_expenses_json = COALESCE(?, monthly_expenses_json),
      existing_debts_json = COALESCE(?, existing_debts_json),
      loan_amount_requested = COALESCE(?, loan_amount_requested),
      loan_purpose_category = COALESCE(?, loan_purpose_category),
      loan_purpose_description = COALESCE(?, loan_purpose_description),
      repayment_term_months = COALESCE(?, repayment_term_months),
      references_json = COALESCE(?, references_json),
      staff_notes = COALESCE(?, staff_notes),
      privacy_notice_acknowledged = COALESCE(?, privacy_notice_acknowledged),
      privacy_notice_date = COALESCE(?, privacy_notice_date),
      privacy_notice_method = COALESCE(?, privacy_notice_method),
      status = COALESCE(?, status),
      updated_at = datetime('now')
    WHERE id = ?
  `).run(
    applicant_name, address, phone, email,
    household_size, employment_status, employer,
    monthly_income,
    monthly_expenses_json ? JSON.stringify(monthly_expenses_json) : null,
    existing_debts_json ? JSON.stringify(existing_debts_json) : null,
    loan_amount_requested, loan_purpose_category, loan_purpose_description,
    repayment_term_months,
    references_json ? JSON.stringify(references_json) : null,
    staff_notes,
    privacy_notice_acknowledged !== undefined ? (privacy_notice_acknowledged ? 1 : 0) : null,
    privacy_notice_date, privacy_notice_method,
    status,
    req.params.id
  );

  return res.json({ success: true });
});

// Record decision (Approve, Deny, Withdraw, Counteroffer)
router.post('/:id/decision', (req, res) => {
  const existing = db.prepare('SELECT id FROM applications WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Application not found' });

  const {
    decision, denial_reasons_json,
    credit_report_used, cra_name, cra_address, cra_phone,
    credit_score_used, credit_score_value, credit_score_range,
    credit_score_date, credit_score_key_factors_json
  } = req.body;

  if (!['Approved', 'Denied', 'Withdrawn', 'Counteroffer'].includes(decision)) {
    return res.status(400).json({ error: 'Invalid decision value' });
  }

  db.prepare(`
    UPDATE applications SET
      decision = ?,
      decision_date = datetime('now'),
      denial_reasons_json = ?,
      credit_report_used = ?,
      cra_name = ?,
      cra_address = ?,
      cra_phone = ?,
      credit_score_used = ?,
      credit_score_value = ?,
      credit_score_range = ?,
      credit_score_date = ?,
      credit_score_key_factors_json = ?,
      status = ?,
      closed_at = datetime('now'),
      updated_at = datetime('now')
    WHERE id = ?
  `).run(
    decision,
    JSON.stringify(denial_reasons_json || []),
    credit_report_used ? 1 : 0,
    cra_name, cra_address, cra_phone,
    credit_score_used ? 1 : 0,
    credit_score_value, credit_score_range, credit_score_date,
    JSON.stringify(credit_score_key_factors_json || []),
    decision,
    req.params.id
  );

  return res.json({ success: true });
});

// Delete application (with secure cleanup)
router.delete('/:id', (req, res) => {
  const app = db.prepare('SELECT id FROM applications WHERE id = ?').get(req.params.id);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  // Documents are purged by purgeService; here we mark as withdrawn
  db.prepare(`
    UPDATE applications SET status = 'Withdrawn', closed_at = datetime('now'), updated_at = datetime('now')
    WHERE id = ?
  `).run(req.params.id);

  return res.json({ success: true });
});

export default router;
