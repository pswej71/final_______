import React, { useState, useEffect } from 'react';
import { generateReport } from '../api';
import { FileText, Download, X, Printer, CheckCircle, AlertCircle } from 'lucide-react';

const ReportView = ({ isOpen, onClose }) => {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            handleGenerate();
        }
    }, [isOpen]);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const data = await generateReport(7);
            setReport(data);
        } catch (error) {
            console.error("Error generating report:", error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 1000,
            padding: '2rem'
        }}>
            <div className="glass-card fade-in" style={{
                width: '100%', maxWidth: '900px', maxHeight: '90vh',
                overflowY: 'auto', position: 'relative', padding: '2.5rem'
            }}>
                <button onClick={onClose} style={{
                    position: 'absolute', top: '1.5rem', right: '1.5rem',
                    background: 'none', border: 'none', color: 'var(--text-secondary)',
                    cursor: 'pointer'
                }}><X size={24} /></button>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                    <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <FileText color="var(--accent-primary)" size={28} />
                        Maintenance Recommendation Report
                    </h2>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button className="btn btn-secondary" onClick={() => window.print()} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Printer size={18} /> Print PDF
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '4rem' }}>
                        <div className="loading-spinner" style={{ marginBottom: '1rem' }}></div>
                        <p>Synthesizing historical data and generating AI insights...</p>
                    </div>
                ) : report ? (
                    <div className="report-content">
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem', padding: '1.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                            <div>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Period</span>
                                <p style={{ margin: '0.25rem 0', fontWeight: 600 }}>Last {report.metadata.period_days} Days</p>
                            </div>
                            <div>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Avg Efficiency</span>
                                <p style={{ margin: '0.25rem 0', fontWeight: 600 }}>{report.metadata.avg_efficiency.toFixed(2)}%</p>
                            </div>
                            <div>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Peak Failure Risk</span>
                                <p style={{ margin: '0.25rem 0', fontWeight: 600, color: report.metadata.max_failure_risk > 0.5 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                                    {(report.metadata.max_failure_risk * 100).toFixed(1)}%
                                </p>
                            </div>
                            <div>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Anomalies</span>
                                <p style={{ margin: '0.25rem 0', fontWeight: 600 }}>{report.metadata.total_anomalies}</p>
                            </div>
                        </div>

                        <div className="ai-report-body" style={{ lineHeight: 1.6 }}>
                            <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Executive Summary</h3>
                            <p>{report.report_content.insight}</p>

                            <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginTop: '2rem' }}>Recommended Actions</h3>
                            <ul style={{ paddingLeft: '1.2rem' }}>
                                {report.report_content.recommendations.map((rec, i) => (
                                    <li key={i} style={{ marginBottom: '0.75rem' }}>{rec}</li>
                                ))}
                            </ul>

                            <div style={{ marginTop: '3rem', padding: '1.5rem', border: '1px dashed var(--border-color)', borderRadius: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                <p style={{ margin: 0 }}><strong>Report Identifier:</strong> {report.generated_at}</p>
                                <p style={{ margin: '0.5rem 0 0 0' }}>This report was automatically generated by the AI Guardian engine using historical telemetry and Google Gemini insights.</p>
                            </div>
                        </div>
                    </div>
                ) : <p>Failed to load report.</p>}
            </div>
        </div>
    );
};

export default ReportView;
