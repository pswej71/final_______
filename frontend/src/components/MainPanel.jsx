import React from 'react';

const TrendChart = ({ data }) => {
    // SVG drawing logic from template adapted for React
    const W = 800, H = 180, pad = { t: 10, b: 30, l: 0, r: 0 };
    const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;

    if (!data || data.length === 0) return <div style={{ height: 180 }}>No data</div>;

    const total = data.length;
    const xScale = i => pad.l + (i / (total - 1)) * cW;
    const yScale = v => pad.t + (1 - v) * cH;

    const pathD = (vals) => {
        return vals.reduce((acc, v, i) => {
            if (i === 0) return `M ${xScale(i)} ${yScale(v)}`;
            const px = xScale(i - 1), py = yScale(vals[i - 1]);
            const cx = (xScale(i) + px) / 2;
            return acc + ` C ${cx} ${py} ${cx} ${yScale(v)} ${xScale(i)} ${yScale(v)}`;
        }, '');
    };

    const prData = data.map(d => d.efficiency / 100 || 0);
    const riskData = data.map(d => d.failure_risk || 0);

    // Split historical and forecast (last 10 as forecast)
    const forecastIdx = Math.max(0, total - 10);
    const fxStart = xScale(forecastIdx);

    return (
        <div className="chart-svg-wrap">
            <svg className="chart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
                <defs>
                    <linearGradient id="prGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#4af0c4" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#4af0c4" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ff6b6b" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#ff6b6b" stopOpacity="0" />
                    </linearGradient>
                </defs>

                {/* Forecast region */}
                <rect x={fxStart} y={pad.t} width={W - fxStart} height={cH} fill="rgba(99,130,255,0.05)" rx="4" />
                <line x1={fxStart} y1={pad.t} x2={fxStart} y2={pad.t + cH} stroke="rgba(99,130,255,0.3)" strokeWidth="1" strokeDasharray="4,4" />
                <text x={fxStart + 8} y={pad.t + 14} fontFamily="Space Mono" fontSize="9" fill="rgba(99,130,255,0.6)">FORECAST →</text>

                {/* PR area */}
                <path d={`${pathD(prData)} L ${xScale(total - 1)} ${pad.t + cH} L ${xScale(0)} ${pad.t + cH} Z`} fill="url(#prGrad)" />
                {/* Risk area */}
                <path d={`${pathD(riskData)} L ${xScale(total - 1)} ${pad.t + cH} L ${xScale(0)} ${pad.t + cH} Z`} fill="url(#riskGrad)" />

                {/* Lines */}
                <path d={pathD(prData)} fill="none" stroke="#4af0c4" strokeWidth="2" strokeLinecap="round" />
                <path d={pathD(riskData)} fill="none" stroke="#ff6b6b" strokeWidth="2" strokeLinecap="round" strokeDasharray={`0 ${fxStart * 4} 1000`} />

                {/* Legend */}
                <line x1="16" y1="14" x2="36" y2="14" stroke="#4af0c4" strokeWidth="2" />
                <text x="42" y="18" fontFamily="Syne" fontSize="10" fill="#4af0c4" fontWeight="600">Performance Ratio</text>
                <line x1="160" y1="14" x2="180" y2="14" stroke="#ff6b6b" strokeWidth="2" />
                <text x="186" y="18" fontFamily="Syne" fontSize="10" fill="#ff6b6b" fontWeight="600">Risk Score</text>
            </svg>
        </div>
    );
};

const MainPanel = ({ telemetry, inverters, onSelectInverter, selectedId }) => {
    const riskColor = r => r >= 0.65 ? 'var(--risk-high)' : r >= 0.4 ? 'var(--risk-med)' : 'var(--risk-low)';

    return (
        <div className="center-panel">
            {/* KPIs */}
            <div className="kpi-row">
                <div className="kpi-card green">
                    <div className="kpi-label">Plant Uptime</div>
                    <div className="kpi-value green">97.4<span style={{ fontSize: 18 }}>%</span></div>
                    <div className="kpi-sub">↑ 0.8% vs last week</div>
                </div>
                <div className="kpi-card blue">
                    <div className="kpi-label">Active Inverters</div>
                    <div className="kpi-value blue">10<span style={{ fontSize: 18 }}>/12</span></div>
                    <div className="kpi-sub">2 flagged for review</div>
                </div>
                <div className="kpi-card yellow">
                    <div className="kpi-label">Avg Risk Score</div>
                    <div className="kpi-value yellow">0.38</div>
                    <div className="kpi-sub">Medium band · 7d window</div>
                </div>
                <div className="kpi-card red">
                    <div className="kpi-label">Critical Alerts</div>
                    <div className="kpi-value red">2</div>
                    <div className="kpi-sub">INV-04, INV-09 at high risk</div>
                </div>
            </div>

            {/* Trend Chart */}
            <div className="chart-card">
                <div className="chart-header">
                    <div>
                        <div className="chart-title">Performance Ratio & Risk Forecast</div>
                        <div className="chart-subtitle">30-day historical + 10-day ML prediction window</div>
                    </div>
                    <div className="chart-tabs">
                        <div className="chart-tab active">30D</div>
                        <div className="chart-tab">7D</div>
                        <div className="chart-tab">90D</div>
                    </div>
                </div>
                <TrendChart data={telemetry} />
            </div>

            {/* Risk Heatmap */}
            <div className="chart-card">
                <div className="chart-header">
                    <div>
                        <div className="chart-title">7-Day Risk Heatmap</div>
                        <div className="chart-subtitle">Per-inverter failure probability — click cell for details</div>
                    </div>
                </div>
                <div className="heatmap-labels">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
                        <div key={d} className="heatmap-day-label">{d}</div>
                    ))}
                </div>
                <div className="heatmap-grid" id="heatmap-grid">
                    {inverters.slice(0, 7).map((inv, idx) => (
                        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, di) => {
                            // Simulate risk logic from template
                            const noise = (Math.sin(di * 2.3 + inv.risk * 10) * 0.12);
                            const r = Math.max(0.02, Math.min(0.99, inv.risk + noise));
                            const alpha = 0.15 + r * 0.85;
                            const color = r >= 0.65 ? `rgba(255,107,107,${alpha})` : r >= 0.4 ? `rgba(255,209,102,${alpha})` : `rgba(74,240,196,${alpha})`;
                            const textColor = r >= 0.65 ? '#ff6b6b' : r >= 0.4 ? '#ffd166' : '#4af0c4';
                            return (
                                <div
                                    key={`${inv.id}-${day}`}
                                    className="heatmap-cell"
                                    style={{ background: color, color: textColor }}
                                    onClick={() => onSelectInverter(inv.id)}
                                >
                                    <span style={{ fontSize: 8 }}>{(r * 100).toFixed(0)}</span>
                                </div>
                            );
                        })
                    ))}
                </div>
            </div>

            {/* Inverter Table */}
            <div className="grid-card">
                <div className="grid-header">
                    <div>
                        <div style={{ fontSize: 15, fontWeight: 700 }}>All Inverters — Current Status</div>
                        <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>Sorted by risk score (descending)</div>
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Inverter</th>
                            <th>Block</th>
                            <th>Risk Score</th>
                            <th>PR (7d avg)</th>
                            <th>Temp (°C)</th>
                            <th>Alarms</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {inverters.map(inv => (
                            <tr
                                key={inv.id}
                                className={inv.id === selectedId ? 'active' : ''}
                                onClick={() => onSelectInverter(inv.id)}
                                style={{ background: inv.id === selectedId ? 'rgba(99,130,255,0.08)' : '', cursor: 'pointer' }}
                            >
                                <td style={{ fontWeight: 700 }}>{inv.id}</td>
                                <td style={{ fontFamily: 'Space Mono', fontSize: 11 }}>{inv.block}</td>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', width: `${inv.risk * 100}%`, background: riskColor(inv.risk) }}></div>
                                        </div>
                                        <span style={{ fontFamily: 'Space Mono', fontSize: 11, color: riskColor(inv.risk), width: 36, textAlign: 'right' }}>{inv.risk.toFixed(2)}</span>
                                    </div>
                                </td>
                                <td style={{ fontFamily: 'Space Mono', fontSize: 11 }}>{inv.pr}</td>
                                <td style={{ fontFamily: 'Space Mono', fontSize: 11 }}>{inv.temp}</td>
                                <td style={{ fontFamily: 'Space Mono', fontSize: 11, color: inv.alarms > 1 ? 'var(--risk-high)' : 'var(--muted)' }}>{inv.alarms}</td>
                                <td><span style={{ color: riskColor(inv.risk), fontSize: 12, fontWeight: 700 }}>{inv.status}</span></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default MainPanel;
