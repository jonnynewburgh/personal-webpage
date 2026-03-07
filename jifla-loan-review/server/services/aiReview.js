// aiReview.js - Layer 2 Claude API integration with PII filtering pipeline
//
// DATA HANDLING NOTE:
// Anthropic's data usage policy verified: 2025-01-01
// Per Anthropic's terms, API inputs/outputs are NOT used for model training by default.
// IMPORTANT: Sending applicant data to Anthropic constitutes sharing NPI with a
// nonaffiliated third party under GLBA Privacy Rule. This MUST be disclosed in JIFLA's
// privacy notice to applicants.
// Re-verify Anthropic's data policy at: https://www.anthropic.com/privacy
//
// PII FILTERING: This module applies a strict data filtering pipeline before any
// data reaches the Claude API. See buildReviewPayload() for what is/is not sent.

import Anthropic from '@anthropic-ai/sdk';
import crypto from 'crypto';
import db from '../db.js';
import { redactPII } from './piiRedactor.js';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const SYSTEM_PROMPT = `You are an experienced loan reviewer for JIFLA (Jewish Interest Free Loan Association of Georgia), a nonprofit organization that makes interest-free loans to individuals in need.

Your role is to assist staff in reviewing loan applications for compliance with JIFLA's written loan policy. You are NOT making approval or denial recommendations — that is exclusively the loan committee's responsibility.

CRITICAL FAIR LENDING INSTRUCTION: You must not consider, reference, or allow to influence your analysis in any way: the applicant's race, color, religion, national origin, sex, marital status, age, receipt of public assistance income, or exercise of any Consumer Credit Protection Act rights. If any such information appears in documents, ignore it entirely. Analyze only financial factors and policy compliance.

CRITICAL LANGUAGE INSTRUCTION: You must NOT use language such as "recommend approval," "recommend denial," "should be approved," "should be denied," or any other decision language. Your role is to flag, describe, and note — not to decide.

When reviewing, organize your findings into these sections:

1. **POLICY COMPLIANCE ISSUES** — Flag any issues not caught by the automated checks, citing specific policy sections where possible.

2. **DOCUMENT/APPLICATION INCONSISTENCIES** — Identify discrepancies between stated information and supporting documents (e.g., income on form vs. pay stubs).

3. **COMPLETENESS AND CLARITY** — Note what is missing, unclear, or ambiguous. Be precise about what is missing vs. what is merely unclear.

4. **NOTABLE FACTORS** — Note any hardship circumstances, strengths, or contextual factors the committee should be aware of. Do not make judgments — just note.

5. **SUGGESTED FOLLOW-UP** — Specific questions to ask the applicant, or additional documents to request, before the committee vote.

Remember: This is a charitable, interest-free loan program, not a commercial lending operation. The applicant's need and circumstances matter alongside financial capacity.`;

/**
 * Build the review payload, applying PII filtering pipeline.
 * Documents with is_credit_report=true are replaced with structured summary only.
 * All document text is PII-redacted before inclusion.
 */
function buildReviewPayload(app, policy, documents, ruleResults) {
  // Structured application data (never include SSN, full account numbers, DOB, DL#)
  const applicationData = {
    applicant_name: app.applicant_name,
    address: app.address,
    household_size: app.household_size,
    employment_status: app.employment_status,
    employer: app.employer,
    monthly_income: app.monthly_income,
    monthly_expenses: app.monthly_expenses_json,
    existing_debts: app.existing_debts_json,
    loan_amount_requested: app.loan_amount_requested,
    loan_purpose_category: app.loan_purpose_category,
    loan_purpose_description: app.loan_purpose_description,
    repayment_term_months: app.repayment_term_months,
    references_count: (app.references_json || []).length,
    staff_notes: app.staff_notes ? redactPII(app.staff_notes) : null,
    privacy_notice_acknowledged: app.privacy_notice_acknowledged
  };

  // Process documents: credit reports as summary only, others with PII redaction
  const documentSummaries = documents.map(doc => {
    if (doc.is_credit_report) {
      return {
        label: doc.document_label,
        type: 'credit_report',
        credit_summary: doc.credit_summary_json,
        note: 'Raw credit report text not included per FCRA policy'
      };
    }
    return {
      label: doc.document_label,
      type: 'document',
      extracted_text: doc.extracted_text ? redactPII(doc.extracted_text).substring(0, 3000) : null
    };
  });

  return {
    application: applicationData,
    documents: documentSummaries,
    rule_check_results: ruleResults,
    policy_structured_fields: policy.structured_fields
  };
}

/**
 * Run AI review using Claude API.
 * Returns { text, raw }
 */
export async function runAIReview(app, policy, documents, ruleResults, applicationId) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('ANTHROPIC_API_KEY not configured');
  }

  const payload = buildReviewPayload(app, policy, documents, ruleResults);
  const payloadStr = JSON.stringify(payload);
  const payloadSize = Buffer.byteLength(payloadStr, 'utf8');
  const payloadHash = crypto.createHash('sha256').update(payloadStr).digest('hex');

  const userMessage = `Please review this loan application and provide your analysis organized by the sections specified.

**LOAN POLICY:**
${policy.full_text.substring(0, 30000)}

**APPLICATION DATA AND DOCUMENTS:**
${payloadStr}

Provide a thorough review following the structure outlined in your instructions.`;

  let responseText = null;
  let rawResponse = null;
  let responseStatus = 'error';

  try {
    // Use streaming to handle potentially long responses
    const stream = client.messages.stream({
      model: 'claude-opus-4-6',
      max_tokens: 4096,
      thinking: { type: 'adaptive' },
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: userMessage }]
    });

    const finalMessage = await stream.finalMessage();
    const textBlock = finalMessage.content.find(b => b.type === 'text');
    responseText = textBlock?.text || '';
    rawResponse = {
      model: finalMessage.model,
      usage: finalMessage.usage,
      stop_reason: finalMessage.stop_reason
    };
    responseStatus = 'success';
  } finally {
    // Log API call metadata (not content) for GLBA audit trail
    db.prepare(`
      INSERT INTO api_call_log (application_id, payload_size_bytes, payload_hash, model_used, response_status)
      VALUES (?, ?, ?, ?, ?)
    `).run(applicationId, payloadSize, payloadHash, 'claude-opus-4-6', responseStatus);
  }

  return { text: responseText, raw: rawResponse };
}
