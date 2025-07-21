import React from 'react';
import { useOptionChain } from './OptionChainContext';

const columns = [
  { key: 'volume', label: 'Volume' },
  { key: 'openInterest', label: 'OI' },
  { key: 'bidQty', label: 'Bid Qty' },
  { key: 'askQty', label: 'Ask Qty' },
  { key: 'bidPrice', label: 'Bid Price' },
  { key: 'askPrice', label: 'Ask Price' },
  { key: 'iv', label: 'IV' },
  { key: 'theta', label: 'Theta' },
  { key: 'vega', label: 'Vega' },
  { key: 'gamma', label: 'Gamma' },
];

const biasColor = (bias) => {
  if (bias === 'Bullish') return '#43a047';
  if (bias === 'Bearish') return '#e53935';
  if (bias === 'Sideways') return '#ffa726';
  return '#bbb';
};

export default function BiasIdentifier() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.bias;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No bias data.</div>;
  }

  // Helper to check if all values in an object are zero or undefined
  const isAllZeroOrMissing = obj => obj && Object.values(obj).every(v => !v || Math.abs(v) < 1e-6);

  const showRollingDeltas = data.rolling_deltas !== undefined;
  const showRollingPct = data.rolling_pct !== undefined;
  const deltasAreBaseline = isAllZeroOrMissing(data.rolling_deltas);
  const pctAreBaseline = isAllZeroOrMissing(data.rolling_pct);

  return (
    <div className="bias-root">
      {!fetching && (
        <div className="bias-warning">
          <b>Warning:</b> Data is not updating (fetching stopped). Showing last known results.
        </div>
      )}
      <div className="bias-table-wrapper">
        <table className="bias-table-main">
          <thead>
            <tr>
              <th style={{ background: '#232526', color: '#fff', fontWeight: 700, fontSize: 12, padding: 4, textAlign: 'center', borderBottom: '1px solid #444' }}></th>
              <th style={{ background: '#232526', color: '#fff', fontWeight: 700, fontSize: 12, padding: 4, textAlign: 'center', borderBottom: '1px solid #444' }}></th>
              {columns.map(col => (
                <th key={col.key} style={{ background: '#232526', color: '#61dafb', padding: 4, borderBottom: '1px solid #444', fontWeight: 600, fontSize: 12 }}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Totals */}
            <tr style={{ background: '#232526' }}>
              <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>Totals</td>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
              {columns.map(col => (
                <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.calls && data.calls[col.key] !== undefined ? data.calls[col.key] : '-'}</td>
              ))}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col => (
                <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.puts && data.puts[col.key] !== undefined ? data.puts[col.key] : '-'}</td>
              ))}
            </tr>
            {/* Rolling 10-min Difference Row (always show) */}
            <tr style={{ background: '#232526' }}>
              <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>
                10-min Δ
              </td>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>
                    {showRollingDeltas && data.rolling_deltas && data.rolling_deltas[`call_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_deltas[`call_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2)
                      : '-'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>-</td>
                )
              )}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>
                    {showRollingDeltas && data.rolling_deltas && data.rolling_deltas[`put_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_deltas[`put_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2)
                      : '-'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>-</td>
                )
              )}
            </tr>
            {/* Rolling 10-min % Change Row (always show) */}
            <tr style={{ background: '#232526' }}>
              <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>
                10-min %
              </td>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>
                    {showRollingPct && data.rolling_pct && data.rolling_pct[`call_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_pct[`call_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2) + '%'
                      : '-'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>-</td>
                )
              )}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>
                    {showRollingPct && data.rolling_pct && data.rolling_pct[`put_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_pct[`put_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2) + '%'
                      : '-'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>-</td>
                )
              )}
            </tr>
          </tbody>
        </table>
        {/* Rolling window info message */}
        {(!showRollingDeltas || !showRollingPct) && (
          <div style={{ color: '#ffa726', fontWeight: 500, marginTop: 10 }}>
            Waiting for rolling window data (need 10 minutes of history). Showing baseline values.
          </div>
        )}
        {(deltasAreBaseline && pctAreBaseline && showRollingDeltas && showRollingPct) && (
          <div style={{ color: '#ffa726', fontWeight: 500, marginTop: 10 }}>
            Baseline (first fetch) — rolling window will update as more data accumulates.
          </div>
        )}
      </div>
      {/* Participant & Bias Table */}
      {(data.call_participant || data.put_participant || data.bias) && (
        <div className="bias-participant-table-wrapper">
          <table className="bias-table-participant">
            <thead>
              <tr>
                <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Type</th>
                <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 14, padding: 6, textAlign: 'center', borderBottom: '1px solid #444' }}>Participant</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>Call</td>
                <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.call_participant || '-'}</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>Put</td>
                <td style={{ fontWeight: 500, color: '#fff', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.put_participant || '-'}</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: '#61dafb', padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>Bias</td>
                <td style={{ fontWeight: 700, color: biasColor(data.bias), padding: 6, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.bias || '-'}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 