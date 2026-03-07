import React from 'react';

const statusColors = {
  Draft: 'bg-gray-100 text-gray-700',
  'Under Review': 'bg-yellow-100 text-yellow-800',
  Reviewed: 'bg-blue-100 text-blue-800',
  Approved: 'bg-green-100 text-green-800',
  Denied: 'bg-red-100 text-red-800',
  Withdrawn: 'bg-gray-200 text-gray-600',
  Counteroffer: 'bg-purple-100 text-purple-800'
};

export default function StatusBadge({ status }) {
  const cls = statusColors[status] || 'bg-gray-100 text-gray-700';
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
