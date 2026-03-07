// documents.js - File upload, text extraction, and association with applications
import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import db from '../db.js';
import { extractTextFromFile } from '../services/documentParser.js';
import { summarizeCreditReport } from '../services/creditReportSummarizer.js';
import { encryptFile } from '../services/fileEncryption.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const router = express.Router();

const UPLOAD_DIR = process.env.UPLOAD_DIR
  ? path.resolve(process.env.UPLOAD_DIR)
  : path.join(__dirname, '../../uploads');

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const appDir = path.join(UPLOAD_DIR, `app_${req.params.appId}`);
    fs.mkdirSync(appDir, { recursive: true });
    cb(null, appDir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}_${file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_')}`);
  }
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const allowed = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) cb(null, true);
    else cb(new Error('Only PDF, Word documents, and images (JPG/PNG) are allowed'));
  },
  limits: { fileSize: 25 * 1024 * 1024 } // 25MB per file
});

// Upload document for an application
router.post('/upload/:appId', upload.single('document'), async (req, res) => {
  const app = db.prepare('SELECT id FROM applications WHERE id = ?').get(req.params.appId);
  if (!app) return res.status(404).json({ error: 'Application not found' });
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

  const { document_label, is_credit_report } = req.body;
  const isCreditReport = is_credit_report === 'true' || is_credit_report === true;

  try {
    // Extract text from file
    let extractedText = null;
    const ext = path.extname(req.file.originalname).toLowerCase();
    if (['.pdf', '.docx', '.doc'].includes(ext)) {
      extractedText = await extractTextFromFile(req.file.path, req.file.originalname);
    }

    // Encrypt file on disk
    const encryptedPath = await encryptFile(req.file.path);

    // For credit reports: generate structured summary, store raw in encrypted file
    let creditSummaryJson = null;
    if (isCreditReport && extractedText) {
      const summary = summarizeCreditReport(extractedText);
      creditSummaryJson = JSON.stringify(summary);
      // Clear raw text from extracted_text for credit reports (store only summary)
      extractedText = null;
    }

    const result = db.prepare(`
      INSERT INTO documents (
        application_id, filename, file_path, document_label,
        extracted_text, is_credit_report, credit_summary_json,
        retention_category
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      req.params.appId,
      req.file.originalname,
      encryptedPath,
      document_label || 'Unlabeled',
      extractedText,
      isCreditReport ? 1 : 0,
      creditSummaryJson,
      isCreditReport ? 'credit_reports' : 'pii_documents'
    );

    return res.json({
      success: true,
      documentId: result.lastInsertRowid,
      extractedText: extractedText ? extractedText.substring(0, 200) + '...' : null,
      creditSummary: creditSummaryJson ? JSON.parse(creditSummaryJson) : null
    });
  } catch (err) {
    console.error('Document upload error:', err);
    return res.status(500).json({ error: err.message });
  }
});

// List documents for an application
router.get('/application/:appId', (req, res) => {
  const docs = db.prepare(`
    SELECT id, uploaded_at, filename, document_label, is_credit_report, credit_summary_json, purged_at
    FROM documents WHERE application_id = ? AND purged_at IS NULL
  `).all(req.params.appId);

  return res.json(docs.map(d => ({
    ...d,
    credit_summary_json: d.credit_summary_json ? JSON.parse(d.credit_summary_json) : null
  })));
});

// Delete a document
router.delete('/:id', async (req, res) => {
  const doc = db.prepare('SELECT * FROM documents WHERE id = ?').get(req.params.id);
  if (!doc) return res.status(404).json({ error: 'Document not found' });

  try {
    // Secure deletion: overwrite then unlink
    if (fs.existsSync(doc.file_path)) {
      const stat = fs.statSync(doc.file_path);
      const zeroBuf = Buffer.alloc(stat.size, 0);
      fs.writeFileSync(doc.file_path, zeroBuf);
      fs.unlinkSync(doc.file_path);
    }
    // Also delete encrypted file if different
    const encPath = doc.file_path + '.enc';
    if (fs.existsSync(encPath)) fs.unlinkSync(encPath);

    db.prepare('UPDATE documents SET purged_at = datetime(\'now\'), extracted_text = NULL, file_path = \'\' WHERE id = ?').run(req.params.id);

    return res.json({ success: true });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

export default router;
