import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge.jsx';
import DocumentUpload from '../components/DocumentUpload.jsx';

const DENIAL_REASONS = [
  'Insufficient income',
  'Excessive obligations in relation to income',
  'Unable to verify income',
  'Delinquent credit obligations',
  'Bankruptcy',
  'No credit file',
  'Limited credit experience',
  'Application incomplete',
  'Outside program guidelines',
  'Unable to verify information',
  'Other'
];

export default function ApplicationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [showDecision, setShowDecision] = useState(false);
  const [decision, setDecision] = useState('');
  const [denialReasons, setDenialReasons] = useState([]);
  const [craName, setCraName] = useState('');
  const [craAddress, setCraAddress] = useState('');
  const [craPhone, setCraPhone] = useState('');
  const [creditReportUsed, setCreditReportUsed] = useState(false);
  const [savingDecision, setSavingDecision] = useState(false);

  const loadApp = () => {
    fetch(`/api/applications/${id}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setApp(data); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { loadApp(); }, [id]);

  const handleReview = async () => {
    setReviewing(true);
    setReviewError('');
    try {
      const res = await fetch(`/api/reviews/application/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Review failed');

      navigate(`/reviews/${data.reviewId}`);
    } catch (err) {
      setReviewError(err.message);
      setReviewing(false);
    }
  };

  const toggleDenialReason = (reason) => {
    setDenialReasons(prev =>
      prev.includes(reason) ? prev.filter(r => r !== reason) : [...prev, reason]
    );
  };

  const handleDecision = async () => {
    if (!decision) return;
    setSavingDecision(true);

    try {
      const res = await fetch(`/api/applications/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          decision,
          denial_reasons_json: denialReasons,
          credit_report_used: creditReportUsed,
          cra_name: craName,
          cra_address: craAddress,
          cra_phone: craPhone
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to save decision');

      setShowDecision(false);
      loadApp();
    } catch (err) {
      alert(err.message);
    } finally {
      setSavingDecision(false);
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!app) return <p className="text-red-500">Application not found.</p>;

  const expenses = app.monthly_expenses_json || {};
  const debts = app.existing_debts_json || [];
  const refs = app.references_json || [];
  const totalExpenses = Object.values(expenses).reduce((s, v) => s + (parseFloat(v) || 0), 0);
  const totalDebt = debts.reduce((s, d) => s + (parseFloat(d.monthly_payment) || 0), 0);

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-gray-900">{app.applicant_name}</h1>
            <StatusBadge status={app.status} />
          </div>
          <p className="text-sm text-gray-500">
            Application #{app.id} · Created {app.created_at?.substring(0, 10)} ·
            {app.loan_amount_requested
              ? ` $${app.loan_amount_requested.toLocaleString()} requested`
              : ' Amount not specified'}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/applications/${id}/edit`}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 px-3 py-1.5 rounded text-sm"
          >
            Edit
          </Link>
          {!['Approved', 'Denied', 'Withdrawn'].includes(app.status) && (
            <button
              onClick={handleReview}
              disabled={reviewing}
              className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-1.5 rounded text-sm font-medium disabled:opacity-50"
            >
              {reviewing ? 'Running Review...' : 'Review Application'}
            </button>
          )}
          {!['Approved', 'Denied', 'Withdrawn'].includes(app.status) && (
            <button
              onClick={() => setShowDecision(true)}
              className="bg-green-700 hover:bg-green-600 text-white px-4 py-1.5 rounded text-sm font-medium"
            >
              Record Decision
            </button>
          )}
        </div>
      </div>

      {reviewError && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {reviewError}
        </div>
      )}

      {/* Privacy Notice Warning */}
      {!app.privacy_notice_acknowledged && (
        <div className="mb-4 bg-amber-50 border border-amber-300 text-amber-800 px-4 py-3 rounded text-sm">
          <strong>⚠ GLBA Privacy Notice Required:</strong> The applicant has not acknowledged the privacy notice.
          This must be obtained before processing or reviewing this application.
        </div>
      )}

      {/* Decision Banner */}
      {app.decision && (
        <div className={`mb-4 px-4 py-3 rounded border text-sm ${app.decision === 'Approved' ? 'bg-green-50 border-green-300 text-green-800' : app.decision === 'Denied' ? 'bg-red-50 border-red-300 text-red-800' : 'bg-gray-50 border-gray-300'}`}>
          <strong>Decision: {app.decision}</strong> — {app.decision_date?.substring(0, 10)}
          {app.decision === 'Denied' && (
            <span className="ml-4">
              <Link to={`/applications/${id}/adverse-action`} className="underline font-medium">
                Generate Adverse Action Notice →
              </Link>
            </span>
          )}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">

        {/* Main Content */}
        <div className="col-span-2 space-y-6">

          {/* Financial Summary */}
          <section className="bg-white rounded-lg border border-gray-200 p-4">
            <h2 className="font-semibold text-gray-800 mb-3">Financial Summary</h2>
            <table className="w-full text-sm">
              <tbody className="divide-y divide-gray-100">
                <tr><td className="py-1 text-gray-600">Monthly Income</td><td className="py-1 font-medium text-right">${(app.monthly_income || 0).toLocaleString()}</td></tr>
                {Object.entries(expenses).filter(([,v]) => v).map(([k, v]) => (
                  <tr key={k}><td className="py-1 text-gray-500 pl-4">{k}</td><td className="py-1 text-right">${(parseFloat(v) || 0).toLocaleString()}</td></tr>
                ))}
                <tr><td className="py-1 text-gray-600">Total Expenses</td><td className="py-1 text-right">${totalExpenses.toFixed(2)}</td></tr>
                <tr><td className="py-1 text-gray-600">Existing Debt Payments</td><td className="py-1 text-right">${totalDebt.toFixed(2)}</td></tr>
                {app.loan_amount_requested && app.repayment_term_months && (
                  <tr><td className="py-1 text-gray-600">Proposed Monthly Payment</td><td className="py-1 text-right">${(app.loan_amount_requested / app.repayment_term_months).toFixed(2)}</td></tr>
                )}
                <tr className="font-semibold border-t-2 border-gray-300">
                  <td className="py-1">Net Surplus / (Deficit)</td>
                  <td className="py-1 text-right">
                    {app.monthly_income ? (() => {
                      const surplus = app.monthly_income - totalExpenses - totalDebt - (app.loan_amount_requested && app.repayment_term_months ? app.loan_amount_requested / app.repayment_term_months : 0);
                      return <span className={surplus < 0 ? 'text-red-600' : 'text-green-700'}>${surplus.toFixed(2)}</span>;
                    })() : '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          {/* Existing Debts */}
          {debts.length > 0 && (
            <section className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-3">Existing Debts</h2>
              <table className="w-full text-sm">
                <thead><tr className="border-b"><th className="text-left py-1 text-gray-600">Creditor</th><th className="text-right py-1 text-gray-600">Balance</th><th className="text-right py-1 text-gray-600">Mo. Payment</th></tr></thead>
                <tbody className="divide-y divide-gray-100">
                  {debts.map((d, i) => (
                    <tr key={i}><td className="py-1">{d.creditor}</td><td className="py-1 text-right">${(d.balance || 0).toLocaleString()}</td><td className="py-1 text-right">${(d.monthly_payment || 0).toFixed(2)}</td></tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* Documents */}
          <section className="bg-white rounded-lg border border-gray-200 p-4">
            <h2 className="font-semibold text-gray-800 mb-3">Documents ({(app.documents || []).length})</h2>
            {(app.documents || []).length > 0 && (
              <table className="w-full text-sm mb-4">
                <thead><tr className="border-b"><th className="text-left py-1 text-gray-600">Label</th><th className="text-left py-1 text-gray-600">File</th><th className="text-left py-1 text-gray-600">Credit Report</th></tr></thead>
                <tbody className="divide-y divide-gray-100">
                  {(app.documents || []).map(d => (
                    <tr key={d.id}>
                      <td className="py-1">{d.document_label}</td>
                      <td className="py-1 text-gray-500 text-xs">{d.filename}</td>
                      <td className="py-1">{d.is_credit_report ? '✓' : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <DocumentUpload applicationId={id} onUploadComplete={loadApp} />
          </section>

          {/* Latest Review */}
          {app.latest_review && (
            <section className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-gray-800">Latest Review</h2>
                <Link to={`/reviews/${app.latest_review.id}`} className="text-blue-600 hover:underline text-sm">
                  View Full Review →
                </Link>
              </div>
              <p className="text-xs text-gray-500 mb-2">Reviewed: {app.latest_review.reviewed_at?.substring(0, 10)}</p>
              {app.latest_review.ai_review_text && (
                <div className="bg-gray-50 border rounded p-3 text-sm max-h-48 overflow-y-auto whitespace-pre-wrap font-mono text-xs">
                  {app.latest_review.ai_review_text.substring(0, 500)}...
                </div>
              )}
            </section>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <section className="bg-white rounded-lg border border-gray-200 p-4 text-sm">
            <h2 className="font-semibold text-gray-800 mb-3">Applicant Info</h2>
            <div className="space-y-1 text-gray-600">
              <p>{app.address || 'No address'}</p>
              <p>{app.phone || 'No phone'}</p>
              <p>{app.email || 'No email'}</p>
              <p>Household size: {app.household_size || '—'}</p>
              <p>Employment: {app.employment_status || '—'}</p>
              <p>Employer: {app.employer || '—'}</p>
            </div>
          </section>

          <section className="bg-white rounded-lg border border-gray-200 p-4 text-sm">
            <h2 className="font-semibold text-gray-800 mb-2">Loan Request</h2>
            <div className="space-y-1 text-gray-600">
              <p><strong>Amount:</strong> ${(app.loan_amount_requested || 0).toLocaleString()}</p>
              <p><strong>Purpose:</strong> {app.loan_purpose_category}</p>
              <p><strong>Term:</strong> {app.repayment_term_months ? `${app.repayment_term_months} months` : '—'}</p>
              <p className="text-xs mt-2 text-gray-500">{app.loan_purpose_description}</p>
            </div>
          </section>

          {refs.length > 0 && (
            <section className="bg-white rounded-lg border border-gray-200 p-4 text-sm">
              <h2 className="font-semibold text-gray-800 mb-2">References</h2>
              {refs.map((r, i) => (
                <div key={i} className="text-gray-600 mb-2">
                  <p className="font-medium">{r.name}</p>
                  <p className="text-xs">{r.relationship} · {r.contact}</p>
                </div>
              ))}
            </section>
          )}

          <section className="bg-white rounded-lg border border-gray-200 p-4 text-sm">
            <h2 className="font-semibold text-gray-800 mb-2">Privacy Notice</h2>
            {app.privacy_notice_acknowledged
              ? <p className="text-green-700">✓ Acknowledged {app.privacy_notice_date?.substring(0, 10)} via {app.privacy_notice_method}</p>
              : <p className="text-red-600">✗ Not yet acknowledged</p>}
          </section>

          {app.staff_notes && (
            <section className="bg-white rounded-lg border border-gray-200 p-4 text-sm">
              <h2 className="font-semibold text-gray-800 mb-2">Staff Notes</h2>
              <p className="text-gray-600 text-xs">{app.staff_notes}</p>
            </section>
          )}
        </div>
      </div>

      {/* Decision Modal */}
      {showDecision && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg max-h-screen overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Record Committee Decision</h2>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Decision</label>
              <div className="flex gap-3">
                {['Approved', 'Denied', 'Withdrawn', 'Counteroffer'].map(d => (
                  <button
                    key={d}
                    onClick={() => setDecision(d)}
                    className={`px-3 py-1.5 rounded text-sm border ${decision === d ? 'bg-blue-700 text-white border-blue-700' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {decision === 'Denied' && (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Denial Reasons (select up to 4 — required for adverse action notice)</label>
                  <div className="space-y-1 max-h-40 overflow-y-auto border rounded p-2">
                    {DENIAL_REASONS.map(r => (
                      <label key={r} className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="checkbox"
                          checked={denialReasons.includes(r)}
                          onChange={() => toggleDenialReason(r)}
                          disabled={!denialReasons.includes(r) && denialReasons.length >= 4}
                        />
                        {r}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="flex items-center gap-2 text-sm cursor-pointer mb-3">
                    <input type="checkbox" checked={creditReportUsed} onChange={e => setCreditReportUsed(e.target.checked)} />
                    Credit report was a factor in this decision (FCRA § 615(a) notice required)
                  </label>
                  {creditReportUsed && (
                    <div className="space-y-2 ml-6">
                      <div><label className="text-xs text-gray-600">CRA Name</label><input className="w-full border rounded px-2 py-1 text-sm" value={craName} onChange={e => setCraName(e.target.value)} /></div>
                      <div><label className="text-xs text-gray-600">CRA Address</label><input className="w-full border rounded px-2 py-1 text-sm" value={craAddress} onChange={e => setCraAddress(e.target.value)} /></div>
                      <div><label className="text-xs text-gray-600">CRA Phone</label><input className="w-full border rounded px-2 py-1 text-sm" value={craPhone} onChange={e => setCraPhone(e.target.value)} /></div>
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleDecision}
                disabled={!decision || savingDecision}
                className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                {savingDecision ? 'Saving...' : 'Save Decision'}
              </button>
              <button
                onClick={() => setShowDecision(false)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 px-4 py-2 rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
