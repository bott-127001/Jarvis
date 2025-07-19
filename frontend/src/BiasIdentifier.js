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
            {/* Difference Row */}
            {data.diff_calls && data.diff_puts && (
              <>
                <tr style={{ background: '#232526' }}>
                  <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>
                    Difference vs 9:15 AM
                  </td>
                  <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
                  {columns.map(col => (
                    <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.diff_calls[col.key] !== undefined ? data.diff_calls[col.key].toFixed(2) : '-'}</td>
                  ))}
                </tr>
                <tr style={{ background: '#181a1b' }}>
                  <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
                  {columns.map(col => (
                    <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.diff_puts[col.key] !== undefined ? data.diff_puts[col.key].toFixed(2) : '-'}</td>
                  ))}
                </tr>
              </>
            )}
            {/* Percentage Change Row */}
            {data.pct_calls && data.pct_puts && (
              <>
                <tr style={{ background: '#232526' }}>
                  <td rowSpan={2} style={{ fontWeight: 700, color: '#fff', padding: 4, fontSize: 16, textAlign: 'center', background: '#232526', borderRight: '1px solid #444', borderBottom: '1px solid #333', verticalAlign: 'middle' }}>
                    % Change vs 9:15 AM
                  </td>
                  <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Call</td>
                  {columns.map(col => (
                    <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.pct_calls[col.key] !== undefined ? data.pct_calls[col.key].toFixed(2) + '%' : '-'}</td>
                  ))}
                </tr>
                <tr style={{ background: '#181a1b' }}>
                  <td style={{ fontWeight: 600, color: '#61dafb', padding: 4 }}>Put</td>
                  {columns.map(col => (
                    <td key={col.key} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{data.pct_puts[col.key] !== undefined ? data.pct_puts[col.key].toFixed(2) + '%' : '-'}</td>
                  ))}
                </tr>
              </>
            )}
          </tbody>
        </table>
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