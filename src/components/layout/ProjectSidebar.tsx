import { useState } from "react";
import type { ProjectListItem } from "../../types/project";

type Props = {
  projects: ProjectListItem[];
  activeProjectId: string | null;
  onSelect: (id: string) => void;
  onCreate: (name: string) => Promise<void>;
};

export function ProjectSidebar({ projects, activeProjectId, onSelect, onCreate }: Props) {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [saving, setSaving] = useState(false);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setSaving(true);
    try {
      await onCreate(name);
      setNewName("");
      setCreating(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <aside
      style={{
        borderRight: "1px solid #27272a",
        background: "#0c0c0f",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      {/* Logo */}
      <div
        style={{
          padding: "16px 16px 12px",
          borderBottom: "1px solid #1c1c1f",
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 700, color: "#f4f4f5", letterSpacing: "-0.3px" }}>
          Hardware Copilot
        </div>
        <div style={{ fontSize: 11, color: "#52525b", marginTop: 2 }}>
          AI-powered PCB workbench
        </div>
      </div>

      {/* Section header */}
      <div
        style={{
          padding: "10px 16px 6px",
          fontSize: 11,
          fontWeight: 600,
          color: "#52525b",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        Projects
      </div>

      {/* Project list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 8px" }}>
        {projects.length === 0 && (
          <div style={{ padding: "12px 8px", fontSize: 12, color: "#3f3f46" }}>
            No projects yet.
          </div>
        )}
        {projects.map((p) => {
          const isActive = p.id === activeProjectId;
          return (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              style={{
                width: "100%",
                background: isActive ? "#18181b" : "transparent",
                border: isActive ? "1px solid #3f3f46" : "1px solid transparent",
                borderRadius: 8,
                padding: "8px 10px",
                textAlign: "left",
                cursor: "pointer",
                marginBottom: 2,
                transition: "all 0.1s",
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: isActive ? "#f4f4f5" : "#a1a1aa",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {p.name}
              </div>
              <div style={{ fontSize: 11, color: "#52525b", marginTop: 2 }}>
                {p.phase}
              </div>
            </button>
          );
        })}
      </div>

      {/* New project */}
      <div style={{ padding: "8px", borderTop: "1px solid #1c1c1f" }}>
        {creating ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <input
              autoFocus
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreate();
                if (e.key === "Escape") { setCreating(false); setNewName(""); }
              }}
              placeholder="Project name…"
              style={{
                background: "#09090b",
                color: "#f4f4f5",
                border: "1px solid #3f3f46",
                borderRadius: 7,
                padding: "7px 10px",
                fontSize: 13,
                outline: "none",
              }}
            />
            <div style={{ display: "flex", gap: 4 }}>
              <button
                onClick={handleCreate}
                disabled={saving || !newName.trim()}
                style={actionBtnStyle("#2563eb")}
              >
                {saving ? "Creating…" : "Create"}
              </button>
              <button
                onClick={() => { setCreating(false); setNewName(""); }}
                style={actionBtnStyle("#27272a")}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setCreating(true)}
            style={{
              width: "100%",
              background: "transparent",
              color: "#71717a",
              border: "1px dashed #3f3f46",
              borderRadius: 8,
              padding: "8px",
              cursor: "pointer",
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
            }}
          >
            <span style={{ fontSize: 16, lineHeight: 1 }}>+</span>
            New Project
          </button>
        )}
      </div>
    </aside>
  );
}

function actionBtnStyle(bg: string): React.CSSProperties {
  return {
    flex: 1,
    background: bg,
    color: "#f4f4f5",
    border: "none",
    borderRadius: 7,
    padding: "6px",
    cursor: "pointer",
    fontSize: 12,
  };
}
