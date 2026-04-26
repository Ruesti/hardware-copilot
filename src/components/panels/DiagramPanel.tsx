import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type OnConnect,
  type NodeMouseHandler,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import {
  fetchDiagram,
  updateBlockPosition,
  createConnection,
  deleteConnection,
  suggestConnections,
  describeBlockCircuit,
} from "../../api/diagram";
import { BlockNode, type BlockNodeData } from "../diagram/BlockNode";
import { StatusBadge } from "../ui/StatusBadge";
import type { BlockConnection, ComponentItem, DiagramBlock, TrustLevel } from "../../types/project";

type Props = {
  projectId: string;
  components: ComponentItem[];
};

// ── connection type styling ────────────────────────────────────────────────────

const CONN_COLOR: Record<string, string> = {
  power:   "#f59e0b",
  gnd:     "#6b7280",
  signal:  "#3b82f6",
  i2c:     "#a855f7",
  spi:     "#ec4899",
  uart:    "#22c55e",
  custom:  "#14b8a6",
};

const CONN_TYPES = ["power", "gnd", "signal", "i2c", "spi", "uart", "custom"];

function edgeStyle(connType: string): React.CSSProperties {
  return { stroke: CONN_COLOR[connType] ?? CONN_COLOR.signal, strokeWidth: 2 };
}

// ── helpers ───────────────────────────────────────────────────────────────────

function autoLayout(blocks: DiagramBlock[]): Record<string, { x: number; y: number }> {
  const COLS = 3;
  const W = 280, H = 200;
  const positions: Record<string, { x: number; y: number }> = {};
  blocks.forEach((b, i) => {
    positions[b.id] = {
      x: (i % COLS) * W + 60,
      y: Math.floor(i / COLS) * H + 60,
    };
  });
  return positions;
}

function blocksToNodes(
  blocks: DiagramBlock[],
  components: ComponentItem[],
  useAutoLayout: boolean
): Node<BlockNodeData>[] {
  const autoPos = useAutoLayout ? autoLayout(blocks) : {};
  return blocks.map((b, i) => {
    const hasPos = b.posX !== 0 || b.posY !== 0;
    const pos = hasPos && !useAutoLayout
      ? { x: b.posX, y: b.posY }
      : (autoPos[b.id] ?? { x: (i % 3) * 280 + 60, y: Math.floor(i / 3) * 200 + 60 });
    return {
      id: b.id,
      type: "blockNode",
      position: pos,
      data: {
        name: b.name,
        description: b.description,
        trustLevel: b.trustLevel,
        componentCount: components.filter((c) => c.blockId === b.id).length,
        selected: false,
      },
    };
  });
}

function connectionsToEdges(connections: BlockConnection[]): Edge[] {
  return connections.map((c) => ({
    id: c.id,
    source: c.sourceBlockId,
    target: c.targetBlockId,
    label: c.label || undefined,
    type: "smoothstep",
    style: edgeStyle(c.connType),
    labelStyle: { fill: CONN_COLOR[c.connType] ?? "#a1a1aa", fontSize: 11, fontWeight: 500 },
    labelBgStyle: { fill: "#111114", fillOpacity: 0.85 },
    data: { connType: c.connType, connId: c.id },
  }));
}

// ── custom node types (stable reference) ──────────────────────────────────────
const NODE_TYPES = { blockNode: BlockNode };

// ── component ─────────────────────────────────────────────────────────────────

export function DiagramPanel({ projectId, components }: Props) {
  return (
    <ReactFlowProvider>
      <DiagramInner projectId={projectId} components={components} />
    </ReactFlowProvider>
  );
}

function DiagramInner({ projectId, components }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<BlockNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const [diagramBlocks, setDiagramBlocks] = useState<DiagramBlock[]>([]);
  const [connections, setConnections]     = useState<BlockConnection[]>([]);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);

  const [loading, setLoading]         = useState(true);
  const [suggesting, setSuggesting]   = useState(false);
  const [error, setError]             = useState<string | null>(null);

  // new connection form
  const [pendingEdge, setPendingEdge] = useState<{ source: string; target: string } | null>(null);
  const [connLabel, setConnLabel]     = useState("");
  const [connType, setConnType]       = useState("signal");

  // per-block circuit description
  const [circuitBlockId, setCircuitBlockId] = useState<string | null>(null);
  const [schematic, setSchematic]           = useState<string | null>(null);
  const [schematicLoading, setSchematicLoading] = useState(false);
  const [schematicError, setSchematicError] = useState<string | null>(null);

  const posTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // ── load ────────────────────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchDiagram(projectId);
        if (cancelled) return;
        setDiagramBlocks(data.blocks);
        setConnections(data.connections);
        setNodes(blocksToNodes(data.blocks, components, false));
        setEdges(connectionsToEdges(data.connections));
        setLoading(false);

        // Auto-suggest connections when diagram has none yet
        if (data.connections.length === 0 && data.blocks.length > 1) {
          setSuggesting(true);
          try {
            const result = await suggestConnections(projectId);
            if (cancelled) return;
            const conns = result.connections as BlockConnection[];
            setConnections(conns);
            setEdges(connectionsToEdges(conns));
          } catch {
            // non-critical — user can trigger manually
          } finally {
            if (!cancelled) setSuggesting(false);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      }
    };

    load();
    return () => { cancelled = true; };
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // update component counts when components prop changes
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: {
          ...n.data,
          componentCount: components.filter((c) => c.blockId === n.id).length,
        },
      }))
    );
  }, [components, setNodes]);

  // ── node drag → save position (debounced) ───────────────────────────────────

  const onNodeDragStop: NodeMouseHandler = useCallback(
    (_evt, node) => {
      clearTimeout(posTimers.current[node.id]);
      posTimers.current[node.id] = setTimeout(() => {
        updateBlockPosition(projectId, node.id, node.position.x, node.position.y)
          .catch(console.error);
      }, 600);
    },
    [projectId]
  );

  // ── connect two nodes ────────────────────────────────────────────────────────

  const onConnect: OnConnect = useCallback(
    (params) => {
      if (!params.source || !params.target) return;
      setPendingEdge({ source: params.source, target: params.target });
      setConnLabel("");
      setConnType("signal");
    },
    []
  );

  const confirmConnection = async () => {
    if (!pendingEdge) return;
    try {
      const conn = await createConnection(projectId, {
        sourceBlockId: pendingEdge.source,
        targetBlockId: pendingEdge.target,
        label: connLabel,
        connType,
      });
      setConnections((prev) => [...prev, conn]);
      setEdges((eds) =>
        addEdge(
          {
            id: conn.id,
            source: conn.sourceBlockId,
            target: conn.targetBlockId,
            label: conn.label || undefined,
            type: "smoothstep",
            style: edgeStyle(conn.connType),
            labelStyle: { fill: CONN_COLOR[conn.connType] ?? "#a1a1aa", fontSize: 11 },
            labelBgStyle: { fill: "#111114", fillOpacity: 0.85 },
            data: { connType: conn.connType, connId: conn.id },
          },
          eds
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPendingEdge(null);
    }
  };

  // ── delete edge on click ─────────────────────────────────────────────────────

  const onEdgeClick = useCallback(
    (_evt: React.MouseEvent, edge: Edge) => {
      const connId = (edge.data as { connId?: string })?.connId ?? edge.id;
      if (!confirm(`Delete connection "${edge.label ?? edge.id}"?`)) return;
      deleteConnection(projectId, connId)
        .then(() => {
          setEdges((eds) => eds.filter((e) => e.id !== edge.id));
          setConnections((prev) => prev.filter((c) => c.id !== connId));
        })
        .catch((err) => setError(err.message));
    },
    [projectId, setEdges]
  );

  // ── node click → select ──────────────────────────────────────────────────────

  const onNodeClick: NodeMouseHandler = useCallback((_evt, node) => {
    setSelectedBlockId((prev) => (prev === node.id ? null : node.id));
    setCircuitBlockId(null);
    setSchematic(null);
    setSchematicError(null);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedBlockId(null);
    setPendingEdge(null);
    setCircuitBlockId(null);
    setSchematic(null);
    setSchematicError(null);
  }, []);

  // ── suggest connections ──────────────────────────────────────────────────────

  const handleSuggest = async () => {
    setSuggesting(true);
    setError(null);
    try {
      const result = await suggestConnections(projectId);
      const newConns = result.connections as BlockConnection[];
      setConnections((prev) => [...prev, ...newConns]);
      setEdges((eds) => [
        ...eds,
        ...connectionsToEdges(newConns),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSuggesting(false);
    }
  };

  // ── auto layout ──────────────────────────────────────────────────────────────

  const handleAutoLayout = () => {
    setNodes(blocksToNodes(diagramBlocks, components, true));
    // persist new positions
    const autoPos = autoLayout(diagramBlocks);
    Object.entries(autoPos).forEach(([id, pos]) => {
      updateBlockPosition(projectId, id, pos.x, pos.y).catch(console.error);
    });
  };

  // ── describe block circuit ───────────────────────────────────────────────────

  const handleDescribeCircuit = async (blockId: string) => {
    setCircuitBlockId(blockId);
    setSchematic(null);
    setSchematicError(null);
    setSchematicLoading(true);
    try {
      const result = await describeBlockCircuit(projectId, blockId);
      setSchematic(result.schematic);
    } catch (err) {
      setSchematicError(err instanceof Error ? err.message : String(err));
    } finally {
      setSchematicLoading(false);
    }
  };

  // ── selected block details ───────────────────────────────────────────────────

  const selectedBlock = diagramBlocks.find((b) => b.id === selectedBlockId);
  const blockComponents = components.filter((c) => c.blockId === selectedBlockId);
  const blockConnsOut = connections.filter((c) => c.sourceBlockId === selectedBlockId);
  const blockConnsIn  = connections.filter((c) => c.targetBlockId === selectedBlockId);
  const blockById     = (id: string) => diagramBlocks.find((b) => b.id === id);

  // ── render ───────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div style={centerStyle}>
        <div style={{ color: "#52525b", fontSize: 13 }}>Loading diagram…</div>
      </div>
    );
  }

  if (diagramBlocks.length === 0) {
    return (
      <div style={centerStyle}>
        <div style={{ textAlign: "center", color: "#3f3f46", fontSize: 13 }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>◻</div>
          No blocks yet. Create blocks in the Spec tab or use "Draft Circuit" in Chat.
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>

      {/* Toolbar */}
      <div
        style={{
          padding: "8px 16px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexShrink: 0,
          background: "#0c0c0f",
        }}
      >
        <span style={{ fontSize: 12, color: "#52525b" }}>
          {diagramBlocks.length} blocks · {connections.length} connections
        </span>
        <div style={{ flex: 1 }} />
        {error && (
          <span style={{ fontSize: 12, color: "#f87171", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {error}
          </span>
        )}
        <ToolbarBtn
          label={suggesting ? "Suggesting…" : "Suggest Connections"}
          color="#7c3aed"
          disabled={suggesting}
          onClick={handleSuggest}
        />
        <ToolbarBtn label="Auto Layout" color="#0891b2" onClick={handleAutoLayout} />
        <div style={{ width: 1, height: 20, background: "#27272a" }} />
        <ConnLegend />
      </div>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* React Flow canvas */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            minZoom={0.2}
            maxZoom={2}
            style={{ background: "#09090b" }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              color="#1c1c1f"
              gap={24}
              size={1}
            />
            <Controls
              style={{
                background: "#111114",
                border: "1px solid #27272a",
                borderRadius: 8,
              }}
            />
            <MiniMap
              style={{ background: "#0c0c0f", border: "1px solid #27272a" }}
              nodeColor={(n) => {
                const tl = (n.data as BlockNodeData).trustLevel as TrustLevel;
                return TRUST_COLOR_MAP[tl] ?? "#27272a";
              }}
              maskColor="#09090b88"
            />
          </ReactFlow>
        </div>

        {/* Detail sidebar */}
        {selectedBlock && (
          <div
            style={{
              width: 300,
              borderLeft: "1px solid #18181b",
              display: "flex",
              flexDirection: "column",
              background: "#0c0c0f",
              overflowY: "auto",
            }}
          >
            {/* Block header */}
            <div style={{ padding: "14px 16px", borderBottom: "1px solid #18181b" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
                <div style={{ flex: 1, fontWeight: 600, fontSize: 14, color: "#f4f4f5" }}>
                  {selectedBlock.name}
                </div>
                <StatusBadge label={selectedBlock.trustLevel} tone={selectedBlock.trustLevel} />
              </div>
              {selectedBlock.description && (
                <div style={{ fontSize: 12, color: "#71717a", lineHeight: 1.5 }}>
                  {selectedBlock.description}
                </div>
              )}
            </div>

            {/* Components */}
            <SideSection title={`Components (${blockComponents.length})`}>
              {blockComponents.length === 0 ? (
                <div style={emptyHint}>None assigned</div>
              ) : (
                blockComponents.map((c) => (
                  <div key={c.id} style={sideItemStyle}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "#e4e4e7" }}>
                      {c.name ?? "—"}
                    </div>
                    {c.mpn && (
                      <div style={{ fontSize: 11, color: "#60a5fa", fontFamily: "monospace" }}>
                        {c.mpn}
                      </div>
                    )}
                    {(c.package || c.manufacturer) && (
                      <div style={{ fontSize: 11, color: "#52525b" }}>
                        {[c.package, c.manufacturer].filter(Boolean).join(" · ")}
                      </div>
                    )}
                  </div>
                ))
              )}
            </SideSection>

            {/* Connections */}
            {(blockConnsOut.length > 0 || blockConnsIn.length > 0) && (
              <SideSection title="Connections">
                {blockConnsOut.map((c) => (
                  <ConnLine
                    key={c.id}
                    direction="out"
                    label={c.label}
                    connType={c.connType}
                    otherBlock={blockById(c.targetBlockId)?.name ?? c.targetBlockId}
                  />
                ))}
                {blockConnsIn.map((c) => (
                  <ConnLine
                    key={c.id}
                    direction="in"
                    label={c.label}
                    connType={c.connType}
                    otherBlock={blockById(c.sourceBlockId)?.name ?? c.sourceBlockId}
                  />
                ))}
              </SideSection>
            )}

            {/* Circuit description */}
            <SideSection title="Circuit Topology">
              {schematicLoading ? (
                <div style={{ fontSize: 12, color: "#52525b" }}>Generating…</div>
              ) : schematicError ? (
                <div>
                  <div style={{ fontSize: 12, color: "#f87171", marginBottom: 8, lineHeight: 1.4 }}>
                    {schematicError}
                  </div>
                  <button
                    onClick={() => handleDescribeCircuit(selectedBlock.id)}
                    style={{
                      background: "transparent",
                      border: "1px solid #27272a",
                      borderRadius: 7,
                      color: "#a1a1aa",
                      padding: "6px 12px",
                      cursor: "pointer",
                      fontSize: 12,
                      width: "100%",
                    }}
                  >
                    Retry ↗
                  </button>
                </div>
              ) : schematic && circuitBlockId === selectedBlock.id ? (
                <pre
                  style={{
                    margin: 0,
                    fontSize: 11,
                    fontFamily: "monospace",
                    color: "#a1a1aa",
                    background: "#09090b",
                    borderRadius: 8,
                    padding: 10,
                    whiteSpace: "pre",
                    overflowX: "auto",
                    lineHeight: 1.5,
                  }}
                >
                  {schematic}
                </pre>
              ) : (
                <button
                  onClick={() => handleDescribeCircuit(selectedBlock.id)}
                  style={{
                    background: "transparent",
                    border: "1px solid #27272a",
                    borderRadius: 7,
                    color: "#a1a1aa",
                    padding: "6px 12px",
                    cursor: "pointer",
                    fontSize: 12,
                    width: "100%",
                  }}
                >
                  Generate with Claude ↗
                </button>
              )}
            </SideSection>
          </div>
        )}
      </div>

      {/* New connection modal */}
      {pendingEdge && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "#00000066",
            display: "grid",
            placeItems: "center",
            zIndex: 100,
          }}
          onClick={() => setPendingEdge(null)}
        >
          <div
            style={{
              background: "#111114",
              border: "1px solid #3f3f46",
              borderRadius: 12,
              padding: 20,
              width: 320,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 14, color: "#f4f4f5" }}>
              New Connection
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div>
                <label style={labelStyle}>Type</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                  {CONN_TYPES.map((t) => (
                    <button
                      key={t}
                      onClick={() => setConnType(t)}
                      style={{
                        background:   connType === t ? CONN_COLOR[t] + "22" : "transparent",
                        border:       `1px solid ${connType === t ? CONN_COLOR[t] : "#27272a"}`,
                        borderRadius: 6,
                        color:        CONN_COLOR[t],
                        padding:      "3px 10px",
                        cursor:       "pointer",
                        fontSize:     12,
                      }}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label style={labelStyle}>Label (optional)</label>
                <input
                  autoFocus
                  value={connLabel}
                  onChange={(e) => setConnLabel(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") confirmConnection(); if (e.key === "Escape") setPendingEdge(null); }}
                  placeholder={`e.g. ${connType === "power" ? "5V" : connType === "i2c" ? "SDA/SCL" : "signal"}`}
                  style={inputStyle}
                />
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <button
                  onClick={confirmConnection}
                  style={{ flex: 1, background: "#2563eb", color: "#fff", border: "none", borderRadius: 8, padding: "7px", cursor: "pointer", fontSize: 13 }}
                >
                  Add
                </button>
                <button
                  onClick={() => setPendingEdge(null)}
                  style={{ flex: 1, background: "#27272a", color: "#a1a1aa", border: "none", borderRadius: 8, padding: "7px", cursor: "pointer", fontSize: 13 }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── sub-components ────────────────────────────────────────────────────────────

function SideSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ borderBottom: "1px solid #18181b" }}>
      <div style={{ padding: "8px 16px 4px", fontSize: 11, fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {title}
      </div>
      <div style={{ padding: "4px 12px 12px" }}>{children}</div>
    </div>
  );
}

function ConnLine({ direction, label, connType, otherBlock }: {
  direction: "in" | "out";
  label: string;
  connType: string;
  otherBlock: string;
}) {
  const color = CONN_COLOR[connType] ?? CONN_COLOR.signal;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 0", fontSize: 12 }}>
      <span style={{ color: "#52525b" }}>{direction === "out" ? "→" : "←"}</span>
      <span style={{ color, fontWeight: 500, minWidth: 40 }}>
        {label || connType}
      </span>
      <span style={{ color: "#71717a" }}>{otherBlock}</span>
    </div>
  );
}

function ToolbarBtn({ label, color, disabled, onClick }: {
  label: string; color: string; disabled?: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background:   "transparent",
        border:       `1px solid ${disabled ? "#27272a" : color}`,
        borderRadius: 7,
        color:        disabled ? "#3f3f46" : color,
        padding:      "4px 12px",
        cursor:       disabled ? "not-allowed" : "pointer",
        fontSize:     12,
        opacity:      disabled ? 0.5 : 1,
      }}
    >
      {label}
    </button>
  );
}

function ConnLegend() {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      {(["power", "gnd", "signal", "i2c", "spi", "uart"] as const).map((t) => (
        <div key={t} style={{ display: "flex", alignItems: "center", gap: 3 }}>
          <div style={{ width: 16, height: 2, background: CONN_COLOR[t], borderRadius: 1 }} />
          <span style={{ fontSize: 10, color: "#52525b" }}>{t}</span>
        </div>
      ))}
    </div>
  );
}

const TRUST_COLOR_MAP: Record<TrustLevel, string> = {
  new:              "#27272a",
  parsed:           "#334155",
  reviewed:         "#92400e",
  validated:        "#166534",
  proven:           "#15803d",
  trusted_template: "#1d4ed8",
};

const centerStyle: React.CSSProperties = {
  height: "100%", display: "grid", placeItems: "center", background: "#09090b",
};
const sideItemStyle: React.CSSProperties = {
  background: "#111114", border: "1px solid #1c1c1f",
  borderRadius: 8, padding: "7px 10px", marginBottom: 4,
  display: "flex", flexDirection: "column", gap: 2,
};
const emptyHint: React.CSSProperties = {
  fontSize: 12, color: "#3f3f46", padding: "4px 0",
};
const labelStyle: React.CSSProperties = {
  fontSize: 11, color: "#52525b",
};
const inputStyle: React.CSSProperties = {
  width: "100%", marginTop: 4,
  background: "#09090b", color: "#f4f4f5",
  border: "1px solid #27272a", borderRadius: 7,
  padding: "7px 10px", fontSize: 13, outline: "none",
  boxSizing: "border-box", fontFamily: "inherit",
};
