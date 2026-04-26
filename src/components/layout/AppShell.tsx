import type { ActiveTab } from "../../App";
import type {
  ProjectListItem,
  Requirement,
  DesignBlock,
  ComponentItem,
  ChatMessage,
} from "../../types/project";
import { ProjectSidebar } from "./ProjectSidebar";
import { ChatPanel } from "../panels/ChatPanel";
import { SpecPanel } from "../panels/SpecPanel";
import { ComponentsPanel } from "../panels/ComponentsPanel";
import { DatasheetPanel } from "../panels/DatasheetPanel";
import { ValidationPanel } from "../panels/ValidationPanel";
import { DiagramPanel } from "../panels/DiagramPanel";

type AppShellProps = {
  projects: ProjectListItem[];
  activeProject: ProjectListItem | null;
  activeTab: ActiveTab;
  requirements: Requirement[];
  blocks: DesignBlock[];
  components: ComponentItem[];
  chatMessages: ChatMessage[];
  projectLoading: boolean;
  onSelectProject: (id: string) => void;
  onCreateProject: (name: string) => Promise<void>;
  onTabChange: (tab: ActiveTab) => void;
  onRequirementsChange: (items: Requirement[]) => void;
  onBlocksChange: (items: DesignBlock[]) => void;
  onComponentsChange: (items: ComponentItem[]) => void;
  onChatMessagesChange: (items: ChatMessage[]) => void;
};

const TABS: { id: ActiveTab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "spec", label: "Spec" },
  { id: "components", label: "Components" },
  { id: "datasheets", label: "Datasheets" },
  { id: "validation", label: "Validation" },
  { id: "diagram", label: "Diagram" },
];

export function AppShell({
  projects,
  activeProject,
  activeTab,
  requirements,
  blocks,
  components,
  chatMessages,
  projectLoading,
  onSelectProject,
  onCreateProject,
  onTabChange,
  onRequirementsChange,
  onBlocksChange,
  onComponentsChange,
  onChatMessagesChange,
}: AppShellProps) {
  return (
    <div
      style={{
        height: "100vh",
        display: "grid",
        gridTemplateColumns: "220px 1fr",
        gridTemplateRows: "100%",
        background: "#09090b",
        color: "#f4f4f5",
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: 14,
      }}
    >
      <ProjectSidebar
        projects={projects}
        activeProjectId={activeProject?.id ?? null}
        onSelect={onSelectProject}
        onCreate={onCreateProject}
      />

      <div style={{ minWidth: 0, display: "flex", flexDirection: "column", height: "100%" }}>
        {/* Top bar */}
        <header
          style={{
            height: 52,
            borderBottom: "1px solid #27272a",
            display: "flex",
            alignItems: "center",
            padding: "0 20px",
            gap: 16,
            background: "#0c0c0f",
            flexShrink: 0,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            {activeProject ? (
              <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                <span style={{ fontWeight: 600, fontSize: 15, color: "#f4f4f5" }}>
                  {activeProject.name}
                </span>
                <span style={{ fontSize: 12, color: "#52525b" }}>
                  {activeProject.phase}
                </span>
              </div>
            ) : (
              <span style={{ color: "#52525b" }}>No project selected</span>
            )}
          </div>

          {/* Tab bar */}
          <nav style={{ display: "flex", gap: 2 }}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                style={{
                  background: activeTab === tab.id ? "#18181b" : "transparent",
                  color: activeTab === tab.id ? "#f4f4f5" : "#71717a",
                  border: activeTab === tab.id ? "1px solid #3f3f46" : "1px solid transparent",
                  borderRadius: 8,
                  padding: "5px 14px",
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: activeTab === tab.id ? 500 : 400,
                  transition: "all 0.1s",
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </header>

        {/* Panel area */}
        <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          {!activeProject && (
            <div
              style={{
                height: "100%",
                display: "grid",
                placeItems: "center",
                color: "#52525b",
              }}
            >
              Select or create a project to get started.
            </div>
          )}

          {activeProject && projectLoading && (
            <div
              style={{
                height: "100%",
                display: "grid",
                placeItems: "center",
                color: "#52525b",
              }}
            >
              Loading project data…
            </div>
          )}

          {activeProject && !projectLoading && (
            <>
              {activeTab === "chat" && (
                <ChatPanel
                  projectId={activeProject.id}
                  messages={chatMessages}
                  onMessagesChange={onChatMessagesChange}
                />
              )}
              {activeTab === "spec" && (
                <SpecPanel
                  projectId={activeProject.id}
                  requirements={requirements}
                  blocks={blocks}
                  onRequirementsChange={onRequirementsChange}
                  onBlocksChange={onBlocksChange}
                />
              )}
              {activeTab === "components" && (
                <ComponentsPanel
                  projectId={activeProject.id}
                  components={components}
                  blocks={blocks}
                  onComponentsChange={onComponentsChange}
                  onBlocksChange={onBlocksChange}
                  onDatasheetFetched={() => onTabChange("datasheets")}
                />
              )}
              {activeTab === "datasheets" && (
                <DatasheetPanel projectId={activeProject.id} />
              )}
              {activeTab === "validation" && (
                <ValidationPanel projectId={activeProject.id} />
              )}
              {activeTab === "diagram" && (
                <DiagramPanel
                  projectId={activeProject.id}
                  components={components}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
