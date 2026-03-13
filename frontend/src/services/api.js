const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed for ${path}`);
  }
  return response.json();
}

export function getDevices() {
  return request('/devices');
}

export function getTrustScores() {
  return request('/trust_scores');
}

export function getDrift() {
  return request('/drift');
}

export function getRiskGraph() {
  return request('/risk_graph');
}

export function getDigitalTwins() {
  return request('/digital_twins');
}

export function getDevice(deviceId) {
  return request(`/device/${deviceId}`);
}
