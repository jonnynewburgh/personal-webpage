// memos.js - Generate and export committee summary memos
import express from 'express';
import db from '../db.js';
import { generateMemoHTML } from '../services/memoGenerator.js';

const router = express.Router();

// Generate memo for a review
router.get('/review/:reviewId', (req, res) => {
  const review = db.prepare('SELECT * FROM reviews WHERE id = ?').get(req.params.reviewId);
  if (!review) return res.status(404).json({ error: 'Review not found' });

  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(review.application_id);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  // Parse JSON fields
  app.monthly_expenses_json = JSON.parse(app.monthly_expenses_json || '{}');
  app.existing_debts_json = JSON.parse(app.existing_debts_json || '[]');
  app.references_json = JSON.parse(app.references_json || '[]');
  review.rule_check_results = JSON.parse(review.rule_check_results || '[]');

  const docs = db.prepare(`
    SELECT filename, document_label, is_credit_report, purged_at
    FROM documents WHERE application_id = ?
  `).all(review.application_id);

  const memoHTML = generateMemoHTML(app, review, docs);

  // Mark memo as generated
  db.prepare('UPDATE reviews SET memo_generated_at = datetime(\'now\') WHERE id = ?').run(req.params.reviewId);

  return res.json({ memoHTML, review, application: app, documents: docs });
});

// Get memo as plain HTML for printing
router.get('/review/:reviewId/html', (req, res) => {
  const review = db.prepare('SELECT * FROM reviews WHERE id = ?').get(req.params.reviewId);
  if (!review) return res.status(404).json({ error: 'Review not found' });

  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(review.application_id);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  app.monthly_expenses_json = JSON.parse(app.monthly_expenses_json || '{}');
  app.existing_debts_json = JSON.parse(app.existing_debts_json || '[]');
  review.rule_check_results = JSON.parse(review.rule_check_results || '[]');

  const docs = db.prepare('SELECT filename, document_label, is_credit_report, purged_at FROM documents WHERE application_id = ?').all(review.application_id);

  const memoHTML = generateMemoHTML(app, review, docs, true);

  res.setHeader('Content-Type', 'text/html');
  return res.send(memoHTML);
});

export default router;
