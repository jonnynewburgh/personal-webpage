// memoGenerator.js - Build committee summary memo HTML
// Produces printable HTML; client can use browser print for PDF export

export function generateMemoHTML(app, review, documents, standalone = false) {
  const expenses = app.monthly_expenses_json || {};
  const debts = app.existing_debts_json || [];
  const refs = app.references_json || [];
  const ruleResults = review.rule_check_results || [];

  const totalExpenses = Object.values(expenses).reduce((s, v) => s + (parseFloat(v) || 0), 0);
  const totalDebt = debts.reduce((s, d) => s + (parseFloat(d.monthly_payment) || 0), 0);
  const proposedPayment = app.loan_amount_requested && app.repayment_term_months
    ? (app.loan_amount_requested / app.repayment_term_months).toFixed(2)
    : null;
  const surplus = app.monthly_income
    ? (app.monthly_income - totalExpenses - totalDebt - (proposedPayment || 0)).toFixed(2)
    : null;

  const passes = ruleResults.filter(r => r.status === 'pass').length;
  const fails = ruleResults.filter(r => r.status === 'fail').length;
  const warns = ruleResults.filter(r => r.status === 'warn').length;

  const styles = `
    <style>
      body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #222; }
      h1 { font-size: 1.4em; border-bottom: 2px solid #333; padding-bottom: 8px; }
      h2 { font-size: 1.1em; margin-top: 24px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
      table { width: 100%; border-collapse: collapse; margin: 8px 0; }
      td, th { padding: 4px 8px; border: 1px solid #ccc; font-size: 0.9em; }
      th { background: #f0f0f0; font-weight: bold; text-align: left; }
      .pass { color: #166534; } .fail { color: #991b1b; } .warn { color: #92400e; }
      .badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold; }
      .badge-pass { background: #dcfce7; color: #166534; }
      .badge-fail { background: #fee2e2; color: #991b1b; }
      .badge-warn { background: #fef9c3; color: #92400e; }
      .ai-review { background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px; white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 0.9em; }
      .header-info { background: #f0f4ff; border: 1px solid #c7d2fe; padding: 12px; margin-bottom: 16px; }
      .summary-row { font-weight: bold; background: #f0f0f0; }
      @media print { body { margin: 0; } }
    </style>`;

  const docRows = documents.map(d => `
    <tr>
      <td>${d.document_label || 'Unlabeled'}</td>
      <td>${d.filename}</td>
      <td>${d.is_credit_report ? 'Yes' : 'No'}</td>
      <td>${d.purged_at ? `Purged ${d.purged_at.substring(0, 10)}` : '<span class="pass">Present</span>'}</td>
    </tr>`).join('');

  const ruleRows = ruleResults.map(r => `
    <tr>
      <td><span class="badge badge-${r.status}">${r.status.toUpperCase()}</span></td>
      <td>${r.check}</td>
      <td>${r.detail}</td>
    </tr>`).join('');

  const html = `
    ${standalone ? `<!DOCTYPE html><html><head><meta charset="utf-8"><title>JIFLA Loan Application Memo</title>${styles}</head><body>` : styles}

    <div class="header-info">
      <strong>JIFLA — LOAN APPLICATION COMMITTEE MEMO</strong><br>
      <strong>CONFIDENTIAL — For authorized staff use only</strong><br>
      Application #${app.id} &nbsp;|&nbsp; Generated: ${new Date().toLocaleDateString()}<br>
      Reviewed: ${review.reviewed_at ? review.reviewed_at.substring(0, 10) : 'N/A'}
    </div>

    <h1>Application Summary: ${app.applicant_name}</h1>

    <table>
      <tr><th style="width:30%">Loan Request</th><td>$${(app.loan_amount_requested || 0).toLocaleString()} — ${app.loan_purpose_category || 'Unspecified'}</td></tr>
      <tr><th>Purpose Description</th><td>${app.loan_purpose_description || 'Not provided'}</td></tr>
      <tr><th>Repayment Term</th><td>${app.repayment_term_months ? `${app.repayment_term_months} months ($${proposedPayment}/mo)` : 'Not specified'}</td></tr>
      <tr><th>Status</th><td>${app.status}</td></tr>
      <tr><th>Privacy Notice</th><td>${app.privacy_notice_acknowledged ? `Acknowledged ${app.privacy_notice_date || ''}` : '<strong class="fail">NOT ACKNOWLEDGED</strong>'}</td></tr>
    </table>

    <h2>Financial Snapshot</h2>
    <table>
      <tr><th>Monthly Household Income</th><td>$${(app.monthly_income || 0).toLocaleString()}</td></tr>
      ${Object.entries(expenses).map(([k, v]) => `<tr><td style="padding-left:24px">${k}</td><td>$${(parseFloat(v) || 0).toLocaleString()}</td></tr>`).join('')}
      <tr><th>Total Monthly Expenses</th><td>$${totalExpenses.toLocaleString()}</td></tr>
      <tr><td>Existing Debt Payments</td><td>$${totalDebt.toFixed(2)}</td></tr>
      <tr><td>Proposed Loan Payment</td><td>${proposedPayment ? `$${proposedPayment}` : 'N/A'}</td></tr>
      <tr class="summary-row"><td>Net Monthly Surplus/(Deficit)</td><td>${surplus !== null ? `$${surplus}` : 'N/A'}</td></tr>
    </table>

    ${debts.length > 0 ? `
    <h2>Existing Debts</h2>
    <table>
      <tr><th>Creditor</th><th>Balance</th><th>Monthly Payment</th></tr>
      ${debts.map(d => `<tr><td>${d.creditor || 'Unknown'}</td><td>$${(d.balance || 0).toLocaleString()}</td><td>$${(d.monthly_payment || 0).toFixed(2)}</td></tr>`).join('')}
    </table>` : ''}

    <h2>Required Documents Status</h2>
    <table>
      <tr><th>Label</th><th>Filename</th><th>Credit Report?</th><th>Status</th></tr>
      ${docRows || '<tr><td colspan="4">No documents uploaded</td></tr>'}
    </table>

    <h2>Rule-Based Review Results <span style="font-weight:normal; font-size:0.85em">(${passes} pass, ${fails} fail, ${warns} warn)</span></h2>
    <table>
      <tr><th style="width:80px">Result</th><th style="width:200px">Check</th><th>Detail</th></tr>
      ${ruleRows || '<tr><td colspan="3">No checks run</td></tr>'}
    </table>

    <h2>AI Review Analysis</h2>
    <div class="ai-review">${review.ai_review_text || 'No AI review available.'}</div>

    ${app.staff_notes ? `<h2>Staff Notes</h2><p>${app.staff_notes}</p>` : ''}

    ${refs.length > 0 ? `
    <h2>References / Guarantors</h2>
    <table>
      <tr><th>Name</th><th>Relationship</th><th>Contact</th></tr>
      ${refs.map(r => `<tr><td>${r.name || ''}</td><td>${r.relationship || ''}</td><td>${r.contact || ''}</td></tr>`).join('')}
    </table>` : ''}

    <div style="margin-top:32px; font-size:0.8em; color:#666; border-top:1px solid #ccc; padding-top:8px;">
      This memo is confidential and subject to GLBA privacy requirements. It contains nonpublic personal information.
      Retain per JIFLA's data retention policy. Not for distribution outside authorized loan committee members.
    </div>

    ${standalone ? '</body></html>' : ''}`;

  return html;
}
