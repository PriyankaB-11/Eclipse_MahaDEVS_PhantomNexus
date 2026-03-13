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

  if (error) {
    return <div className="panel rounded-3xl p-6 text-red-200">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="panel rounded-3xl p-6">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-glow/80">Network Map</p>
        <h2 className="mt-2 font-display text-3xl font-semibold">Risk propagation across internal communication paths</h2>
        <p className="mt-2 max-w-3xl text-sm text-mist">
          Graph nodes inherit their device trust score and a propagated trust value after neighboring critical nodes spread a decay penalty.
        </p>
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <NetworkGraph graph={graph} height={560} />
        <div className="panel rounded-3xl p-6">
          <h3 className="font-display text-xl font-semibold">Critical Propagation Sources</h3>
          <p className="mt-2 text-sm text-mist">Nodes below trust 40 that should be isolated before trust decay spreads further.</p>
          <div className="mt-5 space-y-3">
            {criticalNodes.map((node) => (
              <div key={node.id} className="rounded-2xl border border-red-400/20 bg-red-500/10 p-4">
                <div className="font-display text-lg font-semibold text-white">{node.label}</div>
                <div className="mt-2 font-mono text-sm text-red-100">Trust {node.trust_score} | Propagated {node.propagated_trust}</div>
              </div>
            ))}
            {!criticalNodes.length && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-mist">
                No critical nodes in the current simulation window.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
