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
      <div className="entry-status-card">
        <div className="entry-status-header">
          <span className="entry-status-icon">{icon}</span>
          <span className="entry-status-label" style={{ color }}>{data.entry_direction || '-'}</span>
        </div>
        <div className="entry-status-confidence">
          Confidence: <span style={{ color: confColorVal }}>{conf}</span>
        </div>
        <div className="entry-status-tradetype">
          Trade Type: <span>{tradeType}</span>
        </div>
        <div className="entry-status-score">
          Entry Score: <span>{entryScore}</span>
        </div>
        <div className="entry-status-zone">
          Entry Zone: <span>{data.entry_zone ? `${data.entry_zone.zone_type} @ ${data.entry_zone.zone_level} (${data.entry_zone.confidence})` : '-'}</span>
        </div>
        <div className="entry-status-mustavoid">
          Must Avoid: <span style={{ color: data.must_avoid ? '#e53935' : '#43a047' }}>{data.must_avoid ? 'Yes' : 'No'}</span>
        </div>
        <div className="entry-status-reason">
          Reason: <span>{data.reason}</span>
        </div>
      </div>
      {/* Module Table Card */}
      <div className="entry-table-card">
        <table className="entry-table">
          <thead>
            <tr>
              <th>Module</th>
              <th>Key Output</th>
              <th>Confidence/Score</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {moduleTable.map((row, i) => (
              <tr key={row.module}>
                <td className="entry-table-module">{row.module}</td>
                <td className="entry-table-key">{row.key}</td>
                <td className="entry-table-confidence">{row.confidence}</td>
                <td className="entry-table-summary">{row.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 