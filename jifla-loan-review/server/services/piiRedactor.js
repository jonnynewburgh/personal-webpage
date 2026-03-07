// piiRedactor.js - Strip SSNs, account numbers, DOBs before API calls
// CRITICAL: This runs on all document text before sending to Claude API
// per GLBA Privacy Rule requirements for sharing NPI with third parties.

/**
 * Redact common PII patterns from text.
 * Returns redacted text with placeholders.
 */
export function redactPII(text) {
  if (!text) return text;

  let redacted = text;

  // SSN: XXX-XX-XXXX or XXXXXXXXX (9 digits)
  // Keep last 4 digits to preserve some context
  redacted = redacted.replace(/\b(\d{3})-(\d{2})-(\d{4})\b/g, 'XXX-XX-$3');
  redacted = redacted.replace(/\b(\d{3})(\d{2})(\d{4})\b/g, (m, p1, p2, p3) => `XXXXXXXXX`);

  // Bank account numbers (8-17 digits, often preceded by "account" or "#")
  // Keep last 4 digits
  redacted = redacted.replace(
    /\b(account\s*#?\s*|acct\.?\s*#?\s*)(\d{4,})/gi,
    (m, prefix, num) => `${prefix}XXXX${num.slice(-4)}`
  );
  // Routing numbers (9-digit ABA routing numbers)
  redacted = redacted.replace(/\b(\d{9})\b(?=\s*(routing|aba))/gi, 'XXXXXXXXX');

  // Credit/debit card numbers (15-16 digits)
  redacted = redacted.replace(/\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{3,4})\b/g, (m) => {
    const digits = m.replace(/[\s-]/g, '');
    if (digits.length >= 15 && digits.length <= 16) {
      return `XXXX-XXXX-XXXX-${digits.slice(-4)}`;
    }
    return m;
  });

  // Dates of birth - replace with approximate age
  // Format: MM/DD/YYYY or MM-DD-YYYY or Month DD, YYYY
  redacted = redacted.replace(
    /\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}\b/g,
    (m) => {
      const parts = m.split(/[\/\-]/);
      const year = parseInt(parts[2]);
      const age = new Date().getFullYear() - year;
      return `[DOB REDACTED - Age approx. ${age}]`;
    }
  );

  // Georgia Driver's License: 1 letter + 8 digits
  redacted = redacted.replace(/\b([A-Z])(\d{8})\b/g, '$1XXXXXXXX');

  return redacted;
}

/**
 * Redact PII from an array of document objects.
 */
export function redactDocuments(documents) {
  return documents.map(doc => ({
    ...doc,
    extracted_text: doc.extracted_text ? redactPII(doc.extracted_text) : null
  }));
}

/**
 * Check if text appears to contain un-redacted PII (for logging/alerting).
 */
export function containsPII(text) {
  if (!text) return false;
  const patterns = [
    /\b\d{3}-\d{2}-\d{4}\b/,    // SSN
    /\b\d{9}\b/,                  // 9-digit numbers (potential SSN/routing)
    /\b\d{15,16}\b/               // Card numbers
  ];
  return patterns.some(p => p.test(text));
}
