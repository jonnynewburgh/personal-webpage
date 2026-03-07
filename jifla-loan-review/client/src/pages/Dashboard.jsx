import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge.jsx';

export default function Dashboard() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/applications', { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setApplications(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const filtered = applications.filter(a =>
    a.applicant_name?.toLowerCase().includes(search.toLowerCase()) ||
    a.loan_purpose_category?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Application Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">{applications.length} total applications</p>
        </div>
        <Link
          to="/applications/new"
          className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium"
        >
          + New Application
        </Link>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name or purpose..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="border border-gray-300 rounded px-3 py-2 text-sm w-full max-w-md"
        />
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Loading applications...</p>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">No applications found.</p>
          <Link to="/applications/new" className="text-blue-600 hover:underline text-sm mt-2 block">
            Create the first application →
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Applicant</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Amount</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Purpose</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Review</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(app => (
                <tr key={app.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{app.applicant_name}</td>
                  <td className="px-4 py-3">
                    {app.loan_amount_requested
                      ? `$${app.loan_amount_requested.toLocaleString()}`
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{app.loan_purpose_category || '—'}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {app.created_at ? app.created_at.substring(0, 10) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={app.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {app.last_reviewed_at
                      ? `Reviewed ${app.last_reviewed_at.substring(0, 10)}`
                      : 'Not reviewed'}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/applications/${app.id}`}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Open →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
