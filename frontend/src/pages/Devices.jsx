import { useEffect, useState } from 'react';
import DeviceTable from '../components/DeviceTable';
import FileUpload from '../components/FileUpload';
import { getDatasetInfo, getDevices } from '../services/api';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [deviceResponse, datasetResponse] = await Promise.all([getDevices(), getDatasetInfo()]);
        setDevices(deviceResponse);
        setDatasetInfo(datasetResponse);
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    load();
  }, []);

  async function refreshAfterUpload() {
    try {
      const [deviceResponse, datasetResponse] = await Promise.all([getDevices(), getDatasetInfo()]);
      setDevices(deviceResponse);
      setDatasetInfo(datasetResponse);
      setError('');
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="page-hero rounded-3xl p-6">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-[var(--accent-primary)]">Fleet Inventory</p>
        <h2 className="mt-2 font-display text-3xl font-semibold">Device posture and trust status</h2>
        <p className="mt-2 max-w-3xl text-sm soft-label">
          Review current trust scores, active anomalies, and botnet recruitment probability across the monitored IoT estate.
        </p>
        {datasetInfo ? (
          <div className="mt-4 inline-flex rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm soft-label">
            Active dataset: {datasetInfo.dataset_name} • {datasetInfo.record_count} rows • {datasetInfo.device_count} devices
          </div>
        ) : null}
      </section>
      <FileUpload onUploadComplete={refreshAfterUpload} />
      <DeviceTable devices={devices} />
    </div>
  );
}
