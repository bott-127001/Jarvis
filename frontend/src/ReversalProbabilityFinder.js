import React from 'react';
import { useOptionChain } from './OptionChainContext';

export default function ReversalProbabilityFinder() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.reversal;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No reversal probability data.</div>;
  }

  const left = [
    { label: 'Bias Flip Cluster', value: data.bias_cluster_flipped ? 'Yes' : 'No' },
    { label: 'Price vs Bias Conflict', value: data.price_vs_bias_conflict ? 'Yes' : 'No' },
    { label: 'Structural Context', value: data.structural_context || '-' },
    { label: 'Market Style', value: data.market_style || '-' },
  ];
  const right = [
    { label: 'IV/OI Support Flip', value: data.iv_oi_support_flip ? 'Yes' : 'No' },
    { label: 'Liquidity OK', value: data.liquidity_ok ? 'Yes' : 'No' },
    { label: 'Volatility Phase', value: data.volatility_phase || '-' },
    { label: 'Trap Detected', value: data.trap_detected ? 'Yes' : 'No' },
  ];

  return (
    <div className="reversal-root">
      <div className="reversal-header">
        <div className="reversal-title">{(data.reversal_probability * 100).toFixed(0)}%</div>
        <div className="reversal-subtitle">Reversal Probability</div>
        {data.reversal_type && (
          <div className="reversal-type">Type: <b>{data.reversal_type}</b></div>
        )}
      </div>
      <div className="reversal-card">
        <table className="reversal-table">
          <tbody>
            {left.map((row, i) => (
              <tr key={row.label}>
                <td className="reversal-label">{row.label}</td>
                <td className="reversal-value">{row.value}</td>
                <td className="reversal-gap"></td>
                <td className="reversal-label">{right[i].label}</td>
                <td className="reversal-value">{right[i].value}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="reversal-summary">{data.reasoning}</div>
      </div>
    </div>
  );
} 