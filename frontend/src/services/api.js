const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `API request failed for ${path}`;
    try {
      const payload = await response.json();
      message = payload.detail || payload.message || message;
    } catch {
      // Ignore JSON parsing failures and preserve the default message.
    }
    throw new Error(message);
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

export function getPeerCorrelations() {
  return request('/peer_correlations');
}

export function getDatasetInfo() {
  return request('/dataset_info');
}

export function getDeviceInvestigation(deviceId) {
  return request(`/device_investigation/${deviceId}`);
}

export function getDeviceReportUrl(deviceId) {
  return `${API_BASE_URL}/device_report/${deviceId}`;
}

export function uploadDataset(file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/upload_dataset`);

    // XHR is used here because fetch does not expose upload progress events.
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
        return;
      }

      try {
        const payload = JSON.parse(xhr.responseText);
        reject(new Error(payload.detail || payload.message || 'Dataset upload failed'));
      } catch {
        reject(new Error('Dataset upload failed'));
      }
    };

    xhr.onerror = () => reject(new Error('Dataset upload failed'));
    xhr.send(formData);
  });
}
