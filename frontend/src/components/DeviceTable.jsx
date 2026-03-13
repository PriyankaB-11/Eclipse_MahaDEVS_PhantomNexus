import { Link } from 'react-router-dom';

function riskClasses(level) {
  if (level === 'critical') {
    return 'bg-red-500/20 text-red-200 border-red-400/30';
  }
  if (level === 'warning') {
    return 'bg-amber-500/20 text-amber-100 border-amber-300/30';
  }
  return 'bg-emerald-500/20 text-emerald-100 border-emerald-300/30';
}

export default function DeviceTable({ devices }) {
  return (
    <div className="panel overflow-hidden rounded-3xl">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div>
          <h2 className="font-display text-xl font-semibold">Device Watchlist</h2>
          <p className="text-sm text-mist">Prioritized by lowest trust score and active recruitment indicators.</p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-xs text-mist">
          {devices.length} monitored devices
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-mist">
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
                  <div className="font-mono text-xs text-mist">{device.src_ip}</div>
                </td>
                <td className="px-6 py-4 font-mono text-lg text-white">{device.trust_score}</td>
                <td className="px-6 py-4 capitalize text-mist">{device.status}</td>
                <td className="px-6 py-4">
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${riskClasses(device.risk_level)}`}>
                    {device.risk_level}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-mist">{Math.round(device.botnet_probability * 100)}%</td>
                <td className="px-6 py-4">
                  <Link
                    className="btn btn-sm border-0 bg-glow px-3 py-2 font-semibold text-midnight hover:bg-[#7df2db]"
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
