import React from 'react';

const Header = ({ onRunPrediction }) => {
    return (
        <header>
            <div className="logo">
                <div className="logo-icon">⚡</div>
                <div className="logo-text">Solar<span>Mind</span></div>
            </div>
            <div className="header-meta">
                <div className="live-indicator">
                    <div className="live-dot"></div>
                    LIVE
                </div>
                <span>Plant: Rajkot Alpha — 40MW</span>
                <span>Updated: {new Date().toLocaleTimeString()}</span>
                <span>7-Day Horizon</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
                <button className="header-btn">Export PDF</button>
                <button className="header-btn primary" onClick={onRunPrediction}>⚡ Run Prediction</button>
            </div>
        </header>
    );
};

export default Header;
