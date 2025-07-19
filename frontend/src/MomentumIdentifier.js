import React from 'react';

const data = {
  title: 'Volatile / Choppy',
  subtitle: 'Market Style Identifier',
  left: [
    { label: 'OI Diff', value: '-0.97' },
    { label: 'IV Diff', value: '2.32' },
    { label: 'Price Dir', value: 'down' },
    { label: 'EMA Slope', value: '-62.36' },
    { label: 'Total Vol', value: '2,020,921,350' },
  ],
  right: [
    { label: 'Vol Diff', value: '-0.09' },
    { label: 'Volatility', value: 'Stable' },
    { label: 'Baseline', value: 'morning' },
    { label: 'Mode', value: 'adaptive' },
    { label: 'Total OI', value: '225,155,625' },
  ],
};

export default function MomentumIdentifier() {
  return (
    <div className="momentum-root">
      <div className="momentum-header">
        <div className="momentum-title">{data.title}</div>
        <div className="momentum-subtitle">{data.subtitle}</div>
      </div>
      <div className="momentum-card">
        <table className="momentum-table">
          <tbody>
            {data.left.map((row, i) => (
              <tr key={row.label}>
                <td className="momentum-label">{row.label}</td>
                <td className="momentum-value">{row.value}</td>
                <td className="momentum-gap"></td>
                <td className="momentum-label">{data.right[i].label}</td>
                <td className="momentum-value">{data.right[i].value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 