import { useState } from "react";
import { fetchValidation } from "../../api/validation";
import { StatusBadge } from "../ui/StatusBadge";
import type { ValidationIssue, ValidationSeverity } from "../../types/project";

type Props = {
  projectId: string;
};

const SEVERITY_ORDER: ValidationSeverity[] = [
  "error",
  "review_required",
  "warning",
  "info",
];

const SEVERITY_ICON: Record<ValidationSeverity, string> = {
  error: "✕",
  warning: "⚠",
  review_required: "◎",
  info: "ℹ",
};

export function ValidationPanel({ projectId }: Props) {
  const [items, setItems] = useState<ValidationIssue[]>([]);
  const [loading, setLoading] = useState(false);
  const [ran, setRan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<ValidationSeverity | "all">("all");

  const runValidation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchValidation(projectId);
      setItems(res.items);
      setRan(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const filtered =
    filter === "all"
      ? items
      : items.filter((i) => i.severity === filter);

  const counts = SEVERITY_ORDER.reduce(
    (acc, s) => {
      acc[s] = items.filter((i) => i.severity === s).length;
      return acc;
    },
    {} as Record<ValidationSeverity, number>
  );

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Toolbar */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>
          Validation
        </span>

        {ran && (
          <div style={{ display: "flex", gap: 6 }}>
            {SEVERITY_ORDER.map((s) =>
              counts[s] > 0 ? (
                <SeverityCounter
                  key={s}
                  severity={s}
                  count={counts[s]}
                  active={filter === s}
                  onClick={() => setFilter(filter === s ? "all" : s)}
                />
              ) : null
            )}
          </div>
        )}

        {ran && items.length > 0 && (
          <button
            onClick={() => setFilter("all")}
            style={{
              background: "transparent",
              border: "none",
              color: filter === "all" ? "#f4f4f5" : "#52525b",
              cursor: "pointer",
              fontSize: 12,
              padding: "4px 8px",
            }}
          >
            All ({items.length})
          </button>
        )}

        <button
          onClick={runValidation}
          disabled={loading}
          style={{
            background: loading ? "#1d2030" : "#7c3aed",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "6px 16px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 13,
            fontWeight: 500,
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Running Claude validation…" : ran ? "Re-run Validation" : "Run Validation"}
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: 16 }}>
        {error && (
          <div
            style={{
              padding: "10px 14px",
              background: "#3f1218",
              border: "1px solid #7f1d1d",
              borderRadius: 8,
              color: "#fca5a5",
              fontSize: 13,
              marginBottom: 12,
            }}
          >
            {error}
          </div>
        )}

        {!ran && !loading && !error && (
          <div
            style={{
              height: "60%",
              display: "grid",
              placeItems: "center",
              color: "#3f3f46",
              fontSize: 13,
              textAlign: "center",
            }}
          >
            <div>
              <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
              Click "Run Validation" to analyze the design with Claude.
              <br />
              Checks coverage, trust levels, missing protection circuits, and more.
            </div>
          </div>
        )}

        {ran && filtered.length === 0 && !loading && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
              paddingTop: 40,
              color: "#22c55e",
            }}
          >
            <div style={{ fontSize: 32 }}>✓</div>
            <div style={{ fontSize: 14 }}>No issues found.</div>
            <div style={{ fontSize: 12, color: "#52525b" }}>
              The design passed all checks.
            </div>
          </div>
        )}

        {filtered.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {SEVERITY_ORDER.flatMap((severity) =>
              filtered
                .filter((i) => i.severity === severity)
                .map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function IssueCard({ issue }: { issue: ValidationIssue }) {
  const [expanded, setExpanded] = useState(false);

  const severityColors: Record<ValidationSeverity, { bg: string; border: string; icon: string }> = {
    error: { bg: "#3f1218", border: "#7f1d1d", icon: "#fca5a5" },
    warning: { bg: "#3a2a10", border: "#854d0e", icon: "#fde68a" },
    review_required: { bg: "#1d2b4f", border: "#1d4ed8", icon: "#bfdbfe" },
    info: { bg: "#0c1a2e", border: "#1e3a5f", icon: "#93c5fd" },
  };

  const colors = severityColors[issue.severity];

  return (
    <div
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 10,
        padding: "10px 14px",
        cursor: "pointer",
      }}
      onClick={() => setExpanded((x) => !x)}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 14, color: colors.icon, flexShrink: 0 }}>
          {SEVERITY_ICON[issue.severity]}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: 13, color: "#f4f4f5" }}>
            {issue.title}
          </div>
        </div>
        <StatusBadge label={issue.severity} tone={issue.severity as Parameters<typeof StatusBadge>[0]["tone"]} />
        <span style={{ color: "#52525b", fontSize: 12 }}>{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${colors.border}` }}>
          <p style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1", lineHeight: 1.6 }}>
            {issue.message}
          </p>
          {issue.relatedKind && issue.relatedId && (
            <div
              style={{
                fontSize: 11,
                color: "#52525b",
                fontFamily: "monospace",
              }}
            >
              {issue.relatedKind}: {issue.relatedId}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SeverityCounter({
  severity,
  count,
  active,
  onClick,
}: {
  severity: ValidationSeverity;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  const colors: Record<ValidationSeverity, string> = {
    error: "#ef4444",
    warning: "#f59e0b",
    review_required: "#3b82f6",
    info: "#6b7280",
  };

  return (
    <button
      onClick={onClick}
      style={{
        background: active ? colors[severity] + "22" : "transparent",
        border: `1px solid ${active ? colors[severity] : "#27272a"}`,
        borderRadius: 6,
        padding: "3px 9px",
        cursor: "pointer",
        fontSize: 12,
        color: colors[severity],
        display: "flex",
        alignItems: "center",
        gap: 4,
      }}
    >
      <span>{SEVERITY_ICON[severity]}</span>
      <span>{count}</span>
    </button>
  );
}
