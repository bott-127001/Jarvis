import React from 'react';
import { useOptionChain } from './OptionChainContext';

const styleColor = (style) => {
  if (style === 'Trending') return '#43a047';
  if (style === 'Ranging') return '#ffa726';
  if (style === 'Volatile') return '#e53935';
  return '#bbb';
};

export default function MarketStyleIdentifier() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.style;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No market style data.</div>;
  }

  return (
    <div className="marketstyle-root">
      {!fetching && (
        <div className="marketstyle-warning">
          <b>Warning:</b> Data is not updating (fetching stopped). Showing last known results.
        </div>
      )}
      <div className="marketstyle-card">
        <div className="marketstyle-header-row">
          <div className="marketstyle-style">Market Style: {data.market_style || '-'}</div>
          <div className="marketstyle-regime">Regime: <b>{data.regime || '-'}</b></div>
        </div>
        <div className="marketstyle-vol-row">
          <div>Volatility: <b>{data.volatility || '-'}</b></div>
          <div>ATR: <b>{data.atr || '-'}</b></div>
        </div>
      </div>
      {/* Key Metrics Table */}
      {(data.metrics || data.key_metrics) && (
        <div className="marketstyle-table-wrapper">
          <table className="marketstyle-table">
            <thead>
              <tr>
                <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Metric</th>
                <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.metrics || data.key_metrics || {}).map(([k, v]) => (
                <tr key={k}>
                  <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{k}</td>
                  <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 