import React from 'react';

const data = [
  {
    leg: 'Call',
    detected: 'No',
    type: 'None',
    score: 0,
    confidence: 'Low',
    comment: 'No trap detected',
  },
  {
    leg: 'Put',
    detected: 'No',
    type: 'None',
    score: 0,
    confidence: 'Low',
    comment: 'No trap detected',
  },
];

const confidenceColor = (conf) => {
  if (conf === 'High') return '#43a047';
  if (conf === 'Medium') return '#ffa726';
  if (conf === 'Low') return '#43a047';
  return '#bbb';
};

export default function TrapDetectorIdentifier() {
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
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={row.leg}>
                <td className="trap-cell-leg">{row.leg}</td>
                <td className="trap-cell">{row.detected}</td>
                <td className="trap-cell">{row.type}</td>
                <td className="trap-cell">{row.score}</td>
                <td className="trap-cell-confidence" style={{ color: confidenceColor(row.confidence) }}>{row.confidence}</td>
                <td className="trap-cell">{row.comment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 