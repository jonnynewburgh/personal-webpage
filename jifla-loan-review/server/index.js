// index.js - Express app entry point for JIFLA Loan Review Tool
import 'dotenv/config';
import express from 'express';
import session from 'express-session';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

// Import DB first to run migrations
import db from './db.js';

// Import routes
import authRoutes from './routes/auth.js';
import policyRoutes from './routes/policies.js';
import applicationRoutes from './routes/applications.js';
import documentRoutes from './routes/documents.js';
import reviewRoutes from './routes/reviews.js';
import memoRoutes from './routes/memos.js';
import adverseActionRoutes from './routes/adverseAction.js';

// Import services
import { runPurgeService } from './services/purgeService.js';
import { logAccess } from './services/accessLogger.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

// Ensure uploads directory exists
const uploadsDir = process.env.UPLOAD_DIR
  ? path.resolve(process.env.UPLOAD_DIR)
  : path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// CORS - restrict to local in production
app.use(cors({
  origin: process.env.NODE_ENV === 'production'
    ? false
    : 'http://localhost:5173',
  credentials: true
}));

// Session management (GLBA requires access controls)
app.use(session({
  secret: process.env.SESSION_SECRET || 'change-this-in-production-immediately',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 8 * 60 * 60 * 1000 // 8 hours
  }
}));

// Authentication middleware - protects all /api routes except /api/auth/login
function requireAuth(req, res, next) {
  if (req.session && req.session.userId) {
    return next();
  }
  return res.status(401).json({ error: 'Authentication required' });
}

// Access logging middleware (GLBA Safeguards Rule requirement)
app.use('/api', (req, res, next) => {
  if (req.session?.userId && req.path !== '/auth/login' && req.path !== '/auth/logout') {
    const applicationId = req.params.id || req.body?.application_id || null;
    logAccess({
      userId: req.session.userId,
      applicationId,
      action: `${req.method} ${req.path}`,
      ipAddress: req.ip
    });
  }
  next();
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/policies', requireAuth, policyRoutes);
app.use('/api/applications', requireAuth, applicationRoutes);
app.use('/api/documents', requireAuth, documentRoutes);
app.use('/api/reviews', requireAuth, reviewRoutes);
app.use('/api/memos', requireAuth, memoRoutes);
app.use('/api/adverse-action', requireAuth, adverseActionRoutes);

// Serve React app in production
if (process.env.NODE_ENV === 'production') {
  const clientBuild = path.join(__dirname, '../client/dist');
  app.use(express.static(clientBuild));
  app.get('*', (req, res) => {
    res.sendFile(path.join(clientBuild, 'index.html'));
  });
}

// Run purge service on startup (checks retention deadlines)
runPurgeService();

// Schedule purge service to run daily
setInterval(runPurgeService, 24 * 60 * 60 * 1000);

app.listen(PORT, () => {
  console.log(`JIFLA Loan Review Tool running on port ${PORT}`);
  if (!process.env.SESSION_SECRET || process.env.SESSION_SECRET === 'change-this-in-production-immediately') {
    console.warn('WARNING: SESSION_SECRET not set in .env. Using insecure default.');
  }
  if (!process.env.ANTHROPIC_API_KEY) {
    console.warn('WARNING: ANTHROPIC_API_KEY not set. AI review will not function.');
  }
});

export default app;
