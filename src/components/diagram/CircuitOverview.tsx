import type { DiagramBlock, BlockConnection } from "../../types/project";

const CONN_COLORS: Record<string, string> = {
  power: "#f59e0b",
  gnd: "#6b7280",
  signal: "#3b82f6",
  i2c: "#a855f7",
  spi: "#ec4899",
  uart: "#22c55e",
  custom: "#14b8a6",
};

const TRUST_DOT: Record<string, string> = {
  new: "#52525b",
  parsed: "#475569",
  reviewed: "#b45309",
  validated: "#16a34a",
  proven: "#15803d",
  trusted_template: "#2563eb",
};

type Props = {
  blocks: DiagramBlock[];
  connections: BlockConnection[];
  onBlockClick: (blockId: string) => void;
};

export function CircuitOverview({ blocks, connections, onBlockClick }: Props) {
  const blockMap = Object.fromEntries(blocks.map((b) => [b.id, b]));

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
      {/* Header */}
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
          Circuit Blocks
        </span>
        <span style={{ fontSize: 11, color: "#52525b" }}>
          {blocks.length} block{blocks.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Scrollable content */}
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "10px 10px 0" }}>
        {/* Block cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {blocks.map((block) => (
            <button
              key={block.id}
              onClick={() => onBlockClick(block.id)}
              style={{
                background: "#111114",
                border: "1px solid #27272a",
                borderRadius: 10,
                padding: "10px 12px",
                cursor: "pointer",
                textAlign: "left",
                transition: "border-color 0.1s, background 0.1s",
                width: "100%",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "#3f3f46";
                (e.currentTarget as HTMLButtonElement).style.background = "#18181b";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "#27272a";
                (e.currentTarget as HTMLButtonElement).style.background = "#111114";
              }}
            >
              {/* Block name + trust dot */}
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                <span
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background: TRUST_DOT[block.trustLevel] ?? "#52525b",
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: 13, fontWeight: 600, color: "#e4e4e7", flex: 1, minWidth: 0 }}>
                  {block.name}
                </span>
                <span style={{ fontSize: 10, color: "#52525b" }}>↗</span>
              </div>

              {/* Description */}
              <div
                style={{
                  fontSize: 12,
                  color: "#71717a",
                  lineHeight: 1.5,
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                  marginBottom: 6,
                }}
              >
                {block.description}
              </div>

              {/* Footer */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: 11, color: "#52525b" }}>
                  {block.componentCount} component{block.componentCount !== 1 ? "s" : ""}
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
                  {block.trustLevel}
                </span>
              </div>
            </button>
          ))}
        </div>

        {/* Connections section */}
        {connections.length > 0 && (
          <div style={{ marginTop: 12, paddingBottom: 10 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#52525b",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                marginBottom: 6,
                padding: "0 2px",
              }}
            >
              Connections
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
              {connections.map((conn) => {
                const src = blockMap[conn.sourceBlockId];
                const tgt = blockMap[conn.targetBlockId];
                const color = CONN_COLORS[conn.connType] ?? CONN_COLORS.custom;
                return (
                  <div
                    key={conn.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 5,
                      fontSize: 11,
                      padding: "4px 6px",
                      borderRadius: 6,
                      background: "#111114",
                      flexWrap: "wrap",
                    }}
                  >
                    <span
                      style={{
                        background: color + "22",
                        color,
                        borderRadius: 4,
                        padding: "1px 5px",
                        fontSize: 10,
                        fontWeight: 600,
                        flexShrink: 0,
                      }}
                    >
                      {conn.connType}
                    </span>
                    <span style={{ color: "#a1a1aa", fontWeight: 500 }}>
                      {src?.name ?? "?"}
                    </span>
                    <span style={{ color: "#3f3f46" }}>→</span>
                    <span style={{ color: "#a1a1aa", fontWeight: 500 }}>
                      {tgt?.name ?? "?"}
                    </span>
                    {conn.label && (
                      <span style={{ color: "#52525b" }}>({conn.label})</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {connections.length === 0 && blocks.length > 0 && (
          <div
            style={{
              fontSize: 11,
              color: "#3f3f46",
              textAlign: "center",
              marginTop: 10,
              paddingBottom: 10,
            }}
          >
            No connections yet — use "Suggest Connections"
          </div>
        )}
      </div>
    </div>
  );
}
