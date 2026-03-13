import { Background, Controls, MiniMap, ReactFlow } from '@xyflow/react';

function trustColor(score) {
  if (score < 40) {
    return '#ff6b6b';
  }
  if (score < 70) {
    return '#ffb454';
  }
  return '#4be2c5';
}

export default function NetworkGraph({ graph, height = 480 }) {
  const nodes = (graph?.nodes || []).map((node, index) => ({
    id: node.id,
    position: {
      x: 120 + (index % 4) * 220,
      y: 80 + Math.floor(index / 4) * 180,
    },
    data: {
      label: node.label,
      trustScore: Number(node.trust_score ?? 0),
      propagatedTrust: Number(node.propagated_trust ?? node.trust_score ?? 0),
    },
    style: {
      width: 160,
      borderRadius: 24,
      border: `1px solid ${trustColor(Number(node.propagated_trust ?? 0))}`,
      background: 'rgba(7, 19, 31, 0.92)',
      color: '#f7fbff',
      boxShadow: `0 0 0 1px ${trustColor(Number(node.propagated_trust ?? 0))}20, 0 12px 30px rgba(0, 0, 0, 0.24)`,
      padding: 14,
    },
  }));

  const edges = (graph?.edges || []).map((edge) => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    label: `${Number(edge.flows ?? 0)} flows`,
    animated: edge.flows > 10,
    style: {
      stroke: 'rgba(147, 185, 216, 0.45)',
      strokeWidth: Math.max(1.2, edge.flows / 8),
    },
    labelStyle: {
      fill: '#93b9d8',
      fontSize: 11,
    },
  }));

  return (
    <div className="panel rounded-3xl p-4">
      <div className="mb-4 px-2 pt-2">
        <h2 className="font-display text-xl font-semibold">Propagation Graph</h2>
        <p className="text-sm text-mist">Edges represent internal communication. Low-trust nodes push a decay penalty to their neighbors.</p>
      </div>
      <div className="overflow-hidden rounded-[24px] border border-white/10" style={{ height }}>
        <ReactFlow fitView nodes={nodes} edges={edges}>
          <MiniMap
            pannable
            zoomable
            nodeStrokeWidth={3}
            nodeColor={(node) => trustColor(Number(node?.data?.propagatedTrust ?? node?.data?.trustScore ?? 0))}
          />
          <Controls />
          <Background color="rgba(147, 185, 216, 0.12)" gap={24} />
        </ReactFlow>
      </div>
    </div>
  );
}
