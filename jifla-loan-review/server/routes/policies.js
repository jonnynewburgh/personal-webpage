// policies.js - Loan policy upload and management
import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import db from '../db.js';
import { extractTextFromFile } from '../services/documentParser.js';
import { parsePolicyFields } from '../services/policyParser.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const router = express.Router();

const policyStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.join(__dirname, '../../uploads/policies');
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    cb(null, `policy_${Date.now()}_${file.originalname}`);
  }
});

const upload = multer({
  storage: policyStorage,
  fileFilter: (req, file, cb) => {
    const allowed = ['.pdf', '.docx', '.doc'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) cb(null, true);
    else cb(new Error('Only PDF and Word documents are allowed for policy upload'));
  },
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB
});

// Upload a new policy version
router.post('/upload', upload.single('policy'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

  try {
    const text = await extractTextFromFile(req.file.path, req.file.originalname);
    const structuredFields = await parsePolicyFields(text);

    // Get next version number
    const maxVersion = db.prepare('SELECT MAX(version) as v FROM loan_policies').get();
    const version = (maxVersion?.v || 0) + 1;

    // Deactivate all existing policies
    db.prepare('UPDATE loan_policies SET is_active = 0').run();

    const result = db.prepare(`
      INSERT INTO loan_policies (version, filename, full_text, structured_fields, is_active)
      VALUES (?, ?, ?, ?, 1)
    `).run(version, req.file.originalname, text, JSON.stringify(structuredFields));

    return res.json({
      success: true,
      policyId: result.lastInsertRowid,
      version,
      structuredFields
    });
  } catch (err) {
    console.error('Policy upload error:', err);
    return res.status(500).json({ error: err.message });
  }
});

// Get active policy
router.get('/active', (req, res) => {
  const policy = db.prepare('SELECT id, version, uploaded_at, filename, structured_fields FROM loan_policies WHERE is_active = 1').get();
  if (!policy) return res.status(404).json({ error: 'No active policy found' });

  policy.structured_fields = JSON.parse(policy.structured_fields || '{}');
  return res.json(policy);
});

// List all policy versions
router.get('/', (req, res) => {
  const policies = db.prepare('SELECT id, version, uploaded_at, filename, is_active FROM loan_policies ORDER BY version DESC').all();
  return res.json(policies);
});

// Activate a specific policy version
router.put('/:id/activate', (req, res) => {
  const policy = db.prepare('SELECT id FROM loan_policies WHERE id = ?').get(req.params.id);
  if (!policy) return res.status(404).json({ error: 'Policy not found' });

  db.prepare('UPDATE loan_policies SET is_active = 0').run();
  db.prepare('UPDATE loan_policies SET is_active = 1 WHERE id = ?').run(req.params.id);

  return res.json({ success: true });
});

// Get full policy text (for display)
router.get('/:id/text', (req, res) => {
  const policy = db.prepare('SELECT id, version, filename, full_text, structured_fields FROM loan_policies WHERE id = ?').get(req.params.id);
  if (!policy) return res.status(404).json({ error: 'Policy not found' });

  policy.structured_fields = JSON.parse(policy.structured_fields || '{}');
  return res.json(policy);
});

export default router;
