import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import { GitBranch, Sparkles } from "lucide-react";
import type { GraphData } from "../types/care";

const COLORS: Record<string, string> = {
  user: "#0f766e",
  clinic: "#c45f38",
  transport: "#d4a017",
  service: "#4f46e5",
  pharmacy: "#0f766e",
};

type Props = {
  graph: GraphData;
};

type GraphNode = GraphData["nodes"][number] & { color: string };
type GraphLink = GraphData["edges"][number];

export function GraphVisualizer({ graph }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<ForceGraphMethods<GraphNode, GraphLink>>();
  const [width, setWidth] = useState(760);
  const [selectedNodeId, setSelectedNodeId] = useState(graph.nodes[0]?.id ?? "");

  const graphData = useMemo(
    () => ({
      nodes: graph.nodes.map((node) => ({ ...node, color: COLORS[node.type] ?? "#64748b" })),
      links: graph.edges.map((edge) => ({ ...edge })),
    }),
    [graph],
  );

  const selectedNode = graphData.nodes.find((node) => node.id === selectedNodeId) ?? graphData.nodes[0] ?? null;

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      const nextWidth = entries[0]?.contentRect.width ?? 760;
      setWidth(Math.max(320, Math.floor(nextWidth)));
    });
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setSelectedNodeId(graph.nodes[0]?.id ?? "");
  }, [graph.nodes]);

  useEffect(() => {
    if (!graphRef.current || graphData.nodes.length === 0) {
      return;
    }
    const chargeForce = graphRef.current.d3Force("charge");
    if (chargeForce && typeof chargeForce.strength === "function") {
      chargeForce.strength(-280);
    }
    const linkForce = graphRef.current.d3Force("link");
    if (linkForce && typeof linkForce.distance === "function") {
      linkForce.distance((link: GraphLink) => (link.label === "reachable_by" ? 180 : 150));
    }
    graphRef.current.d3ReheatSimulation();
    const timeout = window.setTimeout(() => {
      graphRef.current?.zoomToFit(450, 90);
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [graphData]);

  return (
    <section className="rounded-[28px] border border-[#E6DDD1] bg-white p-5 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#ECE4D9] bg-[#FFF7ED] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#9A4E2D]">
            <GitBranch className="h-3.5 w-3.5" />
            Interactive graph
          </div>
          <h3 className="mt-3 text-xl font-semibold text-slate-900">How the route was assembled</h3>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            Drag nodes, zoom the canvas, and inspect the links between clinics, services, transit, and prescription support.
          </p>
        </div>
        <div className="rounded-2xl border border-[#E6DDD1] bg-[#FCFAF7] px-4 py-3 text-sm text-slate-600">
          <p className="font-semibold text-slate-900">Route graph</p>
          <p className="mt-1">{graph.nodes.length} nodes • {graph.edges.length} links</p>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <div ref={containerRef} className="overflow-hidden rounded-[24px] border border-[#E6DDD1] bg-[#FBF8F3]">
          <ForceGraph2D
            ref={graphRef}
            width={width}
            height={520}
            graphData={graphData}
            backgroundColor="#FBF8F3"
            dagMode="lr"
            dagLevelDistance={180}
            cooldownTicks={180}
            d3VelocityDecay={0.22}
            linkColor={() => "#CFC4B5"}
            linkWidth={(link) => Math.max(1.25, ((link.weight as number | undefined) ?? 30) / 45)}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            nodeLabel={(node) => `${node.label}${node.detail ? ` - ${node.detail}` : ""}`}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.label;
              const fontSize = Math.max(11, 14 / globalScale);
              ctx.beginPath();
              ctx.arc(node.x ?? 0, node.y ?? 0, node.type === "user" ? 12 : 9, 0, 2 * Math.PI, false);
              ctx.fillStyle = node.color;
              ctx.fill();

              ctx.font = `600 ${fontSize}px Manrope, sans-serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "top";
              ctx.fillStyle = "#0f172a";
              ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + 14);
            }}
            onNodeClick={(node) => {
              setSelectedNodeId(node.id ?? "");
              if (typeof node.x === "number" && typeof node.y === "number") {
                graphRef.current?.centerAt(node.x, node.y, 500);
                graphRef.current?.zoom(2.2, 500);
              }
            }}
            onBackgroundClick={() => setSelectedNodeId(graphData.nodes[0]?.id ?? "")}
          />
        </div>

        <aside className="rounded-[24px] border border-[#E6DDD1] bg-[#FCFAF7] p-4">
          <div className="flex items-center gap-2 text-[#9A4E2D]">
            <Sparkles className="h-4 w-4" />
            <p className="text-xs font-semibold uppercase tracking-[0.18em]">Selected node</p>
          </div>
          {selectedNode ? (
            <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
              <div className="rounded-2xl border border-[#E6DDD1] bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{selectedNode.label}</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedNode.type}</p>
                  </div>
                  {typeof selectedNode.score === "number" && (
                    <div className="rounded-2xl bg-[#EEF7F3] px-3 py-2 text-right">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Score</p>
                      <p className="text-lg font-semibold text-[#0f766e]">{selectedNode.score}</p>
                    </div>
                  )}
                </div>
                {selectedNode.detail && <p className="mt-3 text-sm leading-6 text-slate-700">{selectedNode.detail}</p>}
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Connected edges</p>
                  <div className="mt-2 space-y-2">
                    {graph.edges
                      .filter((edge) => edge.source === selectedNode.id || edge.target === selectedNode.id)
                      .map((edge) => (
                        <div key={`${edge.source}-${edge.target}-${edge.label}`} className="rounded-2xl border border-[#E6DDD1] bg-white px-3 py-2 text-sm text-slate-700">
                          <span className="font-medium text-slate-900">{edge.label}</span>
                          {typeof edge.weight === "number" ? ` • ${edge.weight}` : ""}
                        </div>
                      ))}
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Legend</p>
                <div className="mt-2 grid gap-2">
                  {Object.entries(COLORS).map(([type, color]) => (
                    <div key={type} className="flex items-center gap-2 rounded-2xl border border-[#E6DDD1] bg-white px-3 py-2 text-sm text-slate-700">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                      {type}
                    </div>
                  ))}
                </div>
                <div className="mt-4 rounded-2xl border border-[#E6DDD1] bg-white p-4 text-sm leading-6 text-slate-600">
                  The graph now flows from left to right so user input, ranked clinics, support services, and transit links stay visually separated.
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-600">Run a route to inspect its graph.</p>
          )}
        </aside>
      </div>
    </section>
  );
}
