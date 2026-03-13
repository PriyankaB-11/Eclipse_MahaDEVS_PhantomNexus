import { useEffect, useState } from 'react';
import DeviceTable from '../components/DeviceTable';
import { getDevices } from '../services/api';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setDevices(await getDevices());
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    load();
  }, []);

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="panel rounded-3xl p-6">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-glow/80">Fleet Inventory</p>
        <h2 className="mt-2 font-display text-3xl font-semibold">Device posture and trust status</h2>
        <p className="mt-2 max-w-3xl text-sm text-mist">
          Review current trust scores, active anomalies, and botnet recruitment probability across the monitored IoT estate.
        </p>
      </section>
      <DeviceTable devices={devices} />
    </div>
  );
}
