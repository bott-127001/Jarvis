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

const confColor = (conf) => {
  if (conf === 'high' || (typeof conf === 'string' && conf.toLowerCase() === 'high')) return '#43a047';
  if (conf === 'medium' || (typeof conf === 'string' && conf.toLowerCase() === 'medium')) return '#ffa726';
  if (conf === 'low' || (typeof conf === 'string' && conf.toLowerCase() === 'low')) return '#e53935';
  return '#bbb';
};

export default function BiasIdentifier() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.bias;
  const style = analytics.style;
  const trap = analytics.trap;
  const reversal = analytics.reversal;
  const sr = analytics.sr;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No bias data.</div>;
  }

  // Helper to check if all values in an object are zero or undefined
  const isAllZeroOrMissing = obj => obj && Object.values(obj).every(v => !v || Math.abs(v) < 1e-6);

  const isBaseline = !!data.is_baseline;

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
                <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>{data.calls && data.calls[col.key] !== undefined ? data.calls[col.key] : '-'}</td>
              ))}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col => (
                <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>{data.puts && data.puts[col.key] !== undefined ? data.puts[col.key] : '-'}</td>
              ))}
            </tr>
            {/* Rolling 10-min Difference Row (always show) */}
            <tr style={{ background: '#232526' }}>
              <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>
                10-min 94
              </td>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>
                    {data.rolling_deltas && data.rolling_deltas[`call_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_deltas[`call_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2)
                      : '0.00'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>-</td>
                )
              )}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>
                    {data.rolling_deltas && data.rolling_deltas[`put_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_deltas[`put_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2)
                      : '0.00'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>-</td>
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
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>
                    {data.rolling_pct && data.rolling_pct[`call_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_pct[`call_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2) + '%'
                      : '0.00%'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>-</td>
                )
              )}
            </tr>
            <tr style={{ background: '#181a1b' }}>
              <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
              {columns.map(col =>
                ['volume', 'openInterest', 'iv'].includes(col.key) ? (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>
                    {data.rolling_pct && data.rolling_pct[`put_${col.key === 'openInterest' ? 'oi' : col.key}`] !== undefined
                      ? data.rolling_pct[`put_${col.key === 'openInterest' ? 'oi' : col.key}`].toFixed(2) + '%'
                      : '0.00%'}
                  </td>
                ) : (
                  <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13, color: '#fff' }}>-</td>
                )
              )}
            </tr>
          </tbody>
        </table>
        {/* Baseline info message */}
        {isBaseline && (
          <div style={{ color: '#ffa726', fontWeight: 500, marginTop: 10 }}>
            Baseline (first fetch) — rolling window will update as more data accumulates.
          </div>
        )}
      </div>
      {/* Classic Bias/Participant Table with spacing */}
      <div style={{ margin: '32px 0 32px 0', width: '100%', maxWidth: 500 }}>
        <table className="bias-table-participant" style={{ width: '100%', borderCollapse: 'collapse', background: '#232526', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflow: 'hidden', margin: '0 auto' }}>
          <thead>
            <tr>
              <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 15, padding: 10, textAlign: 'center', borderBottom: '1px solid #444' }}>Type</th>
              <th style={{ background: '#181a1b', color: '#61dafb', fontWeight: 700, fontSize: 15, padding: 10, textAlign: 'center', borderBottom: '1px solid #444' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 600, color: '#fff', padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>Call Bias</td>
              <td style={{ fontWeight: 500, color: '#fff', padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.call_participant || '-'}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 600, color: '#fff', padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>Put Bias</td>
              <td style={{ fontWeight: 500, color: '#fff', padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.put_participant || '-'}</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 700, color: '#61dafb', padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>Overall Sentiment</td>
              <td style={{ fontWeight: 700, color: biasColor(data.bias), padding: 10, textAlign: 'center', borderBottom: '1px solid #333' }}>{data.bias || '-'}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
} 