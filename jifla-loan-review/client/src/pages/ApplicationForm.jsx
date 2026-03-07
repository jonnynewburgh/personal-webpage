import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const EXPENSE_CATEGORIES = ['Rent/Mortgage', 'Utilities', 'Food', 'Transportation', 'Medical', 'Childcare', 'Other'];
const LOAN_PURPOSES = [
  'Medical/Healthcare', 'Housing/Rent Assistance', 'Utilities', 'Education',
  'Job-Related', 'Home Repair', 'Vehicle Repair', 'Food/Basic Needs',
  'Funeral/Bereavement', 'Other'
];

function SectionHeader({ title }) {
  return <h2 className="text-base font-semibold text-blue-900 border-b border-blue-200 pb-1 mb-4 mt-6">{title}</h2>;
}

function Field({ label, required, children, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}{required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
    </div>
  );
}

const inputClass = "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

export default function ApplicationForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    applicant_name: '',
    address: '',
    phone: '',
    email: '',
    household_size: '',
    employment_status: '',
    employer: '',
    monthly_income: '',
    monthly_expenses: {},
    existing_debts: [],
    loan_amount_requested: '',
    loan_purpose_category: LOAN_PURPOSES[0],
    loan_purpose_description: '',
    repayment_term_months: '',
    references: [],
    staff_notes: '',
    privacy_notice_acknowledged: false,
    privacy_notice_date: '',
    privacy_notice_method: 'in-person'
  });

  useEffect(() => {
    if (isEdit) {
      fetch(`/api/applications/${id}`, { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
          setForm({
            applicant_name: data.applicant_name || '',
            address: data.address || '',
            phone: data.phone || '',
            email: data.email || '',
            household_size: data.household_size || '',
            employment_status: data.employment_status || '',
            employer: data.employer || '',
            monthly_income: data.monthly_income || '',
            monthly_expenses: data.monthly_expenses_json || {},
            existing_debts: data.existing_debts_json || [],
            loan_amount_requested: data.loan_amount_requested || '',
            loan_purpose_category: data.loan_purpose_category || LOAN_PURPOSES[0],
            loan_purpose_description: data.loan_purpose_description || '',
            repayment_term_months: data.repayment_term_months || '',
            references: data.references_json || [],
            staff_notes: data.staff_notes || '',
            privacy_notice_acknowledged: !!data.privacy_notice_acknowledged,
            privacy_notice_date: data.privacy_notice_date || '',
            privacy_notice_method: data.privacy_notice_method || 'in-person'
          });
        });
    }
  }, [id, isEdit]);

  const set = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const setExpense = (category, value) => {
    setForm(prev => ({
      ...prev,
      monthly_expenses: { ...prev.monthly_expenses, [category]: value }
    }));
  };

  const addDebt = () => setForm(prev => ({
    ...prev,
    existing_debts: [...prev.existing_debts, { creditor: '', balance: '', monthly_payment: '' }]
  }));

  const setDebt = (i, field, value) => setForm(prev => {
    const debts = [...prev.existing_debts];
    debts[i] = { ...debts[i], [field]: value };
    return { ...prev, existing_debts: debts };
  });

  const removeDebt = (i) => setForm(prev => ({
    ...prev,
    existing_debts: prev.existing_debts.filter((_, idx) => idx !== i)
  }));

  const addReference = () => setForm(prev => ({
    ...prev,
    references: [...prev.references, { name: '', relationship: '', contact: '' }]
  }));

  const setRef = (i, field, value) => setForm(prev => {
    const refs = [...prev.references];
    refs[i] = { ...refs[i], [field]: value };
    return { ...prev, references: refs };
  });

  const removeRef = (i) => setForm(prev => ({
    ...prev,
    references: prev.references.filter((_, idx) => idx !== i)
  }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    const body = {
      applicant_name: form.applicant_name,
      address: form.address,
      phone: form.phone,
      email: form.email,
      household_size: form.household_size ? parseInt(form.household_size) : null,
      employment_status: form.employment_status,
      employer: form.employer,
      monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : null,
      monthly_expenses_json: form.monthly_expenses,
      existing_debts_json: form.existing_debts.map(d => ({
        creditor: d.creditor,
        balance: d.balance ? parseFloat(d.balance) : 0,
        monthly_payment: d.monthly_payment ? parseFloat(d.monthly_payment) : 0
      })),
      loan_amount_requested: form.loan_amount_requested ? parseFloat(form.loan_amount_requested) : null,
      loan_purpose_category: form.loan_purpose_category,
      loan_purpose_description: form.loan_purpose_description,
      repayment_term_months: form.repayment_term_months ? parseInt(form.repayment_term_months) : null,
      references_json: form.references,
      staff_notes: form.staff_notes,
      privacy_notice_acknowledged: form.privacy_notice_acknowledged,
      privacy_notice_date: form.privacy_notice_date || null,
      privacy_notice_method: form.privacy_notice_method
    };

    try {
      const url = isEdit ? `/api/applications/${id}` : '/api/applications';
      const method = isEdit ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Save failed');

      navigate(`/applications/${isEdit ? id : data.id}`);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        {isEdit ? 'Edit Application' : 'New Loan Application'}
      </h1>
      <p className="text-sm text-gray-500 mb-6">All fields marked * are required.</p>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6">

        <SectionHeader title="Applicant Information" />
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <Field label="Full Name" required>
              <input className={inputClass} value={form.applicant_name} onChange={e => set('applicant_name', e.target.value)} required />
            </Field>
          </div>
          <div className="col-span-2">
            <Field label="Address" required>
              <input className={inputClass} value={form.address} onChange={e => set('address', e.target.value)} />
            </Field>
          </div>
          <Field label="Phone">
            <input className={inputClass} type="tel" value={form.phone} onChange={e => set('phone', e.target.value)} />
          </Field>
          <Field label="Email">
            <input className={inputClass} type="email" value={form.email} onChange={e => set('email', e.target.value)} />
          </Field>
          <Field label="Household Size">
            <input className={inputClass} type="number" min="1" value={form.household_size} onChange={e => set('household_size', e.target.value)} />
          </Field>
          <Field label="Employment Status">
            <select className={inputClass} value={form.employment_status} onChange={e => set('employment_status', e.target.value)}>
              <option value="">-- Select --</option>
              <option>Employed full-time</option>
              <option>Employed part-time</option>
              <option>Self-employed</option>
              <option>Unemployed</option>
              <option>Retired</option>
              <option>Disabled</option>
              <option>Student</option>
            </select>
          </Field>
          <div className="col-span-2">
            <Field label="Employer / Income Source">
              <input className={inputClass} value={form.employer} onChange={e => set('employer', e.target.value)} />
            </Field>
          </div>
          <Field label="Monthly Household Income ($)" required>
            <input className={inputClass} type="number" min="0" step="0.01" value={form.monthly_income} onChange={e => set('monthly_income', e.target.value)} />
          </Field>
        </div>

        <SectionHeader title="Monthly Expenses" />
        <p className="text-xs text-gray-500 mb-3">Enter monthly amounts for each category that applies.</p>
        <div className="grid grid-cols-2 gap-3">
          {EXPENSE_CATEGORIES.map(cat => (
            <Field key={cat} label={`${cat} ($)`}>
              <input
                className={inputClass}
                type="number"
                min="0"
                step="0.01"
                value={form.monthly_expenses[cat] || ''}
                onChange={e => setExpense(cat, e.target.value)}
              />
            </Field>
          ))}
        </div>

        <SectionHeader title="Existing Debts" />
        <p className="text-xs text-gray-500 mb-3">List all existing credit obligations (credit cards, loans, etc.).</p>
        {form.existing_debts.map((debt, i) => (
          <div key={i} className="bg-gray-50 rounded p-3 mb-2 grid grid-cols-3 gap-2 items-end">
            <Field label="Creditor Name">
              <input className={inputClass} value={debt.creditor} onChange={e => setDebt(i, 'creditor', e.target.value)} />
            </Field>
            <Field label="Balance ($)">
              <input className={inputClass} type="number" min="0" value={debt.balance} onChange={e => setDebt(i, 'balance', e.target.value)} />
            </Field>
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <Field label="Monthly Payment ($)">
                  <input className={inputClass} type="number" min="0" value={debt.monthly_payment} onChange={e => setDebt(i, 'monthly_payment', e.target.value)} />
                </Field>
              </div>
              <button type="button" onClick={() => removeDebt(i)} className="text-red-500 hover:text-red-700 pb-2 text-sm">Remove</button>
            </div>
          </div>
        ))}
        <button type="button" onClick={addDebt} className="text-blue-600 hover:underline text-sm">+ Add Debt</button>

        <SectionHeader title="Loan Request" />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Amount Requested ($)" required>
            <input className={inputClass} type="number" min="0" step="0.01" value={form.loan_amount_requested} onChange={e => set('loan_amount_requested', e.target.value)} required />
          </Field>
          <Field label="Repayment Term (months)" required>
            <input className={inputClass} type="number" min="1" max="120" value={form.repayment_term_months} onChange={e => set('repayment_term_months', e.target.value)} />
          </Field>
          <Field label="Loan Purpose Category" required>
            <select className={inputClass} value={form.loan_purpose_category} onChange={e => set('loan_purpose_category', e.target.value)}>
              {LOAN_PURPOSES.map(p => <option key={p}>{p}</option>)}
            </select>
          </Field>
          <div className="col-span-2">
            <Field label="Purpose Description (explain the specific need)" required>
              <textarea className={inputClass} rows={3} value={form.loan_purpose_description} onChange={e => set('loan_purpose_description', e.target.value)} />
            </Field>
          </div>
        </div>

        <SectionHeader title="References / Guarantors" />
        {form.references.map((ref, i) => (
          <div key={i} className="bg-gray-50 rounded p-3 mb-2 grid grid-cols-3 gap-2 items-end">
            <Field label="Full Name">
              <input className={inputClass} value={ref.name} onChange={e => setRef(i, 'name', e.target.value)} />
            </Field>
            <Field label="Relationship">
              <input className={inputClass} value={ref.relationship} onChange={e => setRef(i, 'relationship', e.target.value)} />
            </Field>
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <Field label="Phone / Email">
                  <input className={inputClass} value={ref.contact} onChange={e => setRef(i, 'contact', e.target.value)} />
                </Field>
              </div>
              <button type="button" onClick={() => removeRef(i)} className="text-red-500 hover:text-red-700 pb-2 text-sm">Remove</button>
            </div>
          </div>
        ))}
        <button type="button" onClick={addReference} className="text-blue-600 hover:underline text-sm">+ Add Reference</button>

        <SectionHeader title="Privacy Notice (GLBA Required)" />
        <div className="bg-amber-50 border border-amber-200 rounded p-4 mb-4">
          <p className="text-sm text-amber-800 font-medium mb-1">GLBA Privacy Notice Requirement</p>
          <p className="text-xs text-amber-700">Per the Gramm-Leach-Bliley Act, the applicant must receive a privacy notice before their information is processed. This notice must disclose that application data may be shared with third-party service providers including AI analysis services (Anthropic) as part of the review process.</p>
        </div>
        <div className="space-y-3">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.privacy_notice_acknowledged}
              onChange={e => set('privacy_notice_acknowledged', e.target.checked)}
              className="mt-1"
            />
            <span className="text-sm text-gray-700">Applicant has received and acknowledged the JIFLA GLBA privacy notice</span>
          </label>
          {form.privacy_notice_acknowledged && (
            <div className="grid grid-cols-2 gap-4 ml-7">
              <Field label="Date Acknowledged">
                <input className={inputClass} type="date" value={form.privacy_notice_date} onChange={e => set('privacy_notice_date', e.target.value)} />
              </Field>
              <Field label="Method">
                <select className={inputClass} value={form.privacy_notice_method} onChange={e => set('privacy_notice_method', e.target.value)}>
                  <option value="in-person">In-person</option>
                  <option value="mailed">Mailed</option>
                  <option value="electronic">Electronic</option>
                </select>
              </Field>
            </div>
          )}
        </div>

        <SectionHeader title="Staff Notes" />
        <Field label="Additional notes (not included in applicant-facing communications)">
          <textarea className={inputClass} rows={4} value={form.staff_notes} onChange={e => set('staff_notes', e.target.value)} />
        </Field>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-700 hover:bg-blue-600 text-white px-6 py-2 rounded text-sm font-medium disabled:opacity-50"
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Application'}
          </button>
          <button
            type="button"
            onClick={() => navigate(isEdit ? `/applications/${id}` : '/')}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 px-6 py-2 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
