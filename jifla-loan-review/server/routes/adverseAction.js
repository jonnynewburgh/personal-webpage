// adverseAction.js - ECOA/FCRA adverse action notice generation and tracking
import express from 'express';
import db from '../db.js';
import { generateAdverseActionNotice } from '../services/adverseActionGenerator.js';

const router = express.Router();

// Generate adverse action notice for a denied application
router.get('/application/:appId', (req, res) => {
  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(req.params.appId);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  if (app.decision !== 'Denied') {
    return res.status(400).json({ error: 'Adverse action notice only applies to denied applications' });
  }

  app.denial_reasons_json = JSON.parse(app.denial_reasons_json || '[]');
  app.credit_score_key_factors_json = JSON.parse(app.credit_score_key_factors_json || '[]');

  const noticeHTML = generateAdverseActionNotice(app);

  // Record notice generation
  db.prepare(`
    UPDATE applications
    SET adverse_action_notice_generated_at = datetime('now'), updated_at = datetime('now')
    WHERE id = ?
  `).run(req.params.appId);

  return res.json({ noticeHTML, application: app });
});

// Get notice as HTML for printing
router.get('/application/:appId/html', (req, res) => {
  const app = db.prepare('SELECT * FROM applications WHERE id = ?').get(req.params.appId);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  app.denial_reasons_json = JSON.parse(app.denial_reasons_json || '[]');
  app.credit_score_key_factors_json = JSON.parse(app.credit_score_key_factors_json || '[]');

  const noticeHTML = generateAdverseActionNotice(app, true);

  res.setHeader('Content-Type', 'text/html');
  return res.send(noticeHTML);
});

// Mark notice as sent
router.put('/application/:appId/sent', (req, res) => {
  const { method } = req.body;
  const app = db.prepare('SELECT id FROM applications WHERE id = ?').get(req.params.appId);
  if (!app) return res.status(404).json({ error: 'Application not found' });

  db.prepare(`
    UPDATE applications
    SET adverse_action_notice_sent_at = datetime('now'),
        adverse_action_notice_method = ?,
        updated_at = datetime('now')
    WHERE id = ?
  `).run(method || 'mail', req.params.appId);

  return res.json({ success: true });
});

export default router;
