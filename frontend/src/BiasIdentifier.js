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

      {/* Module Summary Table with extra margin below */}
      <div className="entry-table-card" style={{ margin: '32px 0 0 0', overflowX: 'auto' }}>
        <table className="entry-table" style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, minWidth: 700 }}>
          <thead>
            <tr>
              <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 16 }}>Module</th>
              <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 16 }}>Key Output</th>
              <th style={{ padding: '10px 8px', textAlign: 'right', fontSize: 16, width: 120 }}>Confidence/Score</th>
              <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 16 }}>Summary</th>
            </tr>
          </thead>
          <tbody>
            {[
              {
                module: 'Bias Identifier',
                key: <span style={{ color: biasColor(data.bias), fontWeight: 700 }}>{data.bias || 'No bias'}</span>,
                confidence: data.ml_confidence !== undefined ? (data.ml_confidence * 100).toFixed(1) + '%' : '-',
                summary: (
                  <div>
                    <div>Δ: {data.rolling_deltas ? Object.entries(data.rolling_deltas).map(([k, v]) => `${k}: ${v.toFixed(2)}`).join(', ') : '-'}</div>
                    <div>%: {data.rolling_pct ? Object.entries(data.rolling_pct).map(([k, v]) => `${k}: ${v.toFixed(2)}%`).join(', ') : '-'}</div>
                  </div>
                ),
              },
              {
                module: 'Market Style',
                key: style?.market_style || '-',
                confidence: style?.ml_confidence !== undefined ? (style.ml_confidence * 100).toFixed(1) + '%' : '-',
                summary: style ? (
                  <div style={{ fontSize: 12, color: '#bbb' }}>
                    {['price_direction', 'oi_diff', 'vol_diff', 'iv_diff'].map(k => `${k}: ${style[k]}`).join(', ')}
                  </div>
                ) : '-',
              },
              {
                module: 'Trap Detector',
                key: `Call: ${trap?.call?.trap_type || '-'} (${trap?.call?.confidence_level || '-'}) | Put: ${trap?.put?.trap_type || '-'} (${trap?.put?.confidence_level || '-'})`,
                confidence: `Call: ${trap?.call?.confidence_level || '-'} | Put: ${trap?.put?.confidence_level || '-'}`,
                summary: (
                  <div style={{ fontSize: 12, color: '#bbb' }}>
                    Call deception: {trap?.call?.deception_score ?? '-'}, Put deception: {trap?.put?.deception_score ?? '-'}<br/>
                    Call memory: {trap?.call?.trap_memory ?? '-'}, Put memory: {trap?.put?.trap_memory ?? '-'}
                  </div>
                ),
              },
              {
                module: 'Reversal Probability',
                key: reversal?.reversal_type || '-',
                confidence: reversal?.reversal_probability !== undefined ? (reversal.reversal_probability * 100).toFixed(0) + '%' : '-',
                summary: reversal ? (
                  <div style={{ fontSize: 12, color: '#bbb' }}>
                    Prob: {reversal.reversal_probability !== undefined ? (reversal.reversal_probability * 100).toFixed(0) + '%' : '-'}, Bias flips: {reversal.bias_cluster_flipped ? 'Yes' : 'No'}, IV/OI flip: {reversal.iv_oi_support_flip ? 'Yes' : 'No'}
                  </div>
                ) : '-',
              },
              {
                module: 'Support/Resistance',
                key: Array.isArray(sr) && sr.length > 0 ? `${sr.length} zones` : '-',
                confidence: '-',
                summary: Array.isArray(sr) && sr.length > 0 ? (
                  <div style={{ fontSize: 12, color: '#bbb' }}>
                    {sr.filter(z => z.zone_state === 'Active').map(z => `${z.zone_type} @ ${z.zone_level} (${z.bias_suggestion}, ${z.confidence})`).join('; ') || 'No active zones'}
                  </div>
                ) : '-',
              },
            ].map((row, i) => (
              <tr key={row.module} style={{ borderBottom: '1px solid #444', background: i % 2 === 0 ? '#232526' : '#181a1b' }}>
                <td className="entry-table-module" style={{ padding: '10px 14px', fontWeight: 700, color: '#61dafb', verticalAlign: 'top' }}>{row.module}</td>
                <td className="entry-table-key" style={{ padding: '10px 14px', verticalAlign: 'top', fontWeight: 600 }}>{row.key}</td>
                <td className="entry-table-confidence" style={{ padding: '10px 8px', textAlign: 'right', fontWeight: 600, color: '#ffa726', verticalAlign: 'top' }}>{row.confidence}</td>
                <td className="entry-table-summary" style={{ padding: '10px 14px', verticalAlign: 'top', fontSize: 14 }}>
                  {typeof row.summary === 'string' ? row.summary : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {React.Children.toArray(
                        typeof row.summary === 'object' && row.summary.props && row.summary.props.children
                          ? (Array.isArray(row.summary.props.children) ? row.summary.props.children : [row.summary.props.children])
                          : []
                      ).map((item, idx) => (
                        <div key={idx} style={{ color: '#bbb', fontSize: 14 }}>{item}</div>
                      ))}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 