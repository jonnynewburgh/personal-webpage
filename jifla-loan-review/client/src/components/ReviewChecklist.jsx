import React from 'react';

const icons = {
  pass: '✓',
  fail: '✗',
  warn: '⚠'
};

const colors = {
  pass: 'text-green-700 bg-green-50 border-green-200',
  fail: 'text-red-700 bg-red-50 border-red-200',
  warn: 'text-yellow-700 bg-yellow-50 border-yellow-200'
};

export default function ReviewChecklist({ results }) {
  if (!results || results.length === 0) {
    return <p className="text-gray-500 text-sm">No rule checks available.</p>;
  }

  const passes = results.filter(r => r.status === 'pass').length;
  const fails = results.filter(r => r.status === 'fail').length;
  const warns = results.filter(r => r.status === 'warn').length;

  return (
    <div>
      <div className="flex gap-4 mb-3 text-sm">
        <span className="text-green-700 font-medium">✓ {passes} Pass</span>
        <span className="text-red-700 font-medium">✗ {fails} Fail</span>
        <span className="text-yellow-700 font-medium">⚠ {warns} Warning</span>
      </div>
      <div className="space-y-2">
        {results.map((r, i) => (
          <div key={i} className={`border rounded px-3 py-2 text-sm flex gap-3 ${colors[r.status] || 'bg-gray-50'}`}>
            <span className="font-bold text-base leading-5">{icons[r.status]}</span>
            <div>
              <div className="font-medium">{r.check}</div>
              <div className="text-xs opacity-80 mt-0.5">{r.detail}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
