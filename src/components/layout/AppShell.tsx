import type { ProjectState, Selection, ComponentItem } from "../../types/project";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { WorkspaceLayout } from "./WorkspaceLayout";
import { ChatPanel } from "../panels/ChatPanel";
import { DesignTreePanel } from "../panels/DesignTreePanel";
import { InspectorPanel } from "../panels/InspectorPanel";
import ValidationPanel from "../panels/ValidationPanel";

type AppShellProps = {
  project: ProjectState;
  components: ComponentItem[];
  selection: Selection;
  onSelect: (selection: Selection) => void;
};

export function AppShell({
  project,
  components,
  selection,
  onSelect,
}: AppShellProps) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "240px 1fr",
        background: "#09090b",
        color: "#f4f4f5",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <Sidebar />

      <div
        style={{
          minWidth: 0,
          display: "grid",
          gridTemplateRows: "56px 1fr",
        }}
      >
        <TopBar projectName={project.name} phase={project.phase} />

        <div style={{ minHeight: 0 }}>
          <WorkspaceLayout
            left={<ChatPanel messages={project.chatMessages} />}
            center={
              <DesignTreePanel
                requirements={project.requirements}
                blocks={project.blocks}
                components={components}
                selection={selection}
                onSelect={onSelect}
              />
            }
            right={
              <InspectorPanel
                project={project}
                components={components}
                selection={selection}
              />
            }
            bottom={<ValidationPanel />}
          />
        </div>
      </div>
    </div>
  );
}