import { Panel } from "../ui/Panel";
import { StatusBadge } from "../ui/StatusBadge";
import type { ValidationIssue } from "../../types/project";

type ValidationPanelProps = {
  issues: ValidationIssue[];
};

export function ValidationPanel({ issues }: ValidationPanelProps) {
  return (
    <Panel
      title="Validation Center"
      subtitle="Warnings, assumptions and pending technical checks"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {issues.map((issue) => (
          <div
            key={issue.id}
            style={{
              border: "1px solid #27272a",
              borderRadius: 12,
              background: "#0f0f12",
              padding: 12,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 12,
                alignItems: "center",
              }}
            >
              <div style={{ fontWeight: 600 }}>{issue.title}</div>
              <StatusBadge label={issue.severity} tone={issue.severity} />
            </div>

            <div
              style={{
                fontSize: 13,
                color: "#a1a1aa",
                marginTop: 6,
                lineHeight: 1.5,
              }}
            >
              {issue.description}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}