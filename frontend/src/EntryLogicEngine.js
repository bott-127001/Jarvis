import React from 'react';
import { useOptionChain } from './OptionChainContext';

const directionIcon = (dir) => {
  if (dir === 'long') return '🟢';
  if (dir === 'short') return '🔴';
  if (dir === 'avoid') return '⏸️';
  return '❓';
};
const directionColor = (dir) => {
  if (dir === 'long') return '#43a047';
  if (dir === 'short') return '#e53935';
  if (dir === 'avoid') return '#ffa726';
  return '#bbb';
};
const confColor = (conf) => {
  if (conf === 'high') return '#43a047';
  if (conf === 'medium') return '#ffa726';
  if (conf === 'low') return '#e53935';
  return '#bbb';
};

export default function EntryLogicEngine() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.entry;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No entry logic data.</div>;
  }

  // Main status
  const icon = directionIcon(data.entry_direction);
  const color = directionColor(data.entry_direction);
  const conf = data.confidence || '-';
  const confColorVal = confColor(conf);
  const tradeType = data.trade_type || '-';
  const entryScore = data.entry_score !== undefined ? data.entry_score : '-';

  // Module summary table (if available)
  const raw = data.raw_signals || {};
  const moduleTable = [
    {
      module: 'Bias Identifier',
      key: raw.bias?.bias || '-',
      confidence: '-',
      summary: raw.bias ? JSON.stringify(raw.bias) : '-',
    },
    {
      module: 'Market Style',
      key: raw.style?.market_style || '-',
      confidence: '-',
      summary: raw.style ? JSON.stringify(raw.style) : '-',
    },
    {
      module: 'Trap Detector',
      key: `Call: ${raw.trap?.call?.trap_type || '-'} (${raw.trap?.call?.confidence_level || '-'}) | Put: ${raw.trap?.put?.trap_type || '-'} (${raw.trap?.put?.confidence_level || '-'})`,
      confidence: `Call: ${raw.trap?.call?.confidence_level || '-'} | Put: ${raw.trap?.put?.confidence_level || '-'}`,
      summary: raw.trap ? JSON.stringify(raw.trap) : '-',
    },
    {
      module: 'Reversal Probability',
      key: raw.reversal?.reversal_type || '-',
      confidence: raw.reversal ? `${(raw.reversal.reversal_probability * 100).toFixed(0)}%` : '-',
      summary: raw.reversal ? JSON.stringify(raw.reversal) : '-',
    },
    {
      module: 'Support/Resistance',
      key: Array.isArray(raw.sr) && raw.sr.length > 0 ? `${raw.sr.length} zones` : '-',
      confidence: '-',
      summary: raw.sr ? JSON.stringify(raw.sr) : '-',
    },
  ];

  return (
    <div className="entry-root">
      {/* Main Status Card */}
      <div className="entry-status-card">
        <div className="entry-status-header">
          <span className="entry-status-icon">{icon}</span>
          <span className="entry-status-label" style={{ color }}>{data.entry_direction || '-'}</span>
        </div>
        <div className="entry-status-confidence">
          Confidence: <span style={{ color: confColorVal }}>{conf}</span>
        </div>
        <div className="entry-status-tradetype">
          Trade Type: <span>{tradeType}</span>
        </div>
        <div className="entry-status-score">
          Entry Score: <span>{entryScore}</span>
        </div>
        <div className="entry-status-zone">
          Entry Zone: <span>{data.entry_zone ? `${data.entry_zone.zone_type} @ ${data.entry_zone.zone_level} (${data.entry_zone.confidence})` : '-'}</span>
        </div>
        <div className="entry-status-mustavoid">
          Must Avoid: <span style={{ color: data.must_avoid ? '#e53935' : '#43a047' }}>{data.must_avoid ? 'Yes' : 'No'}</span>
        </div>
        <div className="entry-status-reason">
          Reason: <span>{data.reason}</span>
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