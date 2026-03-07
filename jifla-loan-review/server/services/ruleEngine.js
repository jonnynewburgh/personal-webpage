// ruleEngine.js - Layer 1 rule-based policy compliance checks
// Checks structured form data against parsed policy fields (instant, no API call)

/**
 * Run all rule-based checks.
 * @param {object} app - Application record (with parsed JSON fields)
 * @param {object} policy - Active policy (with parsed structured_fields)
 * @param {Array} documents - Associated documents
 * @returns {Array} Array of check results: { check, status, detail }
 */
export function runRuleEngine(app, policy, documents) {
  const fields = policy.structured_fields || {};
  const results = [];

  // 1. Check loan amount
  results.push(checkLoanAmount(app, fields));

  // 2. Check required documents
  results.push(...checkRequiredDocuments(app, fields, documents));

  // 3. Check loan purpose
  results.push(checkLoanPurpose(app, fields));

  // 4. Check references
  results.push(checkReferences(app, fields));

  // 5. Check completeness
  results.push(...checkCompleteness(app));

  // 6. Check ability to repay
  results.push(checkRepaymentAbility(app));

  // 7. Check privacy notice
  results.push(checkPrivacyNotice(app));

  // 8. Check repayment term
  results.push(checkRepaymentTerm(app, fields));

  return results;
}

function checkLoanAmount(app, fields) {
  const requested = app.loan_amount_requested;
  if (!requested) {
    return { check: 'Loan Amount', status: 'fail', detail: 'No loan amount specified.' };
  }

  const maxGeneral = fields.max_loan_amounts?.general;
  if (maxGeneral && requested > maxGeneral) {
    return {
      check: 'Loan Amount',
      status: 'fail',
      detail: `Requested amount ($${requested.toLocaleString()}) exceeds policy maximum ($${maxGeneral.toLocaleString()}).`
    };
  }

  // Check by category
  const categoryMax = fields.max_loan_amounts?.by_category?.[app.loan_purpose_category];
  if (categoryMax && requested > categoryMax) {
    return {
      check: 'Loan Amount',
      status: 'fail',
      detail: `Requested amount ($${requested.toLocaleString()}) exceeds maximum for "${app.loan_purpose_category}" ($${categoryMax.toLocaleString()}).`
    };
  }

  return {
    check: 'Loan Amount',
    status: 'pass',
    detail: `$${requested.toLocaleString()} requested${maxGeneral ? ` (policy max: $${maxGeneral.toLocaleString()})` : ''}.`
  };
}

function checkRequiredDocuments(app, fields, documents) {
  const results = [];
  const requiredDocs = fields.required_documents || [];
  if (requiredDocs.length === 0) {
    results.push({ check: 'Required Documents', status: 'warn', detail: 'No required documents defined in policy - cannot verify completeness.' });
    return results;
  }

  const uploadedLabels = documents
    .filter(d => !d.purged_at)
    .map(d => (d.document_label || '').toLowerCase());

  for (const reqDoc of requiredDocs) {
    const found = uploadedLabels.some(label =>
      label.includes(reqDoc.toLowerCase()) || reqDoc.toLowerCase().includes(label)
    );
    results.push({
      check: `Required Document: ${reqDoc}`,
      status: found ? 'pass' : 'fail',
      detail: found ? `"${reqDoc}" uploaded.` : `"${reqDoc}" is required but not uploaded.`
    });
  }

  return results;
}

function checkLoanPurpose(app, fields) {
  const eligiblePurposes = fields.eligible_purposes || [];
  if (eligiblePurposes.length === 0) {
    return { check: 'Loan Purpose', status: 'warn', detail: 'No eligible purposes defined in policy - cannot verify.' };
  }

  if (!app.loan_purpose_category && !app.loan_purpose_description) {
    return { check: 'Loan Purpose', status: 'fail', detail: 'No loan purpose specified.' };
  }

  const purposeToCheck = (app.loan_purpose_category || app.loan_purpose_description || '').toLowerCase();
  const matches = eligiblePurposes.some(p =>
    purposeToCheck.includes(p.toLowerCase()) || p.toLowerCase().includes(purposeToCheck)
  );

  if (matches) {
    return { check: 'Loan Purpose', status: 'pass', detail: `"${app.loan_purpose_category}" is an eligible loan purpose.` };
  }

  return {
    check: 'Loan Purpose',
    status: 'warn',
    detail: `"${app.loan_purpose_category}" may not match an explicitly listed eligible purpose. Staff should verify with policy.`
  };
}

function checkReferences(app, fields) {
  const minRequired = fields.min_references || 0;
  const refs = app.references_json || [];

  if (minRequired === 0) {
    return { check: 'References', status: refs.length > 0 ? 'pass' : 'warn', detail: refs.length > 0 ? `${refs.length} reference(s) provided.` : 'No references provided (policy minimum not specified).' };
  }

  if (refs.length >= minRequired) {
    return { check: 'References', status: 'pass', detail: `${refs.length} of ${minRequired} required reference(s) provided.` };
  }

  return { check: 'References', status: 'fail', detail: `Only ${refs.length} of ${minRequired} required reference(s) provided.` };
}

function checkCompleteness(app) {
  const results = [];
  const required = [
    { field: 'applicant_name', label: 'Applicant Name' },
    { field: 'address', label: 'Address' },
    { field: 'phone', label: 'Phone Number' },
    { field: 'monthly_income', label: 'Monthly Income' },
    { field: 'loan_amount_requested', label: 'Loan Amount' },
    { field: 'loan_purpose_description', label: 'Loan Purpose Description' },
    { field: 'repayment_term_months', label: 'Repayment Term' }
  ];

  for (const { field, label } of required) {
    const val = app[field];
    const missing = val === null || val === undefined || val === '';
    results.push({
      check: `Field: ${label}`,
      status: missing ? 'fail' : 'pass',
      detail: missing ? `"${label}" is missing.` : `"${label}" is complete.`
    });
  }

  return results;
}

function checkRepaymentAbility(app) {
  const income = app.monthly_income;
  const expenses = app.monthly_expenses_json || {};
  const debts = app.existing_debts_json || [];
  const loanAmount = app.loan_amount_requested;
  const term = app.repayment_term_months;

  if (!income || !loanAmount || !term) {
    return { check: 'Ability to Repay', status: 'warn', detail: 'Insufficient data to calculate repayment capacity.' };
  }

  const totalExpenses = Object.values(expenses).reduce((sum, v) => sum + (parseFloat(v) || 0), 0);
  const totalDebtPayments = debts.reduce((sum, d) => sum + (parseFloat(d.monthly_payment) || 0), 0);
  const proposedPayment = loanAmount / term;
  const totalObligations = totalExpenses + totalDebtPayments + proposedPayment;
  const surplus = income - totalObligations;

  const surplusLabel = surplus >= 0 ? `surplus of $${surplus.toFixed(2)}` : `deficit of $${Math.abs(surplus).toFixed(2)}`;

  if (surplus < 0) {
    return {
      check: 'Ability to Repay',
      status: 'fail',
      detail: `With proposed payment of $${proposedPayment.toFixed(2)}/mo, applicant would have a monthly ${surplusLabel}. Income: $${income}/mo, Expenses: $${totalExpenses.toFixed(2)}/mo, Existing debt payments: $${totalDebtPayments.toFixed(2)}/mo.`
    };
  }

  if (surplus < 100) {
    return {
      check: 'Ability to Repay',
      status: 'warn',
      detail: `Applicant would have only a $${surplus.toFixed(2)}/mo surplus after proposed payment of $${proposedPayment.toFixed(2)}/mo. Very tight budget.`
    };
  }

  return {
    check: 'Ability to Repay',
    status: 'pass',
    detail: `Proposed payment: $${proposedPayment.toFixed(2)}/mo. Monthly surplus after all obligations: $${surplus.toFixed(2)}.`
  };
}

function checkPrivacyNotice(app) {
  if (app.privacy_notice_acknowledged) {
    return {
      check: 'Privacy Notice (GLBA)',
      status: 'pass',
      detail: `Applicant acknowledged privacy notice on ${app.privacy_notice_date || 'date not recorded'} via ${app.privacy_notice_method || 'method not recorded'}.`
    };
  }

  return {
    check: 'Privacy Notice (GLBA)',
    status: 'fail',
    detail: 'Applicant has not acknowledged the GLBA privacy notice. This is required before processing the application.'
  };
}

function checkRepaymentTerm(app, fields) {
  const term = app.repayment_term_months;
  if (!term) return { check: 'Repayment Term', status: 'fail', detail: 'No repayment term specified.' };

  const { min_months, max_months } = fields.repayment_terms || {};

  if (min_months && term < min_months) {
    return { check: 'Repayment Term', status: 'fail', detail: `Term of ${term} months is below policy minimum of ${min_months} months.` };
  }
  if (max_months && term > max_months) {
    return { check: 'Repayment Term', status: 'fail', detail: `Term of ${term} months exceeds policy maximum of ${max_months} months.` };
  }

  return { check: 'Repayment Term', status: 'pass', detail: `${term}-month repayment term is within policy limits.` };
}
