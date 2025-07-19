import React, { useState } from 'react';
import { useOptionChain } from './OptionChainContext';

const columns = [
  'call_delta', 'call_theta', 'call_vega', 'call_oi', 'call_pop', 'call_gamma', 'call_prev_oi', 'call_chng_in_oi', 'call_volume', 'call_iv', 'call_ltp', 'call_bid_qty', 'call_bid_price', 'call_ask_price', 'call_ask_qty',
  'strike_price',
  'put_bid_qty', 'put_bid_price', 'put_ask_price', 'put_ask_qty', 'put_ltp', 'put_iv', 'put_volume', 'put_oi', 'put_pop', 'put_gamma', 'put_prev_oi', 'put_chng_in_oi', 'put_vega', 'put_theta', 'put_delta'
];

const columnLabels = {
  call_delta: 'Delta', call_theta: 'Theta', call_vega: 'Vega', call_oi: 'OI', call_pop: 'POP', call_gamma: 'Gamma', call_prev_oi: 'PREV OI', call_chng_in_oi: 'CHNG IN OI', call_volume: 'VOLUME', call_iv: 'IV', call_ltp: 'LTP', call_bid_qty: 'BID QTY', call_bid_price: 'BID', call_ask_price: 'ASK', call_ask_qty: 'ASK QTY',
  strike_price: 'STRIKE',
  put_bid_qty: 'BID QTY', put_bid_price: 'BID', put_ask_price: 'ASK', put_ask_qty: 'ASK QTY', put_ltp: 'LTP', put_iv: 'IV', put_volume: 'VOLUME', put_oi: 'OI', put_pop: 'POP', put_gamma: 'Gamma', put_prev_oi: 'PREV OI', put_chng_in_oi: 'CHNG IN OI', put_vega: 'Vega', put_theta: 'Theta', put_delta: 'Delta'
};

const callsColCount = 15;
const putsColCount = 15;

export default function OptionChain() {
  const {
    user,
    expiry, setExpiry,
    fetching, startFetching, stopFetching,
    optionChain, error, setAnalytics
  } = useOptionChain();
  const [localExpiry, setLocalExpiry] = useState(expiry || '');

  // Sync expiry input with context
  const handleExpiryChange = (e) => {
    setLocalExpiry(e.target.value);
    setExpiry(e.target.value);
  };

  // Compute CHNG IN OI for calls and puts
  const processedData = optionChain.map(row => ({
    ...row,
    call_chng_in_oi: (row.call_oi !== undefined && row.call_prev_oi !== undefined) ? (row.call_oi - row.call_prev_oi) : '-',
    put_chng_in_oi: (row.put_oi !== undefined && row.put_prev_oi !== undefined) ? (row.put_oi - row.put_prev_oi) : '-',
  }));

  const handleStart = () => {
    if (!user || !localExpiry) return;
    startFetching(user, localExpiry);
  };

  const handleStop = () => {
    stopFetching();
  };

  const handleClearData = async () => {
    if (!user || !localExpiry) return;
    if (!window.confirm('Are you sure you want to clear all calculated analytics data? This cannot be undone.')) return;
    // Clear analytics in frontend
    setAnalytics({});
    localStorage.setItem('optionChain_analytics', '{}');
    // Call backend to clear analytics
    try {
      await fetch(`/clear-analytics?user=${user}&expiry=${localExpiry}`, { method: 'POST' });
      alert('Analytics data cleared!');
    } catch {
      alert('Failed to clear analytics data on backend.');
    }
  };

  return (
    <div className="optionchain-root optionchain-align-top">
      <div className="optionchain-filter-row">
        <div className="optionchain-filter-top">
          <label style={{ color: '#fff', fontWeight: 500, marginRight: 8 }}>Expiry Date:</label>
        <input
          type="date"
          value={localExpiry}
          onChange={handleExpiryChange}
            style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #444', background: '#181a1b', color: '#fff', marginRight: 8 }}
        />
        <button
          onClick={handleStart}
          disabled={fetching}
          style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: fetching ? '#444' : '#61dafb', color: fetching ? '#bbb' : '#181a1b', fontWeight: 600, fontSize: 15, cursor: fetching ? 'not-allowed' : 'pointer' }}
        >
          Start Fetch
        </button>
        </div>
        <div className="optionchain-filter-bottom">
        <button
          onClick={handleStop}
          disabled={!fetching}
            style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: !fetching ? '#444' : '#e53935', color: !fetching ? '#bbb' : '#fff', fontWeight: 600, fontSize: 15, cursor: !fetching ? 'not-allowed' : 'pointer', marginRight: 8 }}
        >
          Stop Fetch
        </button>
          <button
            onClick={handleClearData}
            style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: '#ffa726', color: '#232526', fontWeight: 600, fontSize: 15, cursor: 'pointer' }}
          >
            Clear Data
          </button>
        </div>
      </div>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}
      <div className="optionchain-table-wrapper scroll-hide optionchain-table-tall">
        <table style={{ width: '100%', borderCollapse: 'collapse', color: '#fff' }}>
          <thead>
            <tr>
              <th colSpan={callsColCount} style={{ background: '#232526', color: '#fff', fontWeight: 700, fontSize: 13, padding: 4, textAlign: 'center', borderBottom: '1px solid #444' }}>CALLS</th>
              <th style={{ background: '#232526', color: '#fff', fontWeight: 700, fontSize: 13, padding: 4, textAlign: 'center', borderBottom: '1px solid #444' }}>STRIKE</th>
              <th colSpan={putsColCount} style={{ background: '#232526', color: '#fff', fontWeight: 700, fontSize: 13, padding: 4, textAlign: 'center', borderBottom: '1px solid #444' }}>PUTS</th>
            </tr>
            <tr>
              {columns.map(col => (
                <th key={col} style={{ background: '#232526', color: '#61dafb', padding: 4, borderBottom: '1px solid #444', fontWeight: 600, fontSize: 12 }}>{columnLabels[col]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {processedData.length === 0 ? (
              <tr><td colSpan={columns.length} style={{ textAlign: 'center', padding: 24, color: '#bbb' }}>No data</td></tr>
            ) : (
              processedData.map((row, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? '#232526' : '#181a1b' }}>
                  {columns.map(col => (
                    <td key={col} style={{ padding: 4, borderBottom: '1px solid #333', textAlign: 'right', fontSize: 13 }}>{row[col] !== undefined ? row[col] : '-'}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
} 