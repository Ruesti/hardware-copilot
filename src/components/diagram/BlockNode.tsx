import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { TrustLevel } from "../../types/project";

export type BlockNodeData = {
  name: string;
  description: string;
  trustLevel: TrustLevel;
  componentCount: number;
  selected: boolean;
};

const TRUST_BORDER: Record<TrustLevel, string> = {
  new:              "#3f3f46",
  parsed:           "#334155",
  reviewed:         "#92400e",
  validated:        "#166534",
  proven:           "#15803d",
  trusted_template: "#1d4ed8",
};

const TRUST_GLOW: Record<TrustLevel, string> = {
  new:              "transparent",
  parsed:           "transparent",
  reviewed:         "#78350f44",
  validated:        "#14532d44",
  proven:           "#14532d66",
  trusted_template: "#1e3a8a44",
};

export function BlockNode({ data, selected }: NodeProps) {
  const d = data as BlockNodeData;
  const borderColor = TRUST_BORDER[d.trustLevel] ?? "#3f3f46";
  const glowColor   = TRUST_GLOW[d.trustLevel]   ?? "transparent";

  return (
    <div
      style={{
        background:   "#111114",
        border:       `1.5px solid ${selected ? "#60a5fa" : borderColor}`,
        borderRadius: 12,
        padding:      "12px 16px",
        minWidth:     180,
        maxWidth:     240,
        boxShadow:    selected
          ? "0 0 0 2px #3b82f666"
          : `0 0 12px ${glowColor}`,
        cursor: "pointer",
        userSelect: "none",
      }}
    >
      {/* Input handle — left */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: "#3f3f46", border: "1.5px solid #52525b", width: 10, height: 10 }}
      />

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#f4f4f5",
              lineHeight: 1.3,
              wordBreak: "break-word",
            }}
          >
            {d.name}
          </div>
        </div>
        <TrustDot level={d.trustLevel} />
      </div>

      {/* Description */}
      {d.description && (
        <div
          style={{
            fontSize: 11,
            color: "#71717a",
            lineHeight: 1.4,
            marginBottom: 8,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {d.description}
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          display:       "flex",
          alignItems:    "center",
          gap:           6,
          paddingTop:    6,
          borderTop:     "1px solid #1c1c1f",
          fontSize:      11,
          color:         "#52525b",
        }}
      >
        <span
          style={{
            background: "#18181b",
            border:     "1px solid #27272a",
            borderRadius: 6,
            padding:    "1px 7px",
            color:      d.componentCount > 0 ? "#a1a1aa" : "#3f3f46",
          }}
        >
          {d.componentCount} component{d.componentCount !== 1 ? "s" : ""}
        </span>
        <span style={{ flex: 1 }} />
        <span style={{ color: borderColor, fontSize: 10 }}>{d.trustLevel}</span>
      </div>

      {/* Output handle — right */}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: "#3f3f46", border: "1.5px solid #52525b", width: 10, height: 10 }}
      />
    </div>
  );
}

function TrustDot({ level }: { level: TrustLevel }) {
  const colors: Record<TrustLevel, string> = {
    new:              "#3f3f46",
    parsed:           "#475569",
    reviewed:         "#b45309",
    validated:        "#16a34a",
    proven:           "#15803d",
    trusted_template: "#2563eb",
  };
  return (
    <div
      style={{
        width:        8,
        height:       8,
        borderRadius: "50%",
        background:   colors[level] ?? "#3f3f46",
        marginTop:    3,
        flexShrink:   0,
      }}
    />
  );
}
