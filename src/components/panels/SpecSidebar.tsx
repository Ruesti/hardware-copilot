import { useEffect, useRef, useState } from "react";
import type { Requirement, DiagramBlock, ComponentItem } from "../../types/project";

const TYPE_COLORS: Record<string, string> = {
  mcu: "#60a5fa",
  power_ic: "#f59e0b",
  sensor: "#34d399",
  connector: "#a78bfa",
  passive_resistor: "#94a3b8",
  passive_capacitor: "#94a3b8",
  passive_inductor: "#94a3b8",
  diode: "#f87171",
  transistor: "#fb923c",
  protection: "#f87171",
  memory: "#818cf8",
  crystal: "#e879f9",
  other: "#71717a",
};

type Props = {
  requirements: Requirement[];
  blocks: DiagramBlock[];
  components: ComponentItem[];
};

export function SpecSidebar({ requirements, blocks, components }: Props) {
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set());
  const seededIds = useRef<Set<string>>(new Set());

  // Bei kompakten Designs (≤ 5 Blöcke) alle Block-Akkordeons standardmäßig
  // aufgeklappt zeigen — Komponenten sollen sofort sichtbar sein. Wir merken
  // uns pro Block-ID, ob wir ihn schon einmal vorbelegt haben, damit User-
  // Collapses nicht beim nächsten Refresh überschrieben werden.
  useEffect(() => {
    if (blocks.length === 0 || blocks.length > 5) return;
    const newOnes = blocks.filter((b) => !seededIds.current.has(b.id));
    if (newOnes.length === 0) return;
    setExpandedBlocks((prev) => {
      const next = new Set(prev);
      for (const b of newOnes) next.add(b.id);
      return next;
    });
    for (const b of newOnes) seededIds.current.add(b.id);
  }, [blocks]);

  const toggleBlock = (blockId: string) => {
    setExpandedBlocks((prev) => {
      const next = new Set(prev);
      if (next.has(blockId)) next.delete(blockId);
      else next.add(blockId);
      return next;
    });
  };

  const blocksWithComponents = blocks.map((b) => ({
    block: b,
    items: components.filter((c) => c.blockId === b.id),
  }));

  const unassigned = components.filter((c) => !c.blockId);

  return (
    <div
      style={{
        width: 340,
        flexShrink: 0,
        borderLeft: "1px solid #18181b",
        display: "flex",
        flexDirection: "column",
        background: "#0c0c0f",
        overflow: "hidden",
      }}
    >
      {/* ── Anforderungen ── */}
      <div
        style={{
          padding: "10px 14px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: "#a1a1aa", letterSpacing: "0.05em", textTransform: "uppercase" }}>
          Anforderungen
        </span>
        <span style={{ fontSize: 11, color: "#52525b" }}>
          {requirements.length}
        </span>
      </div>

      <div style={{ maxHeight: 280, overflowY: "auto", padding: "8px 10px" }}>
        {requirements.length === 0 ? (
          <div style={{ fontSize: 11, color: "#3f3f46", textAlign: "center", padding: "12px 0" }}>
            Noch keine Anforderungen — Interview läuft…
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {requirements.map((req) => (
              <div
                key={req.id}
                style={{
                  padding: "8px 10px",
                  background: "#111114",
                  border: "1px solid #1f1f23",
                  borderRadius: 8,
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600, color: "#e4e4e7", marginBottom: 2 }}>
                  {req.title}
                </div>
                {req.description && (
                  <div style={{ fontSize: 11, color: "#71717a", lineHeight: 1.5 }}>
                    {req.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Bauteileliste ── */}
      <div
        style={{
          padding: "10px 14px",
          borderTop: "1px solid #18181b",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600, color: "#a1a1aa", letterSpacing: "0.05em", textTransform: "uppercase" }}>
          Bauteile
        </span>
        <span style={{ fontSize: 11, color: "#52525b" }}>
          {components.length}
        </span>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "8px 10px" }}>
        {components.length === 0 ? (
          <div style={{ fontSize: 11, color: "#3f3f46", textAlign: "center", padding: "12px 0" }}>
            Noch keine Bauteile — „Suggest Components" klicken
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {blocksWithComponents.filter((g) => g.items.length > 0).map(({ block, items }) => (
              <div key={block.id}>
                {/* Block header (accordion) */}
                <button
                  onClick={() => toggleBlock(block.id)}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "6px 8px",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    borderRadius: 6,
                    textAlign: "left",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#18181b")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <span style={{ fontSize: 10, color: "#52525b", width: 10 }}>
                    {expandedBlocks.has(block.id) ? "▼" : "▶"}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#d4d4d8", flex: 1 }}>
                    {block.name}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      color: "#52525b",
                      background: "#18181b",
                      border: "1px solid #27272a",
                      borderRadius: 4,
                      padding: "1px 5px",
                    }}
                  >
                    {items.length}
                  </span>
                </button>

                {/* Components list */}
                {expandedBlocks.has(block.id) && (
                  <div style={{ paddingLeft: 16, paddingBottom: 4 }}>
                    {items.map((c) => (
                      <ComponentRow key={c.id} component={c} />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Unassigned components */}
            {unassigned.length > 0 && (
              <div>
                <button
                  onClick={() => toggleBlock("__unassigned__")}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "6px 8px",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    borderRadius: 6,
                    textAlign: "left",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#18181b")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <span style={{ fontSize: 10, color: "#52525b", width: 10 }}>
                    {expandedBlocks.has("__unassigned__") ? "▼" : "▶"}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#71717a", flex: 1 }}>
                    Nicht zugeordnet
                  </span>
                  <span style={{ fontSize: 10, color: "#52525b", background: "#18181b", border: "1px solid #27272a", borderRadius: 4, padding: "1px 5px" }}>
                    {unassigned.length}
                  </span>
                </button>
                {expandedBlocks.has("__unassigned__") && (
                  <div style={{ paddingLeft: 16, paddingBottom: 4 }}>
                    {unassigned.map((c) => <ComponentRow key={c.id} component={c} />)}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ComponentRow({ component: c }: { component: ComponentItem }) {
  const typeColor = TYPE_COLORS[c.type ?? "other"] ?? TYPE_COLORS.other;
  return (
    <div
      style={{
        padding: "5px 8px",
        borderRadius: 6,
        marginBottom: 2,
        background: "#111114",
        border: "1px solid #1f1f23",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, fontWeight: 500, color: "#d4d4d8", flex: 1, minWidth: 80 }}>
          {c.name ?? c.description}
        </span>
        {c.type && (
          <span style={{ fontSize: 9, color: typeColor, background: typeColor + "22", borderRadius: 3, padding: "1px 4px", fontWeight: 600 }}>
            {c.type}
          </span>
        )}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 2 }}>
        {c.value && <span style={{ fontSize: 10, color: "#71717a" }}>{c.value}</span>}
        {c.package && <span style={{ fontSize: 10, color: "#52525b" }}>{c.package}</span>}
        {c.mpn && <span style={{ fontSize: 10, color: "#3f3f46", fontFamily: "monospace" }}>{c.mpn}</span>}
      </div>
    </div>
  );
}
