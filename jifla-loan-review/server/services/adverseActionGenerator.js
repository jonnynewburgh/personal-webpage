// adverseActionGenerator.js - ECOA/FCRA adverse action notice from Reg B model forms
// Based on Regulation B Appendix C, Form C-1 (combined ECOA/FCRA notice)
// 12 CFR 1002 Appendix C
// IMPORTANT: This template must be reviewed by counsel before use.

// Standard adverse action reason codes from Regulation B Appendix C
export const STANDARD_DENIAL_REASONS = [
  'Insufficient income',
  'Excessive obligations in relation to income',
  'Unable to verify income',
  'Length of employment',
  'Temporary or irregular employment',
  'Unable to verify employment',
  'Lack of established credit history',
  'Delinquent credit obligations',
  'Garnishment, attachment, foreclosure, repossession, collection action, or judgment',
  'Bankruptcy',
  'Number of recent inquiries on credit bureau report',
  'Value or type of collateral not sufficient',
  'Length of residence',
  'Unable to verify residence',
  'No credit file',
  'Limited credit experience',
  'Poor credit performance with us',
  'Delinquency with us',
  'Application incomplete',
  'Unable to verify information',
  'Credit application incomplete',
  'Temporary illness or disability',
  'Income from alimony, child support, or separate maintenance insufficient',
  'Outside special program guidelines',
  'Other (see below)'
];

export function generateAdverseActionNotice(app, standalone = false) {
  const denialReasons = app.denial_reasons_json || [];
  const keyFactors = app.credit_score_key_factors_json || [];
  const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  const styles = `
    <style>
      body { font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 30px; color: #222; line-height: 1.5; }
      h2 { font-size: 1.1em; margin-top: 20px; text-transform: uppercase; }
      .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 12px; margin-bottom: 20px; }
      .notice-box { border: 1px solid #999; padding: 12px; margin: 12px 0; background: #f9f9f9; }
      .bold { font-weight: bold; }
      ol { margin: 8px 0; padding-left: 20px; }
      @media print { body { margin: 0; } }
    </style>`;

  const html = `
    ${standalone ? `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Adverse Action Notice</title>${styles}</head><body>` : styles}

    <div class="header">
      <div class="bold">JEWISH INTEREST FREE LOAN ASSOCIATION OF GEORGIA</div>
      <div>Notice of Action Taken on Credit Application</div>
      <div style="font-size:0.85em">(Combined ECOA and FCRA Adverse Action Notice — Regulation B, Form C-1)</div>
    </div>

    <p><span class="bold">Date:</span> ${today}</p>
    <p><span class="bold">Applicant:</span> ${app.applicant_name}</p>
    <p><span class="bold">Address:</span> ${app.address || '[Address on file]'}</p>

    <h2>Description of Action Taken</h2>
    <p>Your application for a loan in the amount of <strong>$${(app.loan_amount_requested || 0).toLocaleString()}</strong> for <strong>${app.loan_purpose_description || app.loan_purpose_category || 'stated purpose'}</strong> has been <strong>DENIED</strong> on ${app.decision_date ? app.decision_date.substring(0, 10) : today}.</p>

    <h2>Principal Reason(s) for Action Taken</h2>
    <div class="notice-box">
      ${denialReasons.length > 0
        ? `<ol>${denialReasons.slice(0, 4).map(r => `<li>${r}</li>`).join('')}</ol>`
        : '<p><em>No specific reasons recorded. Staff must enter denial reasons before sending this notice.</em></p>'}
    </div>

    ${app.credit_report_used ? `
    <h2>Disclosure of Credit Score Used (FCRA § 615(a))</h2>
    <div class="notice-box">
      <p>Our credit decision was based in whole or in part on information obtained from a consumer reporting agency (credit bureau).</p>
      <p><span class="bold">Consumer Reporting Agency (CRA) that supplied the report:</span><br>
      ${app.cra_name || '[CRA Name]'}<br>
      ${app.cra_address || '[CRA Address]'}<br>
      ${app.cra_phone || '[CRA Phone]'}</p>
      <p>The consumer reporting agency that provided information about you played no part in our decision and is unable to provide you with specific reasons why we denied your request.</p>
      ${app.credit_score_used ? `
      <p><span class="bold">Credit Score Used:</span> ${app.credit_score_value || 'N/A'}<br>
      <span class="bold">Score Range:</span> ${app.credit_score_range || 'N/A'}<br>
      <span class="bold">Date of Score:</span> ${app.credit_score_date || 'N/A'}</p>
      ${keyFactors.length > 0 ? `<p><span class="bold">Key factors that adversely affected your credit score:</span></p><ol>${keyFactors.slice(0, 4).map(f => `<li>${f}</li>`).join('')}</ol>` : ''}
      ` : ''}
    </div>

    <h2>Your Rights Under the Fair Credit Reporting Act (FCRA)</h2>
    <div class="notice-box">
      <p>You have the right to obtain a <strong>free copy of your credit report</strong> from the consumer reporting agency listed above if you request it <strong>within 60 days</strong> of receiving this notice.</p>
      <p>You have the right to <strong>dispute inaccurate or incomplete information</strong> in your credit report. If you find that any information in the report used in our decision is inaccurate or incomplete, you have the right to dispute the matter with the reporting agency.</p>
    </div>` : ''}

    <h2>Your Rights Under the Equal Credit Opportunity Act (ECOA)</h2>
    <div class="notice-box">
      <p>The federal Equal Credit Opportunity Act prohibits creditors from discriminating against credit applicants on the basis of race, color, religion, national origin, sex, marital status, age (provided the applicant has the capacity to enter into a binding contract); because all or part of the applicant's income derives from any public assistance program; or because the applicant has in good faith exercised any right under the Consumer Credit Protection Act.</p>
      <p>The federal agency that administers compliance with this law concerning this creditor is:</p>
      <p><strong>Federal Trade Commission<br>Equal Credit Opportunity<br>Washington, DC 20580</strong></p>
    </div>

    <p style="margin-top:20px; font-size:0.9em; color:#555;">
      If you have questions about this notice, please contact JIFLA at [JIFLA contact information]. You may request a statement of specific reasons for this action within 60 days of receiving this notice.
    </p>

    <div style="margin-top:32px; font-size:0.8em; color:#666; border-top:1px solid #ccc; padding-top:8px;">
      <strong>NOTICE: This is an adverse action notice required by ECOA (12 CFR 1002) and FCRA (15 U.S.C. § 1681m).</strong><br>
      This document must be retained in the application file per ECOA record retention requirements (25 months from date of action).
    </div>

    ${standalone ? '</body></html>' : ''}`;

  return html;
}
