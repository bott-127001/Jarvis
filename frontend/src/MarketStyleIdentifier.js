import React from 'react';
import { useOptionChain } from './OptionChainContext';

const styleColor = (style) => {
  if (style && style.toLowerCase().includes('trend')) return '#43a047';
  if (style && style.toLowerCase().includes('range')) return '#ffa726';
  if (style && style.toLowerCase().includes('volatile')) return '#e53935';
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
          <div className="marketstyle-style" style={{ color: styleColor(data.market_style), fontWeight: 700, fontSize: 18 }}>
            Market Style: {data.market_style || '-'}
          </div>
          <div className="marketstyle-volstate">
            Volatility: <b>{data.volatility_state || '-'}</b>
          </div>
        </div>
        <div className="marketstyle-info-row">
          <div>Price Direction: <b>{data.price_direction || '-'}</b></div>
          <div>Trend Strength: <b>{data.spot_trend_strength !== undefined ? data.spot_trend_strength.toFixed(2) : '-'}</b></div>
        </div>
        <div className="marketstyle-info-row">
          <div>Baseline Used: <b>{data.baseline_used || '-'}</b></div>
          <div>Mode: <b>{data.mode || '-'}</b></div>
        </div>
        <div className="marketstyle-info-row">
          <div>Total Volume: <b>{data.total_volume !== undefined ? data.total_volume : '-'}</b></div>
          <div>Total OI: <b>{data.total_oi !== undefined ? data.total_oi : '-'}</b></div>
        </div>
      </div>
      {/* Key Metrics Table */}
      <div className="marketstyle-table-wrapper">
        <table className="marketstyle-table">
          <thead>
            <tr>
              <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Metric</th>
              <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>OI Diff (CE-PE)</td>
              <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.oi_diff !== undefined ? data.oi_diff.toFixed(2) : '-'}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>Volume Diff (CE-PE)</td>
              <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.vol_diff !== undefined ? data.vol_diff.toFixed(2) : '-'}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>IV Diff (CE-PE)</td>
              <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.iv_diff !== undefined ? data.iv_diff.toFixed(2) : '-'}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
} 