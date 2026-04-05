import { Panel } from "../ui/Panel";
import { StatusBadge } from "../ui/StatusBadge";
import type { ProjectState, Selection, ComponentItem } from "../../types/project";

type InspectorPanelProps = {
  project: ProjectState;
  components: ComponentItem[];
  selection: Selection;
};

export function InspectorPanel({
  project,
  components,
  selection,
}: InspectorPanelProps) {
  let title = "Nothing selected";
  let details = "Select a requirement, block or component in the workspace.";
  let badgeLabel: string | null = null;
  let badgeTone:
    | "new"
    | "parsed"
    | "reviewed"
    | "validated"
    | "proven"
    | "trusted_template"
    | "error"
    | "warning"
    | "info"
    | "neutral" = "neutral";

  if (selection?.kind === "requirement") {
    const req = project.requirements.find((r) => r.id === selection.id);
    if (req) {
      title = "Requirement";
      details = req.description;
      badgeLabel = "input";
      badgeTone = "neutral";
    }
  }

  if (selection?.kind === "block") {
    const block = project.blocks.find((b) => b.id === selection.id);
    if (block) {
      title = block.name;
      details = block.description ?? "No description available.";
      badgeLabel = block.trustLevel;
      badgeTone = block.trustLevel;
    }
  }

  if (selection?.kind === "component") {
    const comp = components.find((c) => c.id === selection.id);
    if (comp) {
      title = comp.name;
      details = comp.description || comp.value || "No description available.";
      badgeLabel = comp.trustLevel;
      badgeTone = comp.trustLevel;
    }
  }

  return (
    <Panel title="Inspector" subtitle="Context-sensitive technical details">
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <section
          style={{
            border: "1px solid #27272a",
            borderRadius: 12,
            background: "#0f0f12",
            padding: 12,
          }}
        >
          <div style={{ fontSize: 12, color: "#a1a1aa", marginBottom: 6 }}>
            Current selection
          </div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{title}</div>
          <div style={{ marginTop: 8, color: "#a1a1aa" }}>{details}</div>
          {badgeLabel ? (
            <div style={{ marginTop: 10 }}>
              <StatusBadge label={badgeLabel} tone={badgeTone} />
            </div>
          ) : null}
        </section>

        <section
          style={{
            border: "1px solid #27272a",
            borderRadius: 12,
            background: "#0f0f12",
            padding: 12,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Base notes</div>
          <ul
            style={{
              margin: 0,
              paddingLeft: 18,
              color: "#d4d4d8",
              fontSize: 14,
              lineHeight: 1.6,
            }}
          >
            <li>Inspector is now driven by current selection.</li>
            <li>Next step can attach real metadata per selected item.</li>
            <li>Later this panel should show pins, constraints and notes.</li>
          </ul>
        </section>

        <section
          style={{
            border: "1px solid #27272a",
            borderRadius: 12,
            background: "#0f0f12",
            padding: 12,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Project summary</div>
          <div style={{ fontSize: 14, color: "#d4d4d8", lineHeight: 1.6 }}>
            Requirements: {project.requirements.length}
            <br />
            Blocks: {project.blocks.length}
            <br />
            Components: {components.length}
          </div>
        </section>
      </div>
    </Panel>
  );
}