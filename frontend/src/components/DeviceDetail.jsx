export default function DeviceDetail({ detail }) {
  if (!detail) {
    return null;
  }

  const summary = detail.summary;
  const explanation = detail.explanation;
  const digitalTwin = detail.digital_twin;
  const evidenceEntries = Object.entries(explanation.evidence || {});

  return (
    <div className="grid gap-6 lg:grid-cols-[1.25fr_0.95fr]">
      <section className="panel rounded-3xl p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-glow/80">Device Investigation</p>
            <h2 className="font-display text-3xl font-semibold text-white">{detail.device_id}</h2>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 px-5 py-3 text-right">
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-mist">Trust Score</div>
            <div className="font-mono text-3xl font-semibold text-white">{summary.trust_score}</div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="panel-soft rounded-2xl p-4">
            <div className="text-sm text-mist">Current Status</div>
            <div className="mt-2 text-lg font-semibold capitalize text-white">{summary.status}</div>
          </div>
          <div className="panel-soft rounded-2xl p-4">
            <div className="text-sm text-mist">Drift Score</div>
            <div className="mt-2 font-mono text-lg text-white">{summary.drift_score}</div>
          </div>
          <div className="panel-soft rounded-2xl p-4">
            <div className="text-sm text-mist">Botnet Probability</div>
            <div className="mt-2 font-mono text-lg text-white">{Math.round(summary.botnet_probability * 100)}%</div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="panel-soft rounded-2xl p-4">
            <h3 className="mb-3 font-display text-lg font-semibold">Detected Anomalies</h3>
            <ul className="space-y-2 text-sm text-mist">
              {explanation.reason.map((reason) => (
                <li key={reason} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-white">
                  {reason}
                </li>
              ))}
            </ul>
          </div>
          <div className="panel-soft rounded-2xl p-4">
            <h3 className="mb-3 font-display text-lg font-semibold">Recommended Action</h3>
            <p className="text-sm text-white">{explanation.recommended_action}</p>
            <div className="mt-4 text-sm text-mist">
              Baseline ports: {detail.phantom_twin.normal_ports.join(', ') || 'none'}
            </div>
            <div className="mt-2 text-sm text-mist">
              Baseline destinations: {detail.phantom_twin.common_destinations.slice(0, 4).join(', ') || 'none'}
            </div>
          </div>
        </div>

        {digitalTwin && (
          <div className="mt-6 panel-soft rounded-2xl p-4">
            <h3 className="mb-3 font-display text-lg font-semibold">Digital Twin State</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <div className="text-mist">Behavioral State</div>
                <div className="mt-1 capitalize text-white">{digitalTwin.behavioral_state}</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <div className="text-mist">Twin Confidence</div>
                <div className="mt-1 text-white">{Math.round(digitalTwin.confidence * 100)}%</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <div className="text-mist">Flow Delta</div>
                <div className="mt-1 text-white">{digitalTwin.deviations.flow_frequency_delta_pct}%</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <div className="text-mist">External Delta</div>
                <div className="mt-1 text-white">{digitalTwin.deviations.external_connection_delta}</div>
              </div>
            </div>
            <div className="mt-3 text-sm text-mist">
              New ports: {digitalTwin.deviations.new_ports.join(', ') || 'none'}
            </div>
            <div className="mt-1 text-sm text-mist">
              New destinations: {digitalTwin.deviations.new_destinations.slice(0, 4).join(', ') || 'none'}
            </div>
          </div>
        )}
      </section>

      <section className="panel rounded-3xl p-6">
        <h3 className="mb-4 font-display text-xl font-semibold">Evidence Ledger</h3>
        <div className="space-y-3">
          {evidenceEntries.map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="font-mono text-xs uppercase tracking-[0.2em] text-mist">{key}</div>
              <div className="mt-2 text-sm text-white">{Array.isArray(value) ? value.join(', ') : JSON.stringify(value)}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
