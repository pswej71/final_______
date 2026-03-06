import React, { useState } from 'react';
import { askQuestion } from '../api';

const RiskDial = ({ risk }) => {
    const dashOffset = 180 - ((risk || 0) * 180);
    const color = risk >= 0.65 ? 'var(--risk-high)' : risk >= 0.4 ? 'var(--risk-med)' : 'var(--risk-low)';
    const level = risk >= 0.65 ? 'HIGH' : risk >= 0.4 ? 'MEDIUM' : 'LOW';

    return (
        <div className="risk-dial-wrap">
            <svg className="dial-svg" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle cx="50" cy="50" r="38" fill="none" stroke={color} strokeWidth="8"
                    strokeDasharray="180" strokeDashoffset={dashOffset}
                    strokeLinecap="round" transform="rotate(-90 50 50)"
                    style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }} />
                <text x="50" y="54" textAnchor="middle" fontFamily="Syne" fontSize="20" fontWeight="800" fill={color}>
                    {(risk || 0).toFixed(2)}
                </text>
            </svg>
            <div className="dial-info">
                <div className="dial-label" style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, marginBottom: 4 }}>7-Day Failure Risk</div>
                <div className="dial-value" style={{ fontSize: 28, fontWeight: 800, letterSpacing: -1, color: color }}>{level}</div>
                <div className="dial-desc" style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4, fontFamily: 'Space Mono' }}>P(failure) = {(risk || 0).toFixed(2)}</div>
            </div>
        </div>
    );
};

const RightPanel = ({ selectedInverter, predictiveRisk, aiInsight, loading }) => {
    const [messages, setMessages] = useState([]);
    const [query, setQuery] = useState('');
    const [isAsking, setIsAsking] = useState(false);

    const handleSend = async () => {
        if (!query.trim()) return;
        setMessages(prev => [...prev, { text: query, sender: 'user' }]);
        setQuery('');
        setIsAsking(true);
        try {
            const res = await askQuestion(query);
            setMessages(prev => [...prev, { text: res.answer, sender: 'ai' }]);
        } catch (err) {
            setMessages(prev => [...prev, { text: "Error connecting to AI service.", sender: 'ai' }]);
        }
        setIsAsking(false);
    };

    if (!selectedInverter) return <div className="right-panel">Select an inverter</div>;

    const risk = predictiveRisk ? predictiveRisk.failure_probability_7d || predictiveRisk.risk_score || selectedInverter.risk : selectedInverter.risk;
    const color = risk >= 0.65 ? 'var(--risk-high)' : risk >= 0.4 ? 'var(--risk-med)' : 'var(--risk-low)';

    return (
        <div className="right-panel">
            <div style={{ padding: 20, borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
                <div className="ai-badge">
                    <div className="live-dot" style={{ width: 5, height: 5, background: 'var(--accent)', borderRadius: '50%', animation: 'blink 1.5s infinite' }}></div>
                    GenAI Insight Engine
                </div>
                <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 2 }}>{selectedInverter.id}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>Block {selectedInverter.block} · String {selectedInverter.string} · {selectedInverter.cap} nominal</div>

                <RiskDial risk={risk} />

                {risk >= 0.4 && (
                    <div className="alert-banner" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', borderRadius: 8, fontSize: 12, color: color, background: `${color}15`, border: `1px solid ${color}40` }}>
                        <span>{risk >= 0.65 ? '⚠' : '⚡'}</span>
                        <span><strong>{risk >= 0.65 ? 'Immediate action required.' : 'Elevated risk detected.'}</strong> {risk >= 0.65 ? 'Shutdown probability exceeds threshold.' : 'Schedule inspection within 5 days.'}</span>
                    </div>
                )}
            </div>

            <div style={{ padding: '16px 20px 0', marginBottom: 8, flexShrink: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', marginBottom: 10, fontFamily: 'Space Mono', letterSpacing: 1, textTransform: 'uppercase' }}>Top Risk Factors (SHAP)</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {(predictiveRisk?.top_features ? predictiveRisk.top_features.map(f => f.feature) : (predictiveRisk?.key_contributing_factors || ['DC Bus Voltage', 'Thermal Stress', 'Efficiency Loss'])).slice(0, 3).map((factor, i) => (
                        <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ fontSize: 12, fontWeight: 600 }}>{factor}</div>
                                <div style={{ fontFamily: 'Space Mono', fontSize: 11, color: 'var(--accent)' }}>{(predictiveRisk?.top_features ? (predictiveRisk.top_features[i].importance).toFixed(3) : (0.8 - i * 0.1).toFixed(2))}</div>
                            </div>
                            <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${Math.max(10, 80 - i * 15)}%`, background: 'linear-gradient(90deg, var(--accent2), var(--accent))' }}></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px 20px' }}>
                <div className="narrative-box">
                    <strong>AI Analysis — {selectedInverter.id}:</strong><br /><br />
                    {loading ? "Analyzing patterns..." : (
                        predictiveRisk && predictiveRisk.llm_explanation ? (
                            <>
                                {predictiveRisk.llm_explanation}
                            </>
                        ) : aiInsight ? (
                            <>
                                Inverter <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{selectedInverter.id}</span> shows {aiInsight.trend}. {aiInsight.insight}<br /><br />
                                <strong>Recommendation:</strong> {aiInsight.recommendation}
                            </>
                        ) : (
                            <>
                                Inverter <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{selectedInverter.id}</span> is showing a <span style={{ color: color, fontWeight: 600 }}>{risk >= 0.65 ? 'high' : risk >= 0.4 ? 'moderate' : 'low'} failure risk ({risk.toFixed(2)})</span>.
                                Telemetry patterns suggest stable operation with minor thermal deviations.
                            </>
                        )
                    )}
                </div>

                <div style={{ marginTop: 16 }}>
                    <strong style={{ fontSize: 12, color: 'var(--muted)' }}>Chat with RAG Agent:</strong>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
                        {messages.map((m, i) => (
                            <div key={i} style={{ padding: '8px 12px', borderRadius: 8, fontSize: 12, backgroundColor: m.sender === 'user' ? 'rgba(255,255,255,0.1)' : 'rgba(99,130,255,0.15)', alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
                                <strong style={{ color: m.sender === 'user' ? '#fff' : 'var(--accent)' }}>{m.sender === 'user' ? 'You' : 'Agent'}: </strong>
                                {m.text}
                            </div>
                        ))}
                        {isAsking && <div style={{ fontSize: 11, color: 'var(--muted)' }}>Agent is typing...</div>}
                    </div>
                </div>
            </div>

            <div className="chat-input-wrap">
                <div className="chat-row" style={{ display: 'flex', gap: 8 }}>
                    <input
                        className="chat-input"
                        placeholder="Ask about inverter health…"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSend()}
                        style={{ flex: 1, padding: 8, borderRadius: 4, background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }}
                    />
                    <button className="chat-send" onClick={handleSend} style={{ background: 'var(--accent)', color: '#000', border: 'none', borderRadius: 4, padding: '0 12px', cursor: 'pointer', fontWeight: 'bold' }}>↑</button>
                </div>
            </div>
        </div>
    );
};

export default RightPanel;
