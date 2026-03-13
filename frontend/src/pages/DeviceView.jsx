import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import DeviceDetail from '../components/DeviceDetail';
import TrustScoreChart from '../components/TrustScoreChart';
import { getDevice } from '../services/api';

export default function DeviceView() {
  const { deviceId } = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setDetail(await getDevice(deviceId));
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    load();
  }, [deviceId]);

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  if (!detail) {
    return <div className="surface-card rounded-3xl p-6 soft-label">Loading device investigation...</div>;
  }

  return (
    <div className="space-y-6">
      <Link className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm soft-label hover:bg-white/10" to="/devices">
        Back to Devices
      </Link>
      <DeviceDetail detail={detail} />
      <TrustScoreChart history={detail.history} title="Device Trust History" />
    </div>
  );
}
