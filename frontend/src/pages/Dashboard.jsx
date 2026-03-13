import { useEffect, useState } from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import NetworkGraph from '../components/NetworkGraph';
import TrustScoreChart from '../components/TrustScoreChart';
import { getDevices, getRiskGraph, getTrustScores } from '../services/api';

const PIE_COLORS = ['#4be2c5', '#ffb454', '#ff6b6b'];

function buildSystemHistory(trustScores) {
  const buckets = {};
  trustScores.forEach((device) => {
    device.history.forEach((point) => {
      if (!buckets[point.timestamp]) {
        buckets[point.timestamp] = { timestamp: point.timestamp, total: 0, count: 0 };
      }
      buckets[point.timestamp].total += point.trust_score;
      buckets[point.timestamp].count += 1;
    });
  });

  return Object.values(buckets)
    .map((bucket) => ({
      timestamp: bucket.timestamp,
      trust_score: Number((bucket.total / bucket.count).toFixed(2)),
    }))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
}

export default function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [trustScores, setTrustScores] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [deviceResponse, trustResponse, graphResponse] = await Promise.all([
          getDevices(),
          getTrustScores(),
          getRiskGraph(),
        ]);
        setDevices(deviceResponse);
        setTrustScores(trustResponse);
        setGraph(graphResponse);
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    load();
  }, []);

  const riskyDevices = devices.filter((device) => device.trust_score < 70);
  const averageTrust = devices.length
    ? (devices.reduce((total, device) => total + device.trust_score, 0) / devices.length).toFixed(1)
    : '0.0';
  const riskDistribution = [
    { name: 'Safe', value: devices.filter((device) => device.risk_level === 'safe').length },
    { name: 'Warning', value: devices.filter((device) => device.risk_level === 'warning').length },
    { name: 'Critical', value: devices.filter((device) => device.risk_level === 'critical').length },
  ];
  const systemHistory = buildSystemHistory(trustScores);

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'Total Devices', value: devices.length, accent: 'text-glow' },
          { label: 'Risky Devices', value: riskyDevices.length, accent: 'text-amber-300' },
          { label: 'Average Trust Score', value: averageTrust, accent: 'text-white' },
        ].map((stat) => (
          <div key={stat.label} className="panel rounded-3xl p-6">
            <p className="font-mono text-xs uppercase tracking-[0.3em] text-mist">{stat.label}</p>
            <p className={`mt-4 font-mono text-4xl font-semibold ${stat.accent}`}>{stat.value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <TrustScoreChart history={systemHistory} title="System Trust Trajectory" />
        <div className="panel rounded-3xl p-6">
          <div className="mb-5">
            <h2 className="font-display text-xl font-semibold">Risk Distribution</h2>
            <p className="text-sm text-mist">Fleet-wide segmentation by current trust posture.</p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskDistribution} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100} paddingAngle={5}>
                  {riskDistribution.map((entry, index) => (
                    <Cell key={entry.name} fill={PIE_COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#0f2332',
                    border: '1px solid rgba(147, 185, 216, 0.2)',
                    borderRadius: '16px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid gap-2">
            {riskDistribution.map((entry, index) => (
              <div key={entry.name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: PIE_COLORS[index] }} />
                  <span>{entry.name}</span>
                </div>
                <span className="font-mono text-white">{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <NetworkGraph graph={graph} height={420} />
        <div className="panel rounded-3xl p-6">
          <div className="mb-5">
            <h2 className="font-display text-xl font-semibold">Priority Queue</h2>
            <p className="text-sm text-mist">Devices with the strongest signs of recruitment drift and outbound abuse.</p>
          </div>
          <div className="space-y-3">
            {devices.slice(0, 5).map((device) => (
              <div key={device.device_id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-display text-lg font-semibold text-white">{device.device_id}</div>
                    <div className="mt-1 text-sm text-mist">{device.anomalies.join(', ') || 'No active anomalies'}</div>
                  </div>
                  <div className="rounded-2xl bg-black/20 px-3 py-2 font-mono text-lg text-white">{device.trust_score}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
