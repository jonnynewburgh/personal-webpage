// policyParser.js - Extract structured fields from loan policy text
// Uses Claude API to intelligently parse the policy document

import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function parsePolicyFields(policyText) {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.warn('No Anthropic API key - returning empty policy fields');
    return getDefaultFields();
  }

  try {
    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 4096,
      system: `You are a loan policy analyst. Extract structured information from nonprofit loan policy documents.
Return a JSON object with these exact fields (use null if not specified):
{
  "max_loan_amounts": { "general": number_or_null, "by_category": {} },
  "eligible_purposes": ["list of eligible loan purposes/categories"],
  "required_documents": ["list of required documents"],
  "residency_requirements": "text description or null",
  "membership_requirements": "text description or null",
  "income_criteria": "text description or null",
  "hardship_criteria": "text description or null",
  "repayment_terms": { "min_months": null, "max_months": null, "description": "text" },
  "min_references": number_or_null,
  "disqualifying_conditions": ["list of disqualifying conditions"],
  "application_decision_timeline_days": number_or_null,
  "other_key_rules": ["any other important rules not captured above"]
}`,
      messages: [{
        role: 'user',
        content: `Extract structured policy fields from this loan policy document:\n\n${policyText.substring(0, 50000)}`
      }]
    });

    const text = response.content[0].text;
    // Extract JSON from response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return getDefaultFields();
  } catch (err) {
    console.error('Policy parsing error:', err.message);
    return getDefaultFields();
  }
}

function getDefaultFields() {
  return {
    max_loan_amounts: { general: null, by_category: {} },
    eligible_purposes: [],
    required_documents: [],
    residency_requirements: null,
    membership_requirements: null,
    income_criteria: null,
    hardship_criteria: null,
    repayment_terms: { min_months: null, max_months: null, description: null },
    min_references: null,
    disqualifying_conditions: [],
    application_decision_timeline_days: 30,
    other_key_rules: []
  };
}
