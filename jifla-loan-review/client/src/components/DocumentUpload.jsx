import React, { useState, useRef } from 'react';

const DOCUMENT_LABELS = [
  'Pay Stub',
  'Bank Statement',
  'Tax Return',
  'Lease / Rental Agreement',
  'Medical Bill',
  'Government ID',
  'Employment Verification Letter',
  'Credit Report',
  'Utility Bill',
  'Letter of Explanation',
  'Other'
];

export default function DocumentUpload({ applicationId, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [label, setLabel] = useState('Pay Stub');
  const [isCreditReport, setIsCreditReport] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef(null);

  const handleLabelChange = (e) => {
    const val = e.target.value;
    setLabel(val);
    setIsCreditReport(val === 'Credit Report');
  };

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setError('Please select a file.');
      return;
    }

    setError('');
    setUploading(true);

    const formData = new FormData();
    formData.append('document', file);
    formData.append('document_label', label);
    formData.append('is_credit_report', isCreditReport ? 'true' : 'false');

    try {
      const res = await fetch(`/api/documents/upload/${applicationId}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Upload failed');

      if (fileRef.current) fileRef.current.value = '';
      onUploadComplete && onUploadComplete(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="border border-dashed border-gray-300 rounded p-4 bg-gray-50">
      <h3 className="font-medium text-sm text-gray-700 mb-3">Upload Document</h3>
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Document Type</label>
          <select
            value={label}
            onChange={handleLabelChange}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
          >
            {DOCUMENT_LABELS.map(l => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">File (PDF, Word, JPG, PNG)</label>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.jpg,.jpeg,.png" className="text-sm" />
        </div>
        {label === 'Credit Report' && (
          <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            <span>⚠</span>
            <span>Credit report text will be summarized only — raw text not retained per FCRA policy.</span>
          </div>
        )}
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-1.5 rounded text-sm disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
    </div>
  );
}
