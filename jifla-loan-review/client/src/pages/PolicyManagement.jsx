import React, { useState, useEffect, useRef } from 'react';

export default function PolicyManagement() {
  const [policies, setPolicies] = useState([]);
  const [activePolicy, setActivePolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [purgingNow, setPurgingNow] = useState(false);
  const [purgeResult, setPurgeResult] = useState('');
  const fileRef = useRef(null);

  const loadPolicies = () => {
    Promise.all([
      fetch('/api/policies', { credentials: 'include' }).then(r => r.json()),
      fetch('/api/policies/active', { credentials: 'include' }).then(r => r.json()).catch(() => null)
    ]).then(([all, active]) => {
      setPolicies(all);
      setActivePolicy(active);
      setLoading(false);
    });
  };

  useEffect(() => { loadPolicies(); }, []);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) { setUploadError('Please select a file.'); return; }

    setUploadError('');
    setUploadSuccess('');
    setUploading(true);

    const formData = new FormData();
    formData.append('policy', file);

    try {
      const res = await fetch('/api/policies/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Upload failed');

      setUploadSuccess(`Policy v${data.version} uploaded successfully. ${Object.keys(data.structuredFields || {}).length} structured fields extracted.`);
      if (fileRef.current) fileRef.current.value = '';
      loadPolicies();
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const activatePolicy = async (policyId) => {
    const res = await fetch(`/api/policies/${policyId}/activate`, {
      method: 'PUT',
      credentials: 'include'
    });
    if (res.ok) loadPolicies();
  };

  const handleManualPurge = async () => {
    if (!confirm('Run manual data purge now? This will securely delete all records past their retention deadline. This action cannot be undone.')) return;

    setPurgingNow(true);
    setPurgeResult('');
    try {
      const res = await fetch('/api/applications', { credentials: 'include' });
      // Purge runs server-side on startup; for manual purge, call a dedicated endpoint
      // For now, just inform the user it runs automatically
      setPurgeResult('Purge service runs automatically on server startup and daily. Manual trigger not yet implemented via UI — restart the server to run immediately, or check server logs for last purge results.');
    } finally {
      setPurgingNow(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Loan Policy Management</h1>
      <p className="text-sm text-gray-500 mb-6">
        Upload and manage the JIFLA loan policy document. The active policy is used for all application reviews.
        Structured fields are extracted automatically by AI and used for rule-based checks.
      </p>

      {/* Active Policy */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Active Policy</h2>
        {activePolicy ? (
          <div className="text-sm">
            <p><strong>Version:</strong> {activePolicy.version}</p>
            <p><strong>File:</strong> {activePolicy.filename}</p>
            <p><strong>Uploaded:</strong> {activePolicy.uploaded_at?.substring(0, 10)}</p>
            {activePolicy.structured_fields && (
              <div className="mt-3">
                <p className="font-medium mb-1">Extracted Policy Fields:</p>
                <div className="bg-gray-50 border rounded p-3 text-xs max-h-48 overflow-y-auto">
                  <pre>{JSON.stringify(activePolicy.structured_fields, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded p-3 text-sm">
            <strong>No active policy found.</strong> Please upload the JIFLA loan policy document to begin reviewing applications.
            The policy document is required for AI-assisted review and rule-based compliance checks.
          </div>
        )}
      </section>

      {/* Upload New Policy */}
      <section className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Upload Policy Document</h2>
        <p className="text-sm text-gray-600 mb-3">
          Upload a PDF or Word document of the JIFLA loan policy. The system will extract the full text
          and automatically parse key policy fields. Uploading a new version will deactivate the current one.
        </p>

        <div className="flex gap-3 items-center">
          <input ref={fileRef} type="file" accept=".pdf,.docx,.doc" className="text-sm" />
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {uploading ? 'Uploading & Parsing...' : 'Upload Policy'}
          </button>
        </div>

        {uploadError && <p className="text-red-600 text-sm mt-2">{uploadError}</p>}
        {uploadSuccess && <p className="text-green-700 text-sm mt-2">✓ {uploadSuccess}</p>}
      </section>

      {/* Policy Versions */}
      {policies.length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
          <h2 className="font-semibold text-gray-800 mb-3">All Policy Versions</h2>
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="text-left pb-2 text-gray-600">Version</th>
                <th className="text-left pb-2 text-gray-600">Filename</th>
                <th className="text-left pb-2 text-gray-600">Uploaded</th>
                <th className="text-left pb-2 text-gray-600">Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {policies.map(p => (
                <tr key={p.id}>
                  <td className="py-2">v{p.version}</td>
                  <td className="py-2 text-gray-600 text-xs">{p.filename}</td>
                  <td className="py-2 text-gray-500">{p.uploaded_at?.substring(0, 10)}</td>
                  <td className="py-2">
                    {p.is_active
                      ? <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-medium">Active</span>
                      : <span className="text-gray-400 text-xs">Inactive</span>}
                  </td>
                  <td className="py-2">
                    {!p.is_active && (
                      <button
                        onClick={() => activatePolicy(p.id)}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        Activate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Data Retention & Purge */}
      <section className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-2">Data Retention & Purge</h2>
        <div className="text-sm text-gray-600 space-y-1 mb-4">
          <p><strong>Credit reports:</strong> Deleted 90 days after application closes (FCRA disposal rule)</p>
          <p><strong>PII documents:</strong> Source files deleted 1 year after application closes</p>
          <p><strong>Application records:</strong> PII purged 3 years after application closes</p>
          <p className="text-xs text-gray-400 mt-2">Purge service runs automatically on server startup and daily. All purge events are logged (without PII).</p>
        </div>

        <button
          onClick={handleManualPurge}
          disabled={purgingNow}
          className="border border-red-300 text-red-700 hover:bg-red-50 px-4 py-2 rounded text-sm disabled:opacity-50"
        >
          {purgingNow ? 'Running Purge...' : 'Run Manual Purge'}
        </button>

        {purgeResult && (
          <div className="mt-3 bg-gray-50 border rounded p-3 text-xs text-gray-600">
            {purgeResult}
          </div>
        )}
      </section>
    </div>
  );
}
