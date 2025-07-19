import React from 'react';

const data = {
  probability: 0,
  left: [
    { label: 'Bias Flip Cluster', value: 'No' },
    { label: 'Price vs Bias Conflict', value: 'No' },
    { label: 'Structural Context', value: 'trend_continuation' },
  ],
  right: [
    { label: 'IV/OI Support Flip', value: 'No' },
    { label: 'Liquidity OK', value: 'No' },
    { label: 'Volatility Phase', value: 'normal' },
  ],
  summary: 'Bias flips: 0, IV/OI flip: False, Price vs Bias: False, Liquidity: False, Volatility: normal, Context: trend_continuation',
};

export default function ReversalProbabilityFinder() {
  return (
    <div className="reversal-root">
      <div className="reversal-header">
        <div className="reversal-title">{data.probability}%</div>
        <div className="reversal-subtitle">Reversal Probability</div>
      </div>
      <div className="reversal-card">
        <table className="reversal-table">
          <tbody>
            {data.left.map((row, i) => (
              <tr key={row.label}>
                <td className="reversal-label">{row.label}</td>
                <td className="reversal-value">{row.value}</td>
                <td className="reversal-gap"></td>
                <td className="reversal-label">{data.right[i].label}</td>
                <td className="reversal-value">{data.right[i].value}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="reversal-summary">{data.summary}</div>
      </div>
    </div>
  );
} 