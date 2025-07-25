import React from 'react';
import { useOptionChain } from './OptionChainContext';

const directionIcon = (dir) => {
  if (dir === 'long') return '🟢';
  if (dir === 'short') return '🔴';
  if (dir === 'avoid') return '⏸️';
  return '❓';
};
const directionColor = (dir) => {
  if (dir === 'long') return '#43a047';
  if (dir === 'short') return '#e53935';
  if (dir === 'avoid') return '#ffa726';
  return '#bbb';
};
const confColor = (conf) => {
  if (conf === 'high') return '#43a047';
  if (conf === 'medium') return '#ffa726';
  if (conf === 'low') return '#e53935';
  return '#bbb';
};

const biasColor = (bias) => {
  if (bias === 'Bullish') return '#43a047';
  if (bias === 'Bearish') return '#e53935';
  if (bias === 'Sideways') return '#ffa726';
  return '#bbb';
};

export default function EntryLogicEngine() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.entry;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No entry logic data.</div>;
  }

  // Main status
  const icon = directionIcon(data.entry_direction);
  const color = directionColor(data.entry_direction);
  const conf = data.confidence || '-';
  const confColorVal = confColor(conf);
  const tradeType = data.trade_type || '-';
  const entryScore = data.entry_score !== undefined ? data.entry_score : '-';

  // Module summary table (if available)
  const raw = data.raw_signals || {};
  const biasVal = raw.bias?.bias || '-';
  const biasWarn = !['Bullish', 'Bearish', 'Sideways'].includes(biasVal);
  const biasDeltas = raw.bias?.rolling_deltas;
  const biasPct = raw.bias?.rolling_pct;
  const biasConf = raw.bias?.ml_confidence !== undefined ? (raw.bias.ml_confidence * 100).toFixed(1) + '%' : '-';

  const marketStyle = raw.style?.market_style || '-';
  const marketConf = raw.style?.ml_confidence !== undefined ? (raw.style.ml_confidence * 100).toFixed(1) + '%' : '-';
  const marketSummary = raw.style ? (
    <div style={{ fontSize: 12, color: '#bbb' }}>
      {['price_direction', 'oi_diff', 'vol_diff', 'iv_diff'].map(k => `${k}: ${raw.style[k]}`).join(', ')}
    </div>
  ) : '-';

  const trapCall = raw.trap?.call;
  const trapPut = raw.trap?.put;
  const trapKey = `Call: ${trapCall?.trap_type || '-'} (${trapCall?.confidence_level || '-'}) | Put: ${trapPut?.trap_type || '-'} (${trapPut?.confidence_level || '-'})`;
  const trapConf = `Call: ${trapCall?.confidence_level || '-'} | Put: ${trapPut?.confidence_level || '-'}`;
  const trapSummary = (
    <div style={{ fontSize: 12, color: '#bbb' }}>
      Call deception: {trapCall?.deception_score ?? '-'}, Put deception: {trapPut?.deception_score ?? '-'}<br/>
      Call memory: {trapCall?.trap_memory ?? '-'}, Put memory: {trapPut?.trap_memory ?? '-'}
    </div>
  );

  const reversalType = raw.reversal?.reversal_type || '-';
  const reversalConf = raw.reversal?.reversal_probability !== undefined ? (raw.reversal.reversal_probability * 100).toFixed(0) + '%' : '-';
  const reversalSummary = raw.reversal ? (
    <div style={{ fontSize: 12, color: '#bbb' }}>
      Prob: {reversalConf}, Bias flips: {raw.reversal.bias_cluster_flipped ? 'Yes' : 'No'}, IV/OI flip: {raw.reversal.iv_oi_support_flip ? 'Yes' : 'No'}
    </div>
  ) : '-';

  const srZones = Array.isArray(raw.sr) ? raw.sr : [];
  const srKey = srZones.length > 0 ? `${srZones.length} zones` : '-';
  const srSummary = srZones.length > 0 ? (
    <div style={{ fontSize: 12, color: '#bbb' }}>
      {srZones.filter(z => z.zone_state === 'Active').map(z => `${z.zone_type} @ ${z.zone_level} (${z.bias_suggestion}, ${z.confidence})`).join('; ') || 'No active zones'}
    </div>
  ) : '-';

  const moduleTable = [
    {
      module: 'Bias Identifier',
      key: (
        <span style={{ color: biasColor(biasVal), fontWeight: 700 }}>{biasVal !== '-' ? biasVal : 'No bias'}{biasWarn && <span style={{ color: '#e53935', marginLeft: 8 }}>(No bias detected)</span>}</span>
      ),
      confidence: biasConf,
      summary: (
        <div>
          <div>Δ: {biasDeltas ? Object.entries(biasDeltas).map(([k, v]) => `${k}: ${v.toFixed(2)}`).join(', ') : '-'}</div>
          <div>%: {biasPct ? Object.entries(biasPct).map(([k, v]) => `${k}: ${v.toFixed(2)}%`).join(', ') : '-'}</div>
        </div>
      ),
    },
    {
      module: 'Market Style',
      key: marketStyle,
      confidence: marketConf,
      summary: marketSummary,
    },
    {
      module: 'Trap Detector',
      key: trapKey,
      confidence: trapConf,
      summary: trapSummary,
    },
    {
      module: 'Reversal Probability',
      key: reversalType,
      confidence: reversalConf,
      summary: reversalSummary,
    },
    {
      module: 'Support/Resistance',
      key: srKey,
      confidence: '-',
      summary: srSummary,
    },
  ];

  return (
    <div className="entry-root">
      {/* Main Status Card */}
      <div className="entry-status-card" style={{ marginBottom: 36, padding: 24, minWidth: 340, maxWidth: 520, boxShadow: '0 2px 12px #0002', borderRadius: 20, background: '#232526', zIndex: 2 }}>
        <div className="entry-status-header" style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
          <span className="entry-status-icon" style={{ fontSize: 38, marginRight: 16 }}>{icon}</span>
          <span className="entry-status-label" style={{ color, fontWeight: 700, fontSize: 32 }}>{data.entry_direction || '-'}</span>
        </div>
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontWeight: 700, color: '#fff' }}>Confidence:</span> <span style={{ color: confColorVal }}>{conf}</span>
          <span style={{ color: '#fff', marginLeft: 16, fontWeight: 700 }}>Trade Type:</span> <span style={{ color: '#fff' }}>{tradeType}</span>
          <span style={{ color: '#fff', marginLeft: 16, fontWeight: 700 }}>Entry Score:</span> <span style={{ color: '#fff' }}>{entryScore}</span>
        </div>
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#fff', fontWeight: 700 }}>Entry Zone:</span> <span style={{ color: '#fff' }}>{data.entry_zone ? data.entry_zone.zone_type + ' @ ' + data.entry_zone.zone_level : '-'}</span>
          <span style={{ color: '#fff', marginLeft: 16, fontWeight: 700 }}>Must Avoid:</span> <span style={{ color: data.must_avoid ? '#e53935' : '#43a047', fontWeight: 700 }}>{data.must_avoid ? 'Yes' : 'No'}</span>
        </div>
        <div style={{ color: '#fff', fontWeight: 700 }}>Reason: <span style={{ fontWeight: 400 }}>{data.reason || '-'}</span></div>
      </div>
      {/* Module Table Card */}
      <div style={{ maxWidth: '700px', width: '100%', margin: '32px auto', padding: '0 8px', boxSizing: 'border-box' }}>
        <div className="entry-table-card" style={{ margin: 0, overflowX: 'auto', width: '100%' }}>
          <table className="entry-table" style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, minWidth: 0, maxWidth: '100%' }}>
            <thead>
              <tr>
                <th style={{ padding: '10px 10px', textAlign: 'left', fontSize: 15, color: '#fff', background: '#181a1b', width: 120 }}>Module</th>
                <th style={{ padding: '10px 10px', textAlign: 'left', fontSize: 15, color: '#fff', background: '#181a1b', width: 160 }}>Key Output</th>
                <th style={{ padding: '10px 8px', textAlign: 'right', fontSize: 15, width: 90, color: '#fff', background: '#181a1b' }}>Confidence/Score</th>
                <th style={{ padding: '10px 10px', textAlign: 'left', fontSize: 14, color: '#fff', background: '#181a1b', maxWidth: 220, minWidth: 120, wordBreak: 'break-word', whiteSpace: 'pre-line' }}>Summary</th>
              </tr>
            </thead>
            <tbody>
              {moduleTable.map((row, i) => (
                <tr key={row.module} style={{ borderBottom: '1px solid #444', background: i % 2 === 0 ? '#232526' : '#181a1b' }}>
                  <td className="entry-table-module" style={{ padding: '10px 10px', fontWeight: 700, color: '#fff', verticalAlign: 'top', width: 120 }}>{row.module}</td>
                  <td className="entry-table-key" style={{ padding: '10px 10px', verticalAlign: 'top', fontWeight: 600, color: '#fff', width: 160 }}>{row.key}</td>
                  <td className="entry-table-confidence" style={{ padding: '10px 8px', textAlign: 'right', fontWeight: 600, color: '#fff', verticalAlign: 'top', width: 90 }}>{row.confidence}</td>
                  <td className="entry-table-summary" style={{ padding: '10px 10px', verticalAlign: 'top', fontSize: 13, color: '#fff', maxWidth: 220, minWidth: 120, wordBreak: 'break-word', whiteSpace: 'pre-line' }}>
                    {row.module === 'Trap Detector' ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, color: '#fff', fontSize: 13 }}>
                        <div><b>Call deception:</b> {trapCall?.deception_score ?? '-'}</div>
                        <div><b>Put deception:</b> {trapPut?.deception_score ?? '-'}</div>
                        <div><b>Call memory:</b> {trapCall?.trap_memory ?? '-'}</div>
                        <div><b>Put memory:</b> {trapPut?.trap_memory ?? '-'}</div>
                        <div><b>Call conf:</b> {trapCall?.confidence_level ?? '-'}</div>
                        <div><b>Put conf:</b> {trapPut?.confidence_level ?? '-'}</div>
                        <div><b>Comment:</b> {trapCall?.comment ?? '-'}</div>
                      </div>
                    ) : typeof row.summary === 'string' ? row.summary : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, color: '#fff', fontSize: 13, wordBreak: 'break-word', whiteSpace: 'pre-line' }}>
                        {React.Children.toArray(
                          typeof row.summary === 'object' && row.summary.props && row.summary.props.children
                            ? (Array.isArray(row.summary.props.children) ? row.summary.props.children : [row.summary.props.children])
                            : []
                        ).map((item, idx) => (
                          <div key={idx} style={{ color: '#fff', fontSize: 13, wordBreak: 'break-word', whiteSpace: 'pre-line' }}>{item}</div>
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
      <style>{`
        @media (max-width: 800px) {
          .entry-table-card { max-width: 99vw !important; }
          .entry-table { font-size: 12px !important; }
          .entry-table th, .entry-table td { padding: 6px 4px !important; }
        }
        @media (max-width: 500px) {
          .entry-table-card { max-width: 99vw !important; }
          .entry-table { font-size: 11px !important; }
          .entry-table th, .entry-table td { padding: 4px 2px !important; }
        }
      `}</style>
    </div>
  );
} 