import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReviewChecklist from '../components/ReviewChecklist.jsx';
import MemoPreview from '../components/MemoPreview.jsx';

export default function ReviewResults() {
  const { reviewId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [memoData, setMemoData] = useState(null);
  const [loadingMemo, setLoadingMemo] = useState(false);
  const [activeTab, setActiveTab] = useState('rules');

  useEffect(() => {
    fetch(`/api/memos/review/${reviewId}`, { credentials: 'include' })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [reviewId]);

  const generateMemo = async () => {
    setLoadingMemo(true);
    setMemoData(data?.memoHTML || null);
    setActiveTab('memo');
    setLoadingMemo(false);
  };

  if (loading) return <p className="text-gray-500">Loading review...</p>;
  if (!data) return <p className="text-red-500">Review not found.</p>;

  const { review, application: app, documents, memoHTML } = data;

  const fails = (review.rule_check_results || []).filter(r => r.status === 'fail').length;
  const warns = (review.rule_check_results || []).filter(r => r.status === 'warn').length;

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link to={`/applications/${app.id}`} className="text-blue-600 hover:underline text-sm">← Back to Application</Link>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Review Results: {app.applicant_name}</h1>
          <p className="text-sm text-gray-500">Review conducted: {review.reviewed_at?.substring(0, 16)} · Application #{app.id}</p>
        </div>
        <div className="flex gap-2">
          {fails > 0 && (
            <span className="bg-red-100 text-red-700 px-3 py-1 rounded text-sm font-medium">
              {fails} Failure{fails !== 1 ? 's' : ''}
            </span>
          )}
          {warns > 0 && (
            <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded text-sm font-medium">
              {warns} Warning{warns !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {[
          { key: 'rules', label: 'Rule Checks' },
          { key: 'ai', label: 'AI Analysis' },
          { key: 'memo', label: 'Committee Memo' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); if (tab.key === 'memo' && !memoData) generateMemo(); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === tab.key ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Rule Checks Tab */}
      {activeTab === 'rules' && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Layer 1 — Rule-Based Policy Checks</h2>
          <ReviewChecklist results={review.rule_check_results || []} />
        </div>
      )}

      {/* AI Analysis Tab */}
      {activeTab === 'ai' && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-semibold text-gray-800">Layer 2 — AI Review Analysis</h2>
              <p className="text-xs text-gray-500 mt-1">
                AI review was conducted using Claude (Anthropic). This is a staff tool to assist review —
                all decisions are made exclusively by the loan committee.
                PII was filtered and credit report data was summarized before sending to the API.
              </p>
            </div>
          </div>
          {review.ai_review_text ? (
            <div className="bg-gray-50 border border-gray-200 rounded p-4 whitespace-pre-wrap text-sm leading-relaxed">
              {review.ai_review_text}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No AI review available.</p>
          )}
        </div>
      )}

      {/* Memo Tab */}
      {activeTab === 'memo' && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Committee Summary Memo</h2>
            <a
              href={`/api/memos/review/${reviewId}/html`}
              target="_blank"
              rel="noreferrer"
              className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-1.5 rounded"
            >
              Open for Print / PDF Export
            </a>
          </div>
          {loadingMemo ? (
            <p className="text-gray-500 text-sm">Generating memo...</p>
          ) : (
            <MemoPreview memoHTML={memoHTML} reviewId={reviewId} />
          )}
        </div>
      )}

      {/* Quick Financial Summary */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2 text-sm">Quick Financial Summary</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-blue-600 text-xs">Monthly Income</p>
            <p className="font-semibold">${(app.monthly_income || 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-blue-600 text-xs">Loan Requested</p>
            <p className="font-semibold">${(app.loan_amount_requested || 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-blue-600 text-xs">Term</p>
            <p className="font-semibold">{app.repayment_term_months ? `${app.repayment_term_months} months` : '—'}</p>
          </div>
        </div>
      </div>

      {/* ECOA Decision Timeline Reminder */}
      <div className="mt-4 bg-amber-50 border border-amber-200 rounded p-3 text-xs text-amber-800">
        <strong>ECOA Reminder:</strong> Under the Equal Credit Opportunity Act, JIFLA must notify the applicant of the
        committee's decision within 30 days of receiving a complete application. If the application is denied,
        an adverse action notice must be provided.
      </div>
    </div>
  );
}
