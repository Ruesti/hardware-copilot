import { Panel } from "../ui/Panel";
import { StatusBadge } from "../ui/StatusBadge";
import type {
  Requirement,
  DesignBlock,
  ComponentItem,
  Selection,
} from "../../types/project";

type DesignTreePanelProps = {
  requirements: Requirement[];
  blocks: DesignBlock[];
  components: ComponentItem[];
  selection: Selection;
  onSelect: (selection: Selection) => void;
};

export function DesignTreePanel({
  requirements,
  blocks,
  components,
  selection,
  onSelect,
}: DesignTreePanelProps) {
  return (
    <Panel
      title="Design Workspace"
      subtitle="Requirements, blocks and selected components"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <section>
          <h3 style={{ fontSize: 14, margin: "0 0 10px 0", color: "#e4e4e7" }}>
            Requirements
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {requirements.map((item) => {
              const isSelected =
                selection?.kind === "requirement" && selection.id === item.id;

              return (
                <div
                  key={item.id}
                  onClick={() => onSelect({ kind: "requirement", id: item.id })}
                  style={{
                    padding: 10,
                    borderRadius: 10,
                    border: "1px solid #27272a",
                    background: isSelected ? "#1e293b" : "#0f0f12",
                    fontSize: 14,
                    cursor: "pointer",
                  }}
                >
                  {item.description}
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <h3 style={{ fontSize: 14, margin: "0 0 10px 0", color: "#e4e4e7" }}>
            Blocks
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {blocks.map((block) => {
              const isSelected =
                selection?.kind === "block" && selection.id === block.id;

              return (
                <div
                  key={block.id}
                  onClick={() => onSelect({ kind: "block", id: block.id })}
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    border: "1px solid #27272a",
                    background: isSelected ? "#1e293b" : "#0f0f12",
                    cursor: "pointer",
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
                    <div style={{ fontWeight: 600 }}>{block.name}</div>
                    <StatusBadge label={block.trustLevel} tone={block.trustLevel} />
                  </div>
                  {block.description ? (
                    <div
                      style={{
                        fontSize: 13,
                        color: "#a1a1aa",
                        marginTop: 6,
                      }}
                    >
                      {block.description}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <h3 style={{ fontSize: 14, margin: "0 0 10px 0", color: "#e4e4e7" }}>
            Components
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {components.map((component) => {
              const isSelected =
                selection?.kind === "component" && selection.id === component.id;

              return (
                <div
                  key={component.id}
                  onClick={() => onSelect({ kind: "component", id: component.id })}
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    border: "1px solid #27272a",
                    background: isSelected ? "#1e293b" : "#0f0f12",
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{component.name}</div>
                    <div style={{ fontSize: 13, color: "#a1a1aa", marginTop: 4 }}>
                      {component.description || component.value || "No details available."}
                    </div>
                  </div>
                  <StatusBadge
                    label={component.trustLevel}
                    tone={component.trustLevel}
                  />
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </Panel>
  );
}