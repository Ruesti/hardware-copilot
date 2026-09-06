import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "./ChatPanel";
import { DiagramPanel } from "./DiagramPanel";
import { SpecSidebar } from "./SpecSidebar";
import { SchematicModal } from "../diagram/SchematicModal";
import { refreshDesign } from "../../api/components";
import { fetchDiagram } from "../../api/diagram";
import { fetchComponents } from "../../api/components";
import { fetchUsage, type UsageSummary } from "../../api/usage";
import { fetchExportReport, kicadDownloadUrl, type ExportReport, type MountStyle } from "../../api/export";
import type {
  BlockConnection,
  ChatMessage,
  ComponentItem,
  DiagramBlock,
  Requirement,
} from "../../types/project";

type SchematicMode = "auto" | "manual";

const MODE_STORAGE_KEY = "hardware-copilot.workbench.schematicMode";
const COL_LEFT_KEY = "hardware-copilot.workbench.colLeft";
const COL_RIGHT_KEY = "hardware-copilot.workbench.colRight";
const COL_LEFT_DEFAULT = 360;
const COL_RIGHT_DEFAULT = 340;
const COL_LEFT_MIN = 240;
const COL_RIGHT_MIN = 240;
const COL_CENTER_MIN = 320;

type Props = {
  projectId: string;
  messages: ChatMessage[];
  onMessagesChange: (msgs: ChatMessage[]) => void;
  requirements: Requirement[];
  onRequirementsChange: (items: Requirement[]) => void;
  components: ComponentItem[];
  onComponentsChange: (items: ComponentItem[]) => void;
  diagramBlocks: DiagramBlock[];
  diagramConnections: BlockConnection[];
  onDiagramBlocksChange: (items: DiagramBlock[]) => void;
  onDiagramConnectionsChange: (items: BlockConnection[]) => void;
};

function loadInitialMode(): SchematicMode {
  if (typeof window === "undefined") return "auto";
  const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
  return stored === "manual" ? "manual" : "auto";
}

function loadColWidth(key: string, fallback: number): number {
  if (typeof window === "undefined") return fallback;
  const v = window.localStorage.getItem(key);
  const n = v ? parseInt(v, 10) : NaN;
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function formatTokens(n: number): string {
  if (n < 1000) return String(n);
  if (n < 1_000_000) return (n / 1000).toFixed(n < 10_000 ? 2 : 1) + "k";
  return (n / 1_000_000).toFixed(2) + "M";
}

export function WorkbenchPanel({
  projectId,
  messages,
  onMessagesChange,
  requirements,
  onRequirementsChange,
  components,
  onComponentsChange,
  diagramBlocks,
  diagramConnections,
  onDiagramBlocksChange,
  onDiagramConnectionsChange,
}: Props) {
  const [openBlockId, setOpenBlockId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [exportReport, setExportReport] = useState<ExportReport | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [exportAsk, setExportAsk] = useState(false);
  const [exportMount, setExportMount] = useState<MountStyle>("smd");
  const closeExport = () => {
    setExportReport(null);
    setExportError(null);
    setExportAsk(false);
  };
  const runExport = (mount: MountStyle) => {
    setExportMount(mount);
    setExportAsk(false);
    setExportLoading(true);
    setExportError(null);
    fetchExportReport(projectId, mount)
      .then(setExportReport)
      .catch((err) => setExportError(String(err?.message ?? err)))
      .finally(() => setExportLoading(false));
  };
  const [mode, setMode] = useState<SchematicMode>(loadInitialMode);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [colLeft, setColLeft] = useState<number>(() => loadColWidth(COL_LEFT_KEY, COL_LEFT_DEFAULT));
  const [colRight, setColRight] = useState<number>(() => loadColWidth(COL_RIGHT_KEY, COL_RIGHT_DEFAULT));
  const pollAbortRef = useRef<{ cancelled: boolean } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, [mode]);
  useEffect(() => {
    window.localStorage.setItem(COL_LEFT_KEY, String(colLeft));
  }, [colLeft]);
  useEffect(() => {
    window.localStorage.setItem(COL_RIGHT_KEY, String(colRight));
  }, [colRight]);

  const openBlock = diagramBlocks.find((b) => b.id === openBlockId) ?? null;

  const updateBlockInState = useCallback(
    (blockId: string, patch: Partial<DiagramBlock>) => {
      onDiagramBlocksChange(
        diagramBlocks.map((b) => (b.id === blockId ? { ...b, ...patch } : b))
      );
    },
    [diagramBlocks, onDiagramBlocksChange]
  );

  const loadUsage = useCallback(() => {
    fetchUsage(projectId)
      .then(setUsage)
      .catch(() => {
        /* ignore */
      });
  }, [projectId]);

  useEffect(() => {
    loadUsage();
  }, [loadUsage]);

  // ── Polling: nach Refresh kurz pollen, bis alle Blöcke einen ASCII-Schaltplan haben
  const pollForSchematics = useCallback(
    async (token: { cancelled: boolean }, maxAttempts = 6, intervalMs = 2000) => {
      for (let i = 0; i < maxAttempts; i++) {
        await new Promise((r) => setTimeout(r, intervalMs));
        if (token.cancelled) return;
        try {
          const diagram = await fetchDiagram(projectId);
          if (token.cancelled) return;
          onDiagramBlocksChange(diagram.blocks);
          onDiagramConnectionsChange(diagram.connections);
          loadUsage();
          const allHaveSchematic = diagram.blocks
            .filter((b) => b.componentCount > 0)
            .every((b) => !!b.schematicAscii);
          if (allHaveSchematic) return;
        } catch {
          // ignore polling errors
        }
      }
    },
    [projectId, onDiagramBlocksChange, onDiagramConnectionsChange, loadUsage]
  );

  const handleAssistantTurn = useCallback(
    async (_content: string, _source: "stream" | "draft" | "suggest" | "connections") => {
      if (refreshing) return;
      setRefreshing(true);
      if (pollAbortRef.current) pollAbortRef.current.cancelled = true;

      try {
        const result = await refreshDesign(projectId, mode);
        onDiagramBlocksChange(result.blocks);
        onDiagramConnectionsChange(result.connections);
        onComponentsChange(result.components);
        loadUsage();

        if (mode === "auto") {
          const token = { cancelled: false };
          pollAbortRef.current = token;
          pollForSchematics(token).finally(() => {
            if (pollAbortRef.current === token) pollAbortRef.current = null;
          });
        }
      } catch (err) {
        console.error("refresh-design failed", err);
      } finally {
        setRefreshing(false);
      }
    },
    [
      projectId,
      mode,
      refreshing,
      onDiagramBlocksChange,
      onDiagramConnectionsChange,
      onComponentsChange,
      pollForSchematics,
      loadUsage,
    ]
  );

  useEffect(() => {
    return () => {
      if (pollAbortRef.current) pollAbortRef.current.cancelled = true;
    };
  }, []);

  // ── Resize-Handles ──────────────────────────────────────────────────────────

  const startDrag = (side: "left" | "right") => (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startLeft = colLeft;
    const startRight = colRight;
    const containerWidth = containerRef.current?.clientWidth ?? 1200;

    const onMove = (ev: MouseEvent) => {
      const dx = ev.clientX - startX;
      if (side === "left") {
        const next = Math.max(
          COL_LEFT_MIN,
          Math.min(startLeft + dx, containerWidth - startRight - COL_CENTER_MIN)
        );
        setColLeft(next);
      } else {
        const next = Math.max(
          COL_RIGHT_MIN,
          Math.min(startRight - dx, containerWidth - startLeft - COL_CENTER_MIN)
        );
        setColRight(next);
      }
    };
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background: "#09090b",
        overflow: "hidden",
      }}
    >
      {/* Workbench-Toolbar */}
      <div
        style={{
          padding: "8px 16px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexShrink: 0,
          background: "#0c0c0f",
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: "#a1a1aa" }}>
          Workbench
        </span>
        <span style={{ fontSize: 11, color: "#52525b" }}>
          {diagramBlocks.length} Blöcke · {components.length} Bauteile
          {refreshing ? " · aktualisiert…" : ""}
        </span>
        <div style={{ flex: 1 }} />

        {/* KiCad-Export */}
        <button
          onClick={() => setExportAsk(true)}
          disabled={exportLoading}
          style={{
            background: "#0c0c0f",
            border: "1px solid #27272a",
            borderRadius: 8,
            color: "#a1a1aa",
            padding: "4px 10px",
            fontSize: 11,
            cursor: exportLoading ? "wait" : "pointer",
          }}
          title="Schaltplan-Gerüst als KiCad-9-Datei exportieren"
        >
          ⬇ KiCad{exportLoading ? "…" : ""}
        </button>

        {/* Token-Anzeige */}
        {usage && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 11,
              color: "#a1a1aa",
              background: "#0c0c0f",
              border: "1px solid #27272a",
              borderRadius: 8,
              padding: "4px 10px",
            }}
            title={`Eingabe: ${usage.totalInputTokens.toLocaleString()} Tokens\nAusgabe: ${usage.totalOutputTokens.toLocaleString()} Tokens\nGesamtkosten: $${usage.totalCostUsd.toFixed(4)}`}
          >
            <span style={{ color: "#3f3f46" }}>📊</span>
            <span>
              <span style={{ color: "#86efac" }}>↓{formatTokens(usage.totalInputTokens)}</span>
              {" "}
              <span style={{ color: "#fbbf24" }}>↑{formatTokens(usage.totalOutputTokens)}</span>
            </span>
            <span style={{ color: "#52525b" }}>·</span>
            <span style={{ color: "#fb923c", fontWeight: 600 }}>
              ${usage.totalCostUsd < 0.01 ? usage.totalCostUsd.toFixed(4) : usage.totalCostUsd.toFixed(3)}
            </span>
          </div>
        )}

        {/* Modus-Schalter */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            background: "#0c0c0f",
            border: "1px solid #27272a",
            borderRadius: 8,
            padding: 2,
          }}
          title={
            mode === "auto"
              ? "Auto-Modus: ASCII-Schaltpläne werden nach jedem KI-Turn im Hintergrund neu erzeugt (kostet Tokens, ~0,5 ¢ pro Block)."
              : "Manuell-Modus: Schaltpläne werden nur auf Klick erzeugt. Validierte Schaltpläne bleiben erhalten."
          }
        >
          <ModeChip
            label="Auto"
            active={mode === "auto"}
            onClick={() => setMode("auto")}
          />
          <ModeChip
            label="Manuell"
            active={mode === "manual"}
            onClick={() => setMode("manual")}
          />
        </div>
      </div>

      {/* Onboarding-Hinweis: keine Anforderungen → Interview-Modus empfehlen */}
      {requirements.length === 0 && diagramBlocks.length === 0 && (
        <div
          style={{
            padding: "10px 16px",
            background: "#1c1404",
            borderBottom: "1px solid #422006",
            color: "#fbbf24",
            fontSize: 12,
            display: "flex",
            alignItems: "center",
            gap: 8,
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 14 }}>💡</span>
          <span>
            Tipp: Aktiviere links den <strong>Interview</strong>-Button. Die KI stellt
            gezielte Fragen und legt automatisch Anforderungen an, aus denen sich das
            Blockschaltbild ergibt.
          </span>
        </div>
      )}

      {/* Drei Spalten — mit Drag-Handles */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          overflow: "hidden",
        }}
      >
        {/* Spalte 1: Chat */}
        <div
          style={{
            width: colLeft,
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            minWidth: 0,
          }}
        >
          <ChatPanel
            projectId={projectId}
            messages={messages}
            onMessagesChange={onMessagesChange}
            diagramBlocks={diagramBlocks}
            diagramConnections={diagramConnections}
            components={components}
            requirements={requirements}
            onRequirementsChange={onRequirementsChange}
            onDiagramRefresh={() => {
              fetchDiagram(projectId)
                .then((d) => {
                  onDiagramBlocksChange(d.blocks);
                  onDiagramConnectionsChange(d.connections);
                })
                .catch(() => {});
              fetchComponents(projectId)
                .then((c) => onComponentsChange(c.items))
                .catch(() => {});
            }}
            embedded
            defaultInterviewMode
            onAssistantTurn={handleAssistantTurn}
          />
        </div>

        <ResizeHandle onMouseDown={startDrag("left")} />

        {/* Spalte 2: Diagramm */}
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <DiagramPanel
            projectId={projectId}
            components={components}
            externalBlocks={diagramBlocks}
            externalConnections={diagramConnections}
            embedded
            onBlockOpen={setOpenBlockId}
          />
        </div>

        <ResizeHandle onMouseDown={startDrag("right")} />

        {/* Spalte 3: Komponenten nach Baugruppe */}
        <div style={{ width: colRight, flexShrink: 0, display: "flex", minWidth: 0 }}>
          <SpecSidebar
            requirements={requirements}
            blocks={diagramBlocks}
            components={components}
          />
        </div>
      </div>

      {openBlock && (
        <SchematicModal
          projectId={projectId}
          block={openBlock}
          components={components}
          onClose={() => setOpenBlockId(null)}
          onBlockChange={(patch) => updateBlockInState(openBlock.id, patch)}
        />
      )}

      {(exportAsk || exportReport || exportError) && (
        <div
          onClick={closeExport}
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 60,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0c0c0f", border: "1px solid #27272a", borderRadius: 12,
              padding: 20, width: 460, maxHeight: "70vh", overflowY: "auto",
              color: "#e4e4e7", fontSize: 13,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 12 }}>KiCad-Export</div>
            {exportAsk ? (
              <>
                <div style={{ marginBottom: 12, color: "#a1a1aa", fontSize: 12 }}>
                  Wie soll bestückt werden? Das bestimmt die automatische
                  Footprint-Zuordnung der Bauteile.
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={() => runExport("smd")}
                    style={{
                      background: "#16a34a", color: "#fff", border: "none",
                      borderRadius: 8, padding: "8px 16px", fontSize: 12, cursor: "pointer",
                    }}
                  >
                    SMD (Oberflächenmontage)
                  </button>
                  <button
                    onClick={() => runExport("tht")}
                    style={{
                      background: "#0c0c0f", color: "#e4e4e7",
                      border: "1px solid #27272a",
                      borderRadius: 8, padding: "8px 16px", fontSize: 12, cursor: "pointer",
                    }}
                  >
                    THT (bedrahtet / Handlöten)
                  </button>
                </div>
              </>
            ) : exportError ? (
              <div style={{ color: "#f87171" }}>{exportError}</div>
            ) : exportReport ? (
              <>
                <div style={{ display: "flex", gap: 14, marginBottom: 12, fontSize: 12 }}>
                  <span style={{ color: "#86efac" }}>{exportReport.counts.mapped} gemappt</span>
                  <span style={{ color: "#a1a1aa" }}>{exportReport.counts.fallback} Standard</span>
                  <span style={{ color: "#fbbf24" }}>{exportReport.counts.unverified} unbestätigt</span>
                  <span style={{ color: "#f87171" }}>{exportReport.counts.unmapped} ohne Symbol</span>
                  <span style={{ color: "#a1a1aa" }}>{exportReport.counts.no_footprint} ohne Footprint</span>
                </div>
                {exportReport.unmapped.length > 0 && (
                  <div style={{ marginBottom: 10 }}>
                    <div style={{ color: "#f87171", fontSize: 12, marginBottom: 4 }}>
                      Nicht exportierbar (kein Bibliothekseintrag):
                    </div>
                    {exportReport.unmapped.map((u, i) => (
                      <div key={i} style={{ fontSize: 12, color: "#a1a1aa" }}>
                        · {u.name ?? u.mpn ?? "?"} ({u.block_name})
                      </div>
                    ))}
                  </div>
                )}
                {exportReport.warnings.length > 0 && (
                  <details style={{ marginBottom: 10 }}>
                    <summary style={{ cursor: "pointer", fontSize: 12, color: "#fbbf24" }}>
                      {exportReport.warnings.length} Hinweise
                    </summary>
                    {exportReport.warnings.map((w, i) => (
                      <div key={i} style={{ fontSize: 11, color: "#a1a1aa", marginTop: 4 }}>
                        · {w}
                      </div>
                    ))}
                  </details>
                )}
                <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                  <a
                    href={kicadDownloadUrl(projectId, exportMount)}
                    download
                    style={{
                      background: "#16a34a", color: "#fff", borderRadius: 8,
                      padding: "6px 14px", fontSize: 12, textDecoration: "none",
                    }}
                  >
                    .kicad_sch herunterladen
                  </a>
                  <button
                    onClick={closeExport}
                    style={{
                      background: "transparent", border: "1px solid #27272a",
                      borderRadius: 8, color: "#a1a1aa", padding: "6px 14px",
                      fontSize: 12, cursor: "pointer",
                    }}
                  >
                    Schließen
                  </button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

function ModeChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? "#18181b" : "transparent",
        color: active ? "#f4f4f5" : "#71717a",
        border: "none",
        borderRadius: 6,
        padding: "4px 12px",
        cursor: "pointer",
        fontSize: 12,
        fontWeight: active ? 600 : 400,
      }}
    >
      {label}
    </button>
  );
}

function ResizeHandle({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseDown={onMouseDown}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 5,
        cursor: "col-resize",
        background: hover ? "#3f3f46" : "#18181b",
        flexShrink: 0,
        transition: "background 0.12s",
      }}
      title="Spaltenbreite anpassen"
    />
  );
}
