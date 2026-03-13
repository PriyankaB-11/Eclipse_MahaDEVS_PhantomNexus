import { useEffect, useState } from 'react';
import NetworkGraph from '../components/NetworkGraph';
import { getRiskGraph } from '../services/api';

export default function NetworkMap() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setGraph(await getRiskGraph());
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    load();
  }, []);

  const criticalNodes = graph.nodes.filter((node) => node.trust_score < 40);
  const decayedNodes = graph.nodes.filter((node) => node.propagated_trust < node.trust_score);

  if (error) {
    return <div className="rounded-3xl border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-[0_22px_55px_rgba(148,163,184,0.14)]">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-emerald-600">Network Map</p>
        <h2 className="mt-2 font-display text-3xl font-semibold text-slate-900">Risk propagation across internal communication paths</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          This command view models how low-trust devices influence adjacent nodes. The graph shows both original trust and propagated trust after local blast-radius decay.
        </p>
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <NetworkGraph graph={graph} height={560} />
        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(148,163,184,0.12)]">
            <h3 className="font-display text-xl font-semibold text-slate-900">Propagation Snapshot</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-red-500">Critical Sources</div>
                <div className="mt-2 font-mono text-3xl text-slate-900">{criticalNodes.length}</div>
              </div>
              <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-sky-600">Neighbors Impacted</div>
                <div className="mt-2 font-mono text-3xl text-slate-900">{decayedNodes.length}</div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(148,163,184,0.12)]">
            <h3 className="font-display text-xl font-semibold text-slate-900">Critical Propagation Sources</h3>
            <p className="mt-2 text-sm text-slate-600">Nodes below trust 40 that should be isolated before trust decay spreads further.</p>
            <div className="mt-5 space-y-3">
              {criticalNodes.map((node) => (
                <div key={node.id} className="rounded-2xl border border-red-200 bg-red-50 p-4">
                  <div className="font-display text-lg font-semibold text-slate-900">{node.label}</div>
                  <div className="mt-2 font-mono text-sm text-red-600">Trust {node.trust_score} | Propagated {node.propagated_trust}</div>
                </div>
              ))}
              {!criticalNodes.length && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                  No critical nodes in the current simulation window.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
