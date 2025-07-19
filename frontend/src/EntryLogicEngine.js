import React from 'react';

const mainStatus = {
  icon: '⏸️',
  label: 'Avoid',
  color: '#ffa726',
  confidence: 'LOW',
  reason: 'No clear directional edge or traps detected.',
};

const moduleTable = [
  {
    module: 'Bias Identifier',
    key: 'Sideways (Neutral / Noise/Neutral / Noise)',
    confidence: 'High',
    summary: '-',
  },
  {
    module: 'Market Style',
    key: 'Sideways',
    confidence: 'High',
    summary: '-',
  },
  {
    module: 'Trap Detector',
    key: 'Call: None (Low) | Put: None (Low)',
    confidence: 'Call: Low | Put: Low',
    summary: '-',
  },
  {
    module: 'Reversal Probability',
    key: 'No reversal',
    confidence: '10%',
    summary: '-',
  },
  {
    module: 'Support/Resistance',
    key: 'No data',
    confidence: '-',
    summary: '-',
  },
];

export default function EntryLogicEngine() {
  return (
    <div className="entry-root">
      {/* Main Status Card */}
      <div className="entry-status-card">
        <div className="entry-status-header">
          <span className="entry-status-icon">{mainStatus.icon}</span>
          <span className="entry-status-label" style={{ color: mainStatus.color }}>{mainStatus.label}</span>
        </div>
        <div className="entry-status-confidence">
          Confidence: <span style={{ color: mainStatus.color }}>{mainStatus.confidence}</span>
        </div>
        <div className="entry-status-reason">
          Reason: <span>{mainStatus.reason}</span>
        </div>
      </div>
      {/* Module Table Card */}
      <div className="entry-table-card">
        <table className="entry-table">
          <thead>
            <tr>
              <th>Module</th>
              <th>Key Output</th>
              <th>Confidence/Score</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {moduleTable.map((row, i) => (
              <tr key={row.module}>
                <td className="entry-table-module">{row.module}</td>
                <td className="entry-table-key">{row.key}</td>
                <td className="entry-table-confidence">{row.confidence}</td>
                <td className="entry-table-summary">{row.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 