import React from 'react';

export default function MemoPreview({ memoHTML, reviewId }) {
  const handlePrint = () => {
    const win = window.open(`/api/memos/review/${reviewId}/html`, '_blank');
    if (win) {
      win.addEventListener('load', () => win.print());
    }
  };

  if (!memoHTML) return null;

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-medium text-gray-700">Committee Memo Preview</h3>
        <button
          onClick={handlePrint}
          className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-1.5 rounded"
        >
          Print / Export PDF
        </button>
      </div>
      <div
        className="border rounded bg-white p-4 overflow-auto max-h-96 text-sm prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: memoHTML }}
      />
    </div>
  );
}
