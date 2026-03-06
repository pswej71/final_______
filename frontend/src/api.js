import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const getLatestTelemetry = async () => {
  const response = await axios.get(`${API_URL}/inverter/latest`);
  return response.data;
};

export const getHistory = async (limit = 100) => {
  const response = await axios.get(`${API_URL}/inverter/history?limit=${limit}`);
  return response.data;
};

export const getAlerts = async () => {
  const response = await axios.get(`${API_URL}/alerts`);
  return response.data;
};

export const getAISuggestions = async () => {
  const response = await axios.get(`${API_URL}/ai/suggestions`);
  return response.data;
};

export const simulateData = async () => {
  const response = await axios.post(`${API_URL}/simulator/generate`);
  return response.data;
};

export const getPredictiveRisk = async () => {
  const response = await axios.get(`${API_URL}/predictive/risk`);
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await axios.get(`${API_URL}/system/status`);
  return response.data;
};

export const generateReport = async (days = 7) => {
  const response = await axios.get(`${API_URL}/reports/generate?days=${days}`);
  return response.data;
};

// --- New Production Intelligent Platform Endpoints ---
const ML_API_URL = 'http://localhost:8001';

export const predictRisk = async (telemetry) => {
  const response = await axios.post(`${ML_API_URL}/predict`, telemetry);
  return response.data;
};

export const askQuestion = async (query) => {
  const response = await axios.post(`${ML_API_URL}/ask`, { query });
  return response.data;
};
