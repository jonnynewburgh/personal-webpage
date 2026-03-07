// creditReportSummarizer.js - Extract structured data from credit reports
// CRITICAL: Raw credit report text must NEVER be sent to the Claude API.
// Only the structured summary generated here is sent. (FCRA requirement)

/**
 * Extract structured summary from raw credit report text.
 * Uses regex-based extraction - no API call made here.
 */
export function summarizeCreditReport(rawText) {
  if (!rawText) return null;

  const summary = {
    open_tradelines: null,
    total_outstanding_debt: null,
    monthly_debt_service: null,
    delinquencies: {
      count: 0,
      severity: null,
      details: []
    },
    public_records: [],
    credit_score: null,
    score_range: null,
    extraction_note: 'Extracted by creditReportSummarizer - raw text not retained per FCRA policy'
  };

  // Count open tradelines
  const tradelineMatches = rawText.match(/(?:open|current)\s+(?:account|tradeline)/gi);
  if (tradelineMatches) {
    summary.open_tradelines = tradelineMatches.length;
  }

  // Extract total balance/debt (look for common patterns)
  const debtMatch = rawText.match(/(?:total\s+balance|total\s+debt|total\s+owing)[:\s]+\$?([\d,]+)/i);
  if (debtMatch) {
    summary.total_outstanding_debt = parseFloat(debtMatch[1].replace(/,/g, ''));
  }

  // Monthly payment obligations
  const monthlyMatch = rawText.match(/(?:total\s+monthly\s+payment|monthly\s+obligations?)[:\s]+\$?([\d,]+)/i);
  if (monthlyMatch) {
    summary.monthly_debt_service = parseFloat(monthlyMatch[1].replace(/,/g, ''));
  }

  // Delinquencies
  const lateMatches = rawText.match(/(\d+)\s*(?:times?\s+)?(?:30|60|90|120)\+?\s*(?:days?\s+)?(?:late|past\s+due)/gi) || [];
  summary.delinquencies.count = lateMatches.length;

  // Severity
  const has90Plus = /90\+?\s*days?\s*(?:late|past\s+due)/i.test(rawText);
  const has60Plus = /60\+?\s*days?\s*(?:late|past\s+due)/i.test(rawText);
  const has30Plus = /30\+?\s*days?\s*(?:late|past\s+due)/i.test(rawText);

  if (has90Plus) summary.delinquencies.severity = 'severe (90+ days late)';
  else if (has60Plus) summary.delinquencies.severity = 'moderate (60+ days late)';
  else if (has30Plus) summary.delinquencies.severity = 'minor (30+ days late)';
  else if (lateMatches.length > 0) summary.delinquencies.severity = 'minor';

  // Public records: bankruptcies
  if (/bankruptcy|chapter\s+7|chapter\s+13/i.test(rawText)) {
    const bkMatch = rawText.match(/(chapter\s+[713]+)\s+bankruptcy.*?(\d{4})/i);
    summary.public_records.push({
      type: 'Bankruptcy',
      detail: bkMatch ? `${bkMatch[1]} (${bkMatch[2]})` : 'Found in report'
    });
  }

  // Judgments
  if (/judgment|judgement/i.test(rawText)) {
    const jMatch = rawText.match(/judgment.*?(\d{4})/i);
    summary.public_records.push({
      type: 'Judgment',
      detail: jMatch ? `Year ${jMatch[1]}` : 'Found in report'
    });
  }

  // Liens
  if (/(?:tax\s+)?lien/i.test(rawText)) {
    summary.public_records.push({ type: 'Lien', detail: 'Found in report' });
  }

  // Credit score
  const scoreMatch = rawText.match(/(?:credit\s+score|fico\s+score|score)[:\s]+(\d{3})/i);
  if (scoreMatch) {
    summary.credit_score = parseInt(scoreMatch[1]);
  }

  // Score range
  if (summary.credit_score) {
    if (summary.credit_score >= 750) summary.score_range = 'Excellent (750+)';
    else if (summary.credit_score >= 700) summary.score_range = 'Good (700-749)';
    else if (summary.credit_score >= 650) summary.score_range = 'Fair (650-699)';
    else if (summary.credit_score >= 600) summary.score_range = 'Poor (600-649)';
    else summary.score_range = 'Very Poor (<600)';
  }

  return summary;
}
