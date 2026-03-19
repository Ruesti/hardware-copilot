import type { TrustLevel, ValidationSeverity } from "../../types/project";

type StatusBadgeProps = {
  label: string;
  tone?: TrustLevel | ValidationSeverity | "neutral";
};

function getColors(tone: StatusBadgeProps["tone"]) {
  switch (tone) {
    case "error":
      return { bg: "#3f1218", border: "#7f1d1d", text: "#fecaca" };
    case "warning":
      return { bg: "#3a2a10", border: "#854d0e", text: "#fde68a" };
    case "info":
      return { bg: "#0f2f46", border: "#1d4ed8", text: "#bfdbfe" };
    case "new":
      return { bg: "#1f1f23", border: "#3f3f46", text: "#d4d4d8" };
    case "parsed":
      return { bg: "#1e293b", border: "#334155", text: "#cbd5e1" };
    case "reviewed":
      return { bg: "#3a2a10", border: "#854d0e", text: "#fde68a" };
    case "validated":
      return { bg: "#0f2f20", border: "#166534", text: "#bbf7d0" };
    case "proven":
      return { bg: "#0b3b2e", border: "#15803d", text: "#bbf7d0" };
    case "trusted_template":
      return { bg: "#1d2b4f", border: "#1d4ed8", text: "#bfdbfe" };
    default:
      return { bg: "#18181b", border: "#3f3f46", text: "#e4e4e7" };
  }
}

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  const colors = getColors(tone);

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "4px 8px",
        borderRadius: 999,
        fontSize: 12,
        border: `1px solid ${colors.border}`,
        background: colors.bg,
        color: colors.text,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
}