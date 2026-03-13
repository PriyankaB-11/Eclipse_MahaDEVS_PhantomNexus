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
        className="min-w-[190px] rounded-[22px] border px-4 py-3 text-slate-900"
        style={{
          borderColor: `${tone}55`,
          background: 'var(--graph-node-bg)',
          boxShadow: `0 0 0 1px ${tone}26, var(--graph-node-shadow)`,
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="font-display text-base font-semibold">{data.label}</div>
            <div className="mt-1 font-mono text-[11px] uppercase tracking-[0.24em] text-slate-500">{data.riskLevel}</div>
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
            <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-slate-500">
              <span>Propagated Trust</span>
              <span>{Math.round(Number(data.propagatedTrust ?? 0))}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.max(4, Math.min(100, Number(data.propagatedTrust ?? 0)))}%`,
                  background: `linear-gradient(90deg, ${tone} 0%, ${tone}aa 100%)`,
                }}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-500">
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-2 py-2">
              <div className="uppercase tracking-[0.14em] text-[10px]">Base</div>
              <div className="mt-1 font-mono text-slate-900">{Number(data.trustScore ?? 0).toFixed(1)}</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-2 py-2">
              <div className="uppercase tracking-[0.14em] text-[10px]">Decay</div>
              <div className="mt-1 font-mono text-slate-900">
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
      color: 'rgba(71, 85, 105, 0.55)',
    },
    style: {
      stroke: 'rgba(71, 85, 105, 0.45)',
      strokeWidth: Math.max(1.6, Number(edge.flows ?? 0) / 8),
    },
    labelStyle: {
      fill: '#475569',
      fontSize: 11,
    },
    labelBgStyle: {
      fill: 'rgba(255, 255, 255, 0.95)',
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
          <h2 className="font-display text-xl font-semibold text-slate-900">Propagation Graph</h2>
          <p className="text-sm text-slate-500">No graph data is available for the current simulation snapshot.</p>
        </div>
        <div className="rounded-[24px] border border-dashed border-slate-200 bg-white px-6 py-16 text-center text-sm text-slate-500">
          Start the backend dataset generator and reload the dashboard to render communication paths.
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-[0_22px_55px_rgba(148,163,184,0.16)] sm:p-5">
      <div className="mb-4 grid gap-4 px-2 pt-2 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <h2 className="font-display text-xl font-semibold text-slate-900">Propagation Graph</h2>
          <p className="text-sm text-slate-600">Edges represent internal communication. Critical nodes spread trust decay through the local neighborhood, exposing likely blast radius.</p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-2xl border border-red-200 bg-red-50 px-3 py-3">
            <div className="text-[11px] uppercase tracking-[0.18em] text-red-500">Critical</div>
            <div className="mt-1 font-mono text-xl text-slate-900">{criticalNodes}</div>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3">
            <div className="text-[11px] uppercase tracking-[0.18em] text-amber-600">Warning</div>
            <div className="mt-1 font-mono text-xl text-slate-900">{warningNodes}</div>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-3">
            <div className="text-[11px] uppercase tracking-[0.18em] text-emerald-600">Avg Decay</div>
            <div className="mt-1 font-mono text-xl text-slate-900">{averageDecay}</div>
          </div>
        </div>
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-2 px-2 text-xs text-slate-600">
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1">Node halo = propagated trust</span>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1">Arrow thickness = flow volume</span>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1">Animated edge = heavy internal chatter</span>
        <span className={`ml-auto rounded-full px-3 py-1 font-mono ${isInteractive ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'}`}>
          {isInteractive ? 'interactive' : 'locked'}
        </span>
      </div>
      <div className="overflow-hidden rounded-[24px] border border-slate-200" style={{ height, background: 'var(--graph-canvas-bg)' }}>
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
