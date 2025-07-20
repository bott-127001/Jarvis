import React from 'react';
import { useOptionChain } from './OptionChainContext';

const confidenceColor = (conf) => {
  if (conf === 'High') return '#43a047';
  if (conf === 'Medium') return '#ffa726';
  if (conf === 'Low') return '#e53935';
  return '#bbb';
};

export default function TrapDetectorIdentifier() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.trap;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No trap detector data.</div>;
  }

  const rows = [
    {
      leg: 'Call',
      detected: data.call?.trap_detected ? 'Yes' : 'No',
      type: data.call?.trap_type || '-',
      score: data.call?.deception_score ?? '-',
      confidence: data.call?.confidence_level || '-',
      comment: data.call?.comment || '-',
      trap_memory: data.call?.trap_memory ?? '-',
    },
    {
      leg: 'Put',
      detected: data.put?.trap_detected ? 'Yes' : 'No',
      type: data.put?.trap_type || '-',
      score: data.put?.deception_score ?? '-',
      confidence: data.put?.confidence_level || '-',
      comment: data.put?.comment || '-',
      trap_memory: data.put?.trap_memory ?? '-',
    },
  ];

  return (
    <div className="trap-root">
      <div className="trap-header">
        <div className="trap-title">Trap Detector</div>
        <div className="trap-subtitle">Real-Time Deception Scanner</div>
      </div>
      <div className="trap-card">
        <table className="trap-table">
          <thead>
            <tr>
              <th>Leg</th>
              <th>Trap Detected</th>
              <th>Trap Type</th>
              <th>Deception Score</th>
              <th>Confidence</th>
              <th>Trap Memory</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.leg}>
                <td className="trap-cell-leg">{row.leg}</td>
                <td className="trap-cell">{row.detected}</td>
                <td className="trap-cell">{row.type}</td>
                <td className="trap-cell">{row.score}</td>
                <td className="trap-cell-confidence" style={{ color: confidenceColor(row.confidence) }}>{row.confidence}</td>
                <td className="trap-cell">{row.trap_memory}</td>
                <td className="trap-cell">{row.comment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 