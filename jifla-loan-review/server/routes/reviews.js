// reviews.js - Trigger and retrieve application reviews
import express from 'express';
import db from '../db.js';
import { runRuleEngine } from '../services/ruleEngine.js';
import { runAIReview } from '../services/aiReview.js';

const router = express.Router();

// Get reviews for an application
router.get('/application/:appId', (req, res) => {
  const reviews = db.prepare(`
    SELECT id, reviewed_at, rule_check_results, ai_review_text, memo_generated_at
    FROM reviews WHERE application_id = ? ORDER BY reviewed_at DESC
  `).all(req.params.appId);

  return res.json(reviews.map(r => ({
    ...r,
    rule_check_results: JSON.parse(r.rule_check_results || '[]')
  })));
});

// Trigger a new review
router.post('/application/:appId', async (req, res) => {
  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(req.params.appId);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  const policy = db.prepare('SELECT * FROM loan_policies WHERE is_active = 1').get();
  if (!policy) return res.status(400).json({ error: 'No active loan policy found. Please upload a policy first.' });

  // Parse JSON fields
  app.monthly_expenses_json = JSON.parse(app.monthly_expenses_json || '{}');
  app.existing_debts_json = JSON.parse(app.existing_debts_json || '[]');
  app.references_json = JSON.parse(app.references_json || '[]');
  policy.structured_fields = JSON.parse(policy.structured_fields || '{}');

  // Get documents
  const documents = db.prepare(`
    SELECT id, filename, document_label, extracted_text, is_credit_report, credit_summary_json
    FROM documents WHERE application_id = ? AND purged_at IS NULL
  `).all(req.params.appId);

  const docs = documents.map(d => ({
    ...d,
    credit_summary_json: d.credit_summary_json ? JSON.parse(d.credit_summary_json) : null
  }));

  try {
    // Layer 1: Rule-based checks
    const ruleResults = runRuleEngine(app, policy, docs);

    // Layer 2: AI review (Claude API)
    let aiReviewText = null;
    let aiRawResponse = null;
    try {
      const aiResult = await runAIReview(app, policy, docs, ruleResults, req.params.appId);
      aiReviewText = aiResult.text;
      aiRawResponse = aiResult.raw;
    } catch (aiErr) {
      console.error('AI review error:', aiErr);
      aiReviewText = `AI review unavailable: ${aiErr.message}`;
    }

    // Update application status
    db.prepare(`
      UPDATE applications SET status = 'Under Review', updated_at = datetime('now') WHERE id = ? AND status = 'Draft'
    `).run(req.params.appId);

    // Save review
    const result = db.prepare(`
      INSERT INTO reviews (application_id, rule_check_results, ai_review_text, ai_review_raw_response)
      VALUES (?, ?, ?, ?)
    `).run(
      req.params.appId,
      JSON.stringify(ruleResults),
      aiReviewText,
      aiRawResponse ? JSON.stringify(aiRawResponse) : null
    );

    // Update status to Reviewed
    db.prepare(`UPDATE applications SET status = 'Reviewed', updated_at = datetime('now') WHERE id = ?`).run(req.params.appId);

    return res.json({
      success: true,
      reviewId: result.lastInsertRowid,
      ruleResults,
      aiReviewText
    });
  } catch (err) {
    console.error('Review error:', err);
    return res.status(500).json({ error: err.message });
  }
});

export default router;
