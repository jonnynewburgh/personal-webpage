# JIFLA Loan Application Review Tool

A browser-based loan application review tool for the Jewish Interest Free Loan Association of Georgia (JIFLA). Helps staff review applications, flag issues, and generate committee memos.

## ⚠️ Security Notice

**This tool handles sensitive personal financial information subject to GLBA, FCRA, ECOA, and Georgia data breach law. Before deploying:**
- Consult with a Georgia attorney experienced in nonprofit financial services and data privacy
- Set strong encryption keys in `.env` (see below)
- Configure filesystem-level encryption (LUKS/FileVault/BitLocker) on the server
- Review Anthropic's data usage policy and update `ANTHROPIC_POLICY_VERIFIED_DATE` in `.env`
- The `.env` file contains encryption keys — **NEVER commit it to version control**

## Setup

### 1. Install Dependencies

```bash
cd jifla-loan-review
npm install
cd client && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in all values:
# - ANTHROPIC_API_KEY
# - DB_ENCRYPTION_KEY (generate: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
# - FILE_ENCRYPTION_KEY (generate separately)
# - SESSION_SECRET (generate: node -e "console.log(require('crypto').randomBytes(64).toString('hex'))")
```

### 3. Create Admin User

```bash
node server/seed.js
```

### 4. Upload Loan Policy

Start the app, log in, and go to **Policy Management** to upload the JIFLA loan policy PDF or Word document.

### 5. Run

**Development (with hot reload):**
```bash
npm run dev
```
- Backend: http://localhost:3000
- Frontend: http://localhost:5173

**Production:**
```bash
npm run build
NODE_ENV=production npm run server:start
```

## Architecture

- **Backend:** Node.js + Express (ES modules)
- **Database:** SQLite via `better-sqlite3`
- **AI:** Anthropic Claude API (`claude-opus-4-6` with adaptive thinking)
- **Frontend:** React + Vite + Tailwind CSS
- **File Storage:** Local `/uploads` directory with AES-256-GCM encryption

## Regulatory Compliance Features

- **GLBA Safeguards Rule:** Session management, access logging, encryption at rest
- **GLBA Privacy Rule:** Privacy notice acknowledgment tracking
- **FCRA:** Credit report special handling (summary only sent to AI), adverse action notice generator
- **ECOA / Regulation B:** Adverse action notices with Reg B model forms, fair lending AI guardrails
- **Georgia O.C.G.A. § 10-1-912:** AES-256-GCM file encryption provides breach notification safe harbor

## Data Flow

1. Application entered → saved to encrypted SQLite
2. Documents uploaded → encrypted with AES-256-GCM on disk
3. Credit reports → structured summary only extracted, raw text not retained
4. Review triggered → PII redacted, credit summary substituted → Claude API call
5. Results displayed → committee memo generated (printable)
6. Decision recorded → adverse action notice generated if denied
7. Purge service runs → data deleted per retention schedule

## Key Files

```
server/
  index.js              Express app entry point
  db.js                 SQLite schema and migrations
  seed.js               Create initial admin user
  routes/               API routes
  services/
    piiRedactor.js      Strip SSNs, account numbers, DOBs before API calls
    creditReportSummarizer.js  Extract structured data from credit reports
    aiReview.js         Claude API integration (PII filtering pipeline)
    ruleEngine.js       Layer 1 policy compliance checks
    purgeService.js     Retention enforcement and secure deletion
    fileEncryption.js   AES-256-GCM file encryption
    adverseActionGenerator.js  ECOA/FCRA combined notice
client/src/
  pages/                React pages
  components/           Reusable UI components
```

## Production Deployment Notes

1. **Database encryption:** Replace `better-sqlite3` with `@journeyapps/sqlcipher` and set `DB_ENCRYPTION_KEY`
2. **Filesystem encryption:** Enable LUKS (Linux) / FileVault (Mac) / BitLocker (Windows) on the data volume
3. **HTTPS:** Place behind a reverse proxy (nginx/caddy) with TLS certificates
4. **Backups:** Encrypt database backups separately before offsite storage
5. **Access controls:** This tool should only be accessible from the office network or VPN
