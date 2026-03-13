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
    return (
      <div className="rounded-3xl p-6" style={{ border: '1px solid var(--critical-border)', background: 'var(--critical-bg)', color: 'var(--critical-text)' }}>
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="page-hero rounded-3xl p-6">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-[var(--accent-primary)]">Network Map</p>
        <h2 className="mt-2 font-display text-3xl font-semibold">Risk propagation across internal communication paths</h2>
        <p className="mt-2 max-w-3xl text-sm soft-label">
          This command view models how low-trust devices influence adjacent nodes. The graph shows both original trust and propagated trust after local blast-radius decay.
        </p>
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <NetworkGraph graph={graph} height={560} />
        <div className="space-y-6">
          <div className="surface-card rounded-3xl p-6">
            <h3 className="font-display text-xl font-semibold">Propagation Snapshot</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl p-4" style={{ border: '1px solid var(--critical-border)', background: 'var(--critical-bg)' }}>
                <div className="text-xs uppercase tracking-[0.2em]" style={{ color: 'var(--critical-text)' }}>Critical Sources</div>
                <div className="mt-2 font-mono text-3xl" style={{ color: 'var(--text-primary)' }}>{criticalNodes.length}</div>
              </div>
              <div className="rounded-2xl p-4" style={{ border: '1px solid rgba(56,189,248,0.22)', background: 'rgba(14,165,233,0.10)' }}>
                <div className="text-xs uppercase tracking-[0.2em]" style={{ color: '#7dd3fc' }}>Neighbors Impacted</div>
                <div className="mt-2 font-mono text-3xl" style={{ color: 'var(--text-primary)' }}>{decayedNodes.length}</div>
              </div>
            </div>
          </div>

          <div className="surface-card rounded-3xl p-6">
            <h3 className="font-display text-xl font-semibold">Critical Propagation Sources</h3>
            <p className="mt-2 text-sm soft-label">Nodes below trust 40 that should be isolated before trust decay spreads further.</p>
            <div className="mt-5 space-y-3">
              {criticalNodes.map((node) => (
                <div key={node.id} className="rounded-2xl p-4" style={{ border: '1px solid var(--critical-border)', background: 'var(--critical-bg)' }}>
                  <div className="font-display text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{node.label}</div>
                  <div className="mt-2 font-mono text-sm" style={{ color: 'var(--critical-text)' }}>Trust {node.trust_score} | Propagated {node.propagated_trust}</div>
                </div>
              ))}
              {!criticalNodes.length && (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm soft-label">
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
