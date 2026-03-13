import { Link } from 'react-router-dom';

function riskClasses(level) {
  if (level === 'critical') {
    return 'risk-badge-critical';
  }
  if (level === 'warning') {
    return 'risk-badge-warning';
  }
  return 'risk-badge-safe';
}

export default function DeviceTable({ devices }) {
  return (
    <div className="surface-card overflow-hidden rounded-3xl">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div>
          <h2 className="font-display text-xl font-semibold">Device Watchlist</h2>
          <p className="text-sm soft-label">Prioritized by lowest trust score and active recruitment indicators.</p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-xs soft-label">
          {devices.length} monitored devices
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 soft-label">
            <tr>
              <th className="px-6 py-3 font-medium">Device</th>
              <th className="px-6 py-3 font-medium">Trust Score</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Risk Level</th>
              <th className="px-6 py-3 font-medium">Botnet Probability</th>
              <th className="px-6 py-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr key={device.device_id} className="border-t border-white/5">
                <td className="px-6 py-4">
                  <div className="font-medium text-white">{device.device_id}</div>
                  <div className="font-mono text-xs soft-label">{device.src_ip}</div>
                </td>
                <td className="px-6 py-4 font-mono text-lg text-white">{device.trust_score}</td>
                <td className="px-6 py-4 capitalize soft-label">{device.status}</td>
                <td className="px-6 py-4">
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${riskClasses(device.risk_level)}`}>
                    {device.risk_level}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono soft-label">{Math.round(device.botnet_probability * 100)}%</td>
                <td className="px-6 py-4">
                  <Link
                    className="btn-accent inline-flex rounded-xl px-3 py-2 text-sm font-semibold"
                    to={`/devices/${device.device_id}`}
                  >
                    Investigate
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
