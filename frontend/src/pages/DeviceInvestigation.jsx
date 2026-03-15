import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Link, useParams } from 'react-router-dom';
import { getDevice, getDeviceInvestigation, getDeviceReportUrl } from '../services/api';


function toPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0;
  }
  // Backend scores are mostly 0..1. If already percent-like, keep them as-is.
  const scaled = numeric <= 1 ? numeric * 100 : numeric;
  return Math.max(0, Math.min(100, Number(scaled.toFixed(2))));
}

function Gauge({ value }) {
  const degrees = Math.max(0, Math.min(100, value)) * 3.6;
  return (
    <div className="flex items-center gap-5">
      <div
        className="relative h-36 w-36 rounded-full"
        style={{ background: `conic-gradient(var(--accent-primary) ${degrees}deg, rgba(255,255,255,0.08) ${degrees}deg 360deg)` }}
      >
        <div className="absolute inset-3 flex items-center justify-center rounded-full bg-[var(--app-bg)]">
          <div className="text-center">
            <div className="font-mono text-3xl font-semibold text-white">{Math.round(value)}</div>
            <div className="text-xs uppercase tracking-[0.24em] soft-label">Trust</div>
          </div>
        </div>
      </div>
      <div className="max-w-xs">
        <div className="font-display text-xl font-semibold">Trust Score Gauge</div>
        <p className="mt-2 text-sm soft-label">A high score keeps the device eligible for adaptive learning. Lower scores freeze baseline updates and elevate the investigation priority.</p>
      </div>
    </div>
  );
}

export default function DeviceInvestigation() {
  const { deviceId } = useParams();
  const [detail, setDetail] = useState(null);
  const [investigation, setInvestigation] = useState(null);
  const [error, setError] = useState('');
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setError('');
        setNotFound(false);
        const [deviceDetail, deviceInvestigation] = await Promise.all([
          getDevice(deviceId),
          getDeviceInvestigation(deviceId),
        ]);
        setDetail(deviceDetail);
        setInvestigation(deviceInvestigation);
      } catch (loadError) {
        const message = loadError.message || 'Failed to load device investigation';
        if (message.toLowerCase().includes('device not found')) {
          setNotFound(true);
          setDetail(null);
          setInvestigation(null);
          return;
        }
        setError(message);
      }
    }

    load();
  }, [deviceId]);

  const anomalyData = investigation
    ? [
        { name: 'Drift', value: toPercent(investigation?.anomaly_scores?.drift_score), color: '#f59e0b' },
        { name: 'Anomaly', value: toPercent(investigation?.anomaly_scores?.anomaly_score), color: '#ef4444' },
        { name: 'Botnet', value: toPercent(investigation?.botnet_probability), color: '#14b8a6' },
        { name: 'Correlation', value: toPercent(investigation?.peer_correlations?.correlation_score), color: '#60a5fa' },
      ]
    : [];

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  if (notFound) {
    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm soft-label hover:bg-white/10" to="/devices">
            Back to Devices
          </Link>
        </div>

        <section className="surface-card rounded-3xl p-6">
          <p className="font-mono text-xs uppercase tracking-[0.34em] text-[var(--warning-text)]">Device Unavailable</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">{deviceId}</h2>
          <p className="mt-3 max-w-3xl text-sm soft-label">
            This device is not present in the active dataset anymore. This usually happens after switching the backend dataset or uploading a new CSV.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link className="btn-accent inline-flex rounded-xl px-4 py-2 text-sm font-semibold" to="/devices">
              Open Current Device List
            </Link>
            <Link className="inline-flex rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10" to="/dashboard">
              Go to Dashboard
            </Link>
          </div>
        </section>
      </div>
    );
  }

  if (!detail || !investigation) {
    return <div className="surface-card rounded-3xl p-6 soft-label">Loading device investigation...</div>;
  }

  const correlatedPeers = investigation.peer_correlations.correlated_peers || [];
  const llmSummary = investigation.llm_summary || {};
  const reportUrl = getDeviceReportUrl(deviceId);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm soft-label hover:bg-white/10" to="/devices">
          Back to Devices
        </Link>
        <a className="btn-accent inline-flex rounded-xl px-4 py-2 text-sm font-semibold" href={reportUrl} target="_blank" rel="noreferrer">
          Download PDF Report
        </a>
      </div>

      <section className="page-hero rounded-3xl p-6">
        <p className="font-mono text-xs uppercase tracking-[0.34em] text-[var(--accent-primary)]">Device Investigation</p>
        <h2 className="mt-2 font-display text-3xl font-semibold">{deviceId}</h2>
        <p className="mt-2 max-w-3xl text-sm soft-label">
          Review anomaly evidence, coordinated peer behavior, gated learning state, and the SOC investigation narrative for this device.
        </p>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="surface-card rounded-3xl p-6">
          <Gauge value={investigation.trust_score} />
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="panel-soft rounded-2xl p-4">
              <div className="text-sm soft-label">Current Status</div>
              <div className="mt-2 text-lg font-semibold capitalize text-white">{detail.summary.status}</div>
            </div>
            <div className="panel-soft rounded-2xl p-4">
              <div className="text-sm soft-label">Learning State</div>
              <div className="mt-2 text-lg font-semibold capitalize text-white">{investigation.gated_learning.learning_state}</div>
            </div>
          </div>
          <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm soft-label">
            {investigation.gated_learning.freeze_reasons.length
              ? `Baseline frozen because: ${investigation.gated_learning.freeze_reasons.join(', ')}`
              : 'Adaptive learning remains enabled because the device passed trust, anomaly, and peer-correlation gates.'}
          </div>
        </div>

        <div className="surface-card rounded-3xl p-6">
          <div className="mb-4">
            <h3 className="font-display text-2xl font-semibold">Anomaly Chart</h3>
            <p className="text-sm soft-label">Normalized scores across drift, behavior anomaly, botnet likelihood, and peer coordination.</p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={anomalyData}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="var(--chart-axis)" />
                <YAxis stroke="var(--chart-axis)" domain={[0, 100]} />
                <Tooltip
                  formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Score']}
                  contentStyle={{
                    background: 'var(--chart-tooltip-bg)',
                    border: '1px solid var(--chart-tooltip-border)',
                    borderRadius: '16px',
                    color: 'var(--text-primary)',
                  }}
                />
                <Bar dataKey="value" radius={[12, 12, 0, 0]} minPointSize={5}>
                  {anomalyData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                  <LabelList dataKey="value" position="top" formatter={(value) => `${Number(value).toFixed(1)}%`} fill="var(--text-primary)" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="surface-card rounded-3xl p-6">
          <div className="mb-4">
            <h3 className="font-display text-2xl font-semibold">Correlated Devices</h3>
            <p className="text-sm soft-label">Devices with matching anomaly vectors inside overlapping suspicious time windows.</p>
          </div>
          <div className="space-y-3">
            {correlatedPeers.length ? (
              correlatedPeers.map((peer) => (
                <div key={peer.device_id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="font-display text-lg font-semibold text-white">{peer.device_id}</div>
                      <div className="mt-1 text-sm soft-label">Shared suspicious windows: {peer.shared_suspicious_windows}</div>
                    </div>
                    <div className="rounded-2xl bg-black/20 px-3 py-2 font-mono text-white">{Math.round(peer.correlation_score * 100)}%</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm soft-label">No coordinated peers were detected for this device.</div>
            )}
          </div>
        </div>

        <div className="surface-card rounded-3xl p-6">
          <div className="mb-4">
            <h3 className="font-display text-2xl font-semibold">Investigation Summary</h3>
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-sm soft-label">Threat Explanation</div>
              <p className="mt-2 text-sm text-white">{llmSummary.threat_explanation}</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="text-sm soft-label">Possible Attack Stage</div>
                <div className="mt-2 text-white capitalize">{llmSummary.possible_attack_stage}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="text-sm soft-label">Confidence</div>
                <div className="mt-2 font-mono text-white">{Math.round((llmSummary.confidence || 0) * 100)}%</div>
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-sm soft-label">Evidence</div>
              <ul className="mt-2 space-y-2 text-sm text-white">
                {(llmSummary.evidence || []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-sm soft-label">Recommended Mitigation</div>
              <ul className="mt-2 space-y-2 text-sm text-white">
                {(llmSummary.recommended_mitigation || []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}