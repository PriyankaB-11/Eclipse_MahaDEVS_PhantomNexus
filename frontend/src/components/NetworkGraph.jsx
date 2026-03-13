import { useEffect, useMemo, useState } from 'react';
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';

function DeviceNode({ data }) {
  const tone = trustColor(Number(data.propagatedTrust ?? data.trustScore ?? 0));

  return (
    <>
      <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-0 !bg-slate-500/60" />
      <div
        className="min-w-[190px] rounded-[22px] border px-4 py-3"
        style={{
          borderColor: `${tone}55`,
          background: 'var(--graph-node-bg)',
          boxShadow: `0 0 0 1px ${tone}26, var(--graph-node-shadow)`,
          color: 'var(--text-primary)',
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="font-display text-base font-semibold">{data.label}</div>
            <div className="mt-1 font-mono text-[11px] uppercase tracking-[0.24em] soft-label">{data.riskLevel}</div>
          </div>
          <div
            className="rounded-full px-2 py-1 font-mono text-xs font-semibold"
            style={{ backgroundColor: `${tone}22`, color: tone }}
          >
            {Math.round(Number(data.trustScore ?? 0))}
          </div>
        </div>
        <div className="mt-3 space-y-2">
          <div>
            <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] soft-label">
              <span>Propagated Trust</span>
              <span>{Math.round(Number(data.propagatedTrust ?? 0))}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full" style={{ backgroundColor: 'var(--surface-subtle)' }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.max(4, Math.min(100, Number(data.propagatedTrust ?? 0)))}%`,
                  background: `linear-gradient(90deg, ${tone} 0%, ${tone}aa 100%)`,
                }}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs soft-label">
            <div className="rounded-xl border px-2 py-2" style={{ borderColor: 'var(--border-soft)', backgroundColor: 'var(--surface-subtle)' }}>
              <div className="uppercase tracking-[0.14em] text-[10px]">Base</div>
              <div className="mt-1 font-mono" style={{ color: 'var(--text-primary)' }}>
                {Number(data.trustScore ?? 0).toFixed(1)}
              </div>
            </div>
            <div className="rounded-xl border px-2 py-2" style={{ borderColor: 'var(--border-soft)', backgroundColor: 'var(--surface-subtle)' }}>
              <div className="uppercase tracking-[0.14em] text-[10px]">Decay</div>
              <div className="mt-1 font-mono" style={{ color: 'var(--text-primary)' }}>
                {(Number(data.trustScore ?? 0) - Number(data.propagatedTrust ?? 0)).toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-0 !bg-slate-500/60" />
    </>
  );
}

function trustColor(score) {
  if (score < 40) {
    return '#ff6b6b';
  }
  if (score < 70) {
    return '#ffb454';
  }
  return '#4be2c5';
}

function mapGraphToNodes(graph) {
  return (graph?.nodes || []).map((node, index) => ({
    id: node.id,
    type: 'deviceNode',
    position: node.position || {
      x: 80 + (index % 4) * 260,
      y: 70 + Math.floor(index / 4) * 210,
    },
    data: {
      label: node.label,
      trustScore: Number(node.trust_score ?? 0),
      propagatedTrust: Number(node.propagated_trust ?? node.trust_score ?? 0),
      riskLevel: node.risk_level ?? 'unknown',
    },
  }));
}

function mapGraphToEdges(graph) {
  return (graph?.edges || []).map((edge) => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    label: `${Number(edge.flows ?? 0)} flows`,
    animated: Number(edge.flows ?? 0) > 10,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: 'var(--graph-edge)',
    },
    style: {
      stroke: 'var(--graph-edge)',
      strokeWidth: Math.max(1.6, Number(edge.flows ?? 0) / 8),
    },
    labelStyle: {
      fill: 'var(--chart-axis)',
      fontSize: 11,
    },
    labelBgStyle: {
      fill: 'var(--chart-tooltip-bg)',
      fillOpacity: 1,
    },
    labelBgPadding: [6, 3],
    labelBgBorderRadius: 8,
  }));
}

export default function NetworkGraph({ graph, height = 480 }) {
  const [isInteractive, setIsInteractive] = useState(true);
  const nodeTypes = useMemo(() => ({ deviceNode: DeviceNode }), []);
  const [nodes, setNodes, onNodesChange] = useNodesState(() => mapGraphToNodes(graph));
  const [edges, setEdges, onEdgesChange] = useEdgesState(() => mapGraphToEdges(graph));

  useEffect(() => {
    setNodes(mapGraphToNodes(graph));
    setEdges(mapGraphToEdges(graph));
  }, [graph, setEdges, setNodes]);

  const criticalNodes = nodes.filter((node) => Number(node.data.trustScore) < 40).length;
  const warningNodes = nodes.filter((node) => Number(node.data.trustScore) >= 40 && Number(node.data.trustScore) < 70).length;
  const averageDecay = nodes.length
    ? (
        nodes.reduce(
          (total, node) => total + (Number(node.data.trustScore ?? 0) - Number(node.data.propagatedTrust ?? 0)),
          0,
        ) / nodes.length
      ).toFixed(1)
    : '0.0';

  if (!nodes.length) {
    return (
      <div className="panel rounded-3xl p-6">
        <div className="mb-4">
          <h2 className="font-display text-xl font-semibold">Propagation Graph</h2>
          <p className="text-sm soft-label">No graph data is available for the current simulation snapshot.</p>
        </div>
        <div className="rounded-[24px] border border-dashed border-white/10 bg-white/5 px-6 py-16 text-center text-sm soft-label">
          Start the backend dataset generator and reload the dashboard to render communication paths.
        </div>
      </div>
    );
  }

  return (
    <div className="surface-card rounded-3xl p-4 sm:p-5">
      <div className="mb-4 grid gap-4 px-2 pt-2 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <h2 className="font-display text-xl font-semibold">Propagation Graph</h2>
          <p className="text-sm soft-label">Edges represent internal communication. Critical nodes spread trust decay through the local neighborhood, exposing likely blast radius.</p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-2xl px-3 py-3" style={{ border: '1px solid var(--critical-border)', background: 'var(--critical-bg)' }}>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: 'var(--critical-text)' }}>Critical</div>
            <div className="mt-1 font-mono text-xl" style={{ color: 'var(--text-primary)' }}>
              {criticalNodes}
            </div>
          </div>
          <div className="rounded-2xl px-3 py-3" style={{ border: '1px solid var(--warning-border)', background: 'var(--warning-bg)' }}>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: 'var(--warning-text)' }}>Warning</div>
            <div className="mt-1 font-mono text-xl" style={{ color: 'var(--text-primary)' }}>
              {warningNodes}
            </div>
          </div>
          <div className="rounded-2xl px-3 py-3" style={{ border: '1px solid var(--success-border)', background: 'var(--success-bg)' }}>
            <div className="text-[11px] uppercase tracking-[0.18em]" style={{ color: 'var(--success-text)' }}>Avg Decay</div>
            <div className="mt-1 font-mono text-xl" style={{ color: 'var(--text-primary)' }}>
              {averageDecay}
            </div>
          </div>
        </div>
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-2 px-2 text-xs soft-label">
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Node halo = propagated trust</span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Arrow thickness = flow volume</span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Animated edge = heavy internal chatter</span>
        <span
          className="ml-auto rounded-full border px-3 py-1 font-mono"
          style={isInteractive
            ? { background: 'var(--success-bg)', color: 'var(--success-text)', borderColor: 'var(--success-border)' }
            : { background: 'var(--surface-subtle)', color: 'var(--text-muted)', borderColor: 'var(--border-soft)' }
          }
        >
          {isInteractive ? 'interactive' : 'locked'}
        </span>
      </div>
      <div className="overflow-hidden rounded-[24px] border border-white/10" style={{ height, background: 'var(--graph-canvas-bg)' }}>
        <ReactFlow
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.16 }}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          nodesDraggable={isInteractive}
          nodesConnectable={false}
          elementsSelectable={isInteractive}
          panOnDrag={isInteractive}
          panOnScroll={isInteractive}
          zoomOnScroll={isInteractive}
          zoomOnPinch={isInteractive}
          zoomOnDoubleClick={isInteractive}
          preventScrolling={false}
          proOptions={{ hideAttribution: true }}
          defaultEdgeOptions={{ type: 'smoothstep' }}
        >
          <MiniMap
            pannable={isInteractive}
            zoomable={isInteractive}
            ariaLabel="Propagation minimap"
            maskColor="var(--graph-mask)"
            style={{ backgroundColor: 'var(--graph-minimap-bg)', border: '1px solid var(--graph-minimap-border)' }}
            nodeStrokeWidth={3}
            nodeColor={(node) => trustColor(Number(node?.data?.propagatedTrust ?? node?.data?.trustScore ?? 0))}
          />
          <Controls className="!shadow-none" showInteractive onInteractiveChange={setIsInteractive} />
          <Background color="var(--chart-grid)" gap={24} />
        </ReactFlow>
      </div>
    </div>
  );
}
