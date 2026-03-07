import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

export default function AdverseActionNotice() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);
  const [sentMethod, setSentMethod] = useState('mail');

  useEffect(() => {
    fetch(`/api/adverse-action/application/${id}`, { credentials: 'include' })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  const markAsSent = async () => {
    setMarking(true);
    try {
      await fetch(`/api/adverse-action/application/${id}/sent`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ method: sentMethod })
      });
      // Reload data
      const res = await fetch(`/api/adverse-action/application/${id}`, { credentials: 'include' });
      const d = await res.json();
      setData(d);
    } catch (err) {
      alert(err.message);
    } finally {
      setMarking(false);
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!data || !data.application) return (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
      {data?.error || 'Unable to generate notice. Ensure the application has been denied.'}
    </div>
  );

  const app = data.application;
  const noticeSent = app.adverse_action_notice_sent_at;

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <Link to={`/applications/${id}`} className="text-blue-600 hover:underline text-sm">← Back to Application</Link>
        <h1 className="text-xl font-bold text-gray-900 mt-2">Adverse Action Notice</h1>
        <p className="text-sm text-gray-500">Required by ECOA (12 CFR 1002) and FCRA (15 U.S.C. § 1681m)</p>
      </div>

      {/* Status Banner */}
      <div className={`mb-4 px-4 py-3 rounded border text-sm ${noticeSent ? 'bg-green-50 border-green-300 text-green-800' : 'bg-amber-50 border-amber-300 text-amber-800'}`}>
        {noticeSent ? (
          <span>✓ Notice sent on {noticeSent.substring(0, 10)} via {app.adverse_action_notice_method}</span>
        ) : (
          <span>⚠ Notice has not been sent. ECOA requires this notice be provided to the applicant. Review, then print and deliver.</span>
        )}
      </div>

      {/* Notice Preview */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-800">Notice Preview</h2>
          <a
            href={`/api/adverse-action/application/${id}/html`}
            target="_blank"
            rel="noreferrer"
            className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-1.5 rounded"
          >
            Open for Print / PDF
          </a>
        </div>
        <div
          className="border rounded p-4 overflow-auto max-h-96 text-sm"
          dangerouslySetInnerHTML={{ __html: data.noticeHTML }}
        />
      </div>

      {/* Denial Reasons Summary */}
      {(app.denial_reasons_json || []).length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <h2 className="font-semibold text-gray-800 mb-2">Denial Reasons on File</h2>
          <ol className="list-decimal list-inside text-sm space-y-1 text-gray-700">
            {app.denial_reasons_json.map((r, i) => <li key={i}>{r}</li>)}
          </ol>
        </div>
      )}

      {/* Mark as Sent */}
      {!noticeSent && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-800 mb-3">Mark Notice as Sent</h2>
          <p className="text-sm text-gray-600 mb-3">
            After delivering the notice to the applicant, record the delivery here for your records.
            ECOA requires tracking of when and how adverse action notices are delivered.
          </p>
          <div className="flex gap-3 items-end">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Delivery Method</label>
              <select
                value={sentMethod}
                onChange={e => setSentMethod(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1.5 text-sm"
              >
                <option value="mail">First-class mail</option>
                <option value="in-person">In-person</option>
                <option value="electronic">Electronic (email)</option>
              </select>
            </div>
            <button
              onClick={markAsSent}
              disabled={marking}
              className="bg-green-700 hover:bg-green-600 text-white px-4 py-1.5 rounded text-sm disabled:opacity-50"
            >
              {marking ? 'Saving...' : 'Mark as Sent'}
            </button>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-400 bg-gray-50 border rounded p-3">
        <strong>Record Retention:</strong> This notice and the application record must be retained for 25 months from the date of action per ECOA requirements (12 CFR 1002.12). Credit report data is subject to FCRA retention and disposal requirements.
      </div>
    </div>
  );
}
