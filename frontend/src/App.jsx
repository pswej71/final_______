import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import InverterSidebar from './components/InverterSidebar';
import MainPanel from './components/MainPanel';
import RightPanel from './components/RightPanel';
import { getHistory, getAISuggestions, getPredictiveRisk, simulateData, predictRisk } from './api';
import './index.css';

const INVERTERS = [
  { id: 'INV-04', name: 'INV-04', block: 'B', string: 3, risk: 0.81, pr: 0.71, temp: 74, alarms: 3, status: 'Critical', cap: '3.3 MW' },
  { id: 'INV-09', name: 'INV-09', block: 'C', string: 1, risk: 0.73, pr: 0.76, temp: 71, alarms: 2, status: 'High Risk', cap: '3.3 MW' },
  { id: 'INV-07', name: 'INV-07', block: 'B', string: 2, risk: 0.51, pr: 0.80, temp: 65, alarms: 1, status: 'Moderate', cap: '3.3 MW' },
  { id: 'INV-11', name: 'INV-11', block: 'D', string: 4, risk: 0.44, pr: 0.82, temp: 63, alarms: 1, status: 'Moderate', cap: '3.3 MW' },
  { id: 'INV-02', name: 'INV-02', block: 'A', string: 2, risk: 0.28, pr: 0.87, temp: 59, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-06', name: 'INV-06', block: 'B', string: 1, risk: 0.22, pr: 0.88, temp: 58, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-01', name: 'INV-01', block: 'A', string: 1, risk: 0.18, pr: 0.89, temp: 57, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-03', name: 'INV-03', block: 'A', string: 3, risk: 0.15, pr: 0.90, temp: 56, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-05', name: 'INV-05', block: 'B', string: 4, risk: 0.14, pr: 0.91, temp: 55, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-08', name: 'INV-08', block: 'C', string: 2, risk: 0.12, pr: 0.92, temp: 54, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-10', name: 'INV-10', block: 'C', string: 3, risk: 0.09, pr: 0.93, temp: 53, alarms: 0, status: 'Normal', cap: '3.3 MW' },
  { id: 'INV-12', name: 'INV-12', block: 'D', string: 2, risk: 0.07, pr: 0.94, temp: 52, alarms: 0, status: 'Normal', cap: '3.3 MW' },
];

function App() {
  const [selectedId, setSelectedId] = useState('INV-04');
  const [telemetry, setTelemetry] = useState([]);
  const [loading, setLoading] = useState(true);
  const [predictiveRisk, setPredictiveRisk] = useState(null);
  const [aiInsight, setAiInsight] = useState(null);

  const fetchData = async () => {
    try {
      const history = await getHistory(50);
      setTelemetry(history);

      const insight = await getAISuggestions();
      setAiInsight(insight);

      const latest = history[history.length - 1] || {};
      const selInv = INVERTERS.find(inv => inv.id === selectedId);

      const telemetryObj = {
        inverter_id: selectedId,
        block: selInv.block,
        ac_power: latest.power || 1000,
        dc_power: (latest.power || 1000) * 1.05,
        pv1_power: (latest.power || 1000) * 0.5,
        pv2_power: (latest.power || 1000) * 0.5,
        v_r: Math.random() * 20 + 220,
        v_y: Math.random() * 20 + 220,
        v_b: Math.random() * 20 + 220,
        temperature: latest.temperature || 45,
        pv1_voltage: 500,
        pv2_voltage: 500,
        grid_voltage: 400
      };

      try {
        const mlRisk = await predictRisk(telemetryObj);
        setPredictiveRisk(mlRisk);
      } catch (err) {
        // Fallback to older predictive risk if ML backend isn't up
        const risk = await getPredictiveRisk();
        setPredictiveRisk(risk);
      }

      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(async () => {
      await simulateData();
      fetchData();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const selectedInverter = INVERTERS.find(inv => inv.id === selectedId);

  return (
    <div className="shell">
      <Header onRunPrediction={fetchData} />
      <main>
        <InverterSidebar
          inverters={INVERTERS}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <MainPanel
          telemetry={telemetry}
          inverters={INVERTERS}
          onSelectInverter={setSelectedId}
          selectedId={selectedId}
        />
        <RightPanel
          selectedInverter={selectedInverter}
          predictiveRisk={predictiveRisk}
          aiInsight={aiInsight}
          loading={loading}
        />
      </main>
    </div>
  );
}

export default App;
