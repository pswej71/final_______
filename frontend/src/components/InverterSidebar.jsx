import React from 'react';

const InverterSidebar = ({ inverters, selectedId, onSelect }) => {
    const riskClass = r => r >= 0.65 ? 'high' : r >= 0.4 ? 'med' : 'low';
    const riskColor = r => r >= 0.65 ? 'var(--risk-high)' : r >= 0.4 ? 'var(--risk-med)' : 'var(--risk-low)';

    return (
        <div className="sidebar">
            <div>
                <div className="section-label">Inverters ({inverters.length})</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {inverters.map((inv) => {
                        const rc = riskClass(inv.risk);
                        return (
                            <div
                                key={inv.id}
                                className={`inverter-card risk-${rc} ${inv.id === selectedId ? 'active' : ''}`}
                                onClick={() => onSelect(inv.id)}
                            >
                                <div className="inv-header">
                                    <div>
                                        <div className="inv-name">{inv.id}</div>
                                        <div className="inv-block">Block {inv.block} · Str {inv.string}</div>
                                    </div>
                                    <div className={`risk-badge ${rc}`}>{(inv.risk * 100).toFixed(0)}%</div>
                                </div>
                                <div className="inv-score-bar">
                                    <div
                                        className="inv-score-fill"
                                        style={{ width: `${inv.risk * 100}%`, background: riskColor(inv.risk) }}
                                    ></div>
                                </div>
                                <div className="inv-meta">
                                    <div className="inv-stat">PR <span>{inv.pr}</span></div>
                                    <div className="inv-stat">Temp <span>{inv.temp}°C</span></div>
                                    <div className="inv-stat">Alarms <span>{inv.alarms}</span></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default InverterSidebar;
