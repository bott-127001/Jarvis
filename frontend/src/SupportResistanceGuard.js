import React from 'react';
import { useOptionChain } from './OptionChainContext';

const zoneColor = (type) => {
  if (type === 'Support') return '#43a047';
  if (type === 'Resistance') return '#e53935';
  return '#ffa726';
};

export default function SupportResistanceGuard() {
  const { analytics, fetching, user, expiry } = useOptionChain();
  const data = analytics.sr;

  if (!user || !expiry) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>Please select user and expiry.</div>;
  }
  if (!data || !Array.isArray(data) || data.length === 0) {
    return <div style={{ color: '#bbb', fontSize: 20 }}>No support/resistance data.</div>;
  }

  const activeZones = data.filter(z => z.zone_state === 'Active');

  return (
    <div className="sr-root">
      {!fetching && (
        <div className="sr-warning">
          <b>Warning:</b> Data is not updating (fetching stopped). Showing last known results.
        </div>
      )}
      {/* Summary Card */}
      <div className="sr-summary-card">
        <div className="sr-summary-title">Active Zones</div>
        {activeZones.length === 0 ? (
          <div className="sr-no-active">No active zones.</div>
        ) : (
          <div className="sr-active-zones">
            {activeZones.map((zone, i) => (
              <div key={i} className="sr-active-zone" style={{ background: zoneColor(zone.zone_type) }}>
                {zone.zone_type} @ {zone.zone_level} <br />
                <span className="sr-active-zone-details">Bias: {zone.bias_suggestion || '-'}<br />Conf: {zone.confidence || '-'}<br />State: {zone.zone_state}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      {/* All Zones Table */}
      <div className="sr-table-card">
        <table className="sr-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Level</th>
              <th>Bias</th>
              <th>Confidence</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            {data.map((zone, i) => (
              <tr key={i}>
                <td className="sr-table-type" style={{ color: zoneColor(zone.zone_type) }}>{zone.zone_type}</td>
                <td className="sr-table-cell">{zone.zone_level}</td>
                <td className="sr-table-cell">{zone.bias_suggestion || '-'}</td>
                <td className="sr-table-cell">{zone.confidence || '-'}</td>
                <td className="sr-table-cell">{zone.zone_state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 