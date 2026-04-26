import { useEffect, useState, useCallback } from "react";
import { AppShell } from "./components/layout/AppShell";
import { fetchProjects, createProject } from "./api/projects";
import { fetchRequirements } from "./api/requirements";
import { fetchBlocks } from "./api/blocks";
import { fetchComponents } from "./api/components";
import { fetchChat } from "./api/chat";
import type {
  ProjectListItem,
  Requirement,
  DesignBlock,
  ComponentItem,
  ChatMessage,
} from "./types/project";

export type ActiveTab = "chat" | "spec" | "components" | "datasheets" | "validation" | "diagram";

function App() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [blocks, setBlocks] = useState<DesignBlock[]>([]);
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat");
  const [loading, setLoading] = useState(true);
  const [projectLoading, setProjectLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects()
      .then((list) => {
        setProjects(list);
        if (list.length > 0) setActiveProjectId(list[0].id);
        else setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      });
  }, []);

  const loadProjectData = useCallback(async (projectId: string) => {
    setProjectLoading(true);
    try {
      const [reqs, blks, cmps, chat] = await Promise.all([
        fetchRequirements(projectId),
        fetchBlocks(projectId),
        fetchComponents(projectId),
        fetchChat(projectId),
      ]);
      setRequirements(reqs.items);
      setBlocks(blks.items);
      setComponents(cmps.items);
      setChatMessages(chat.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setProjectLoading(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeProjectId) loadProjectData(activeProjectId);
  }, [activeProjectId, loadProjectData]);

  const handleSelectProject = (id: string) => {
    setActiveProjectId(id);
  };

  const handleCreateProject = async (name: string) => {
    const project = await createProject(name);
    const item: ProjectListItem = {
      id: project.id,
      name: project.name,
      phase: project.phase,
      createdAt: project.createdAt,
    };
    setProjects((prev) => [item, ...prev]);
    setActiveProjectId(project.id);
  };

  if (loading) {
    return (
      <div style={centerStyle}>
        <div style={{ color: "#60a5fa", fontSize: 14 }}>Connecting to backend…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ ...centerStyle, padding: 24 }}>
        <div style={errorBoxStyle}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
            Backend connection error
          </div>
          <div style={{ color: "#94a3b8", marginBottom: 12, fontSize: 13 }}>
            Make sure the FastAPI backend is running on port 8000.
          </div>
          <pre style={preStyle}>{error}</pre>
          <button
            style={retryBtnStyle}
            onClick={() => { setError(null); setLoading(true); window.location.reload(); }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const activeProject = projects.find((p) => p.id === activeProjectId) ?? null;

  return (
    <AppShell
      projects={projects}
      activeProject={activeProject}
      activeTab={activeTab}
      requirements={requirements}
      blocks={blocks}
      components={components}
      chatMessages={chatMessages}
      projectLoading={projectLoading}
      onSelectProject={handleSelectProject}
      onCreateProject={handleCreateProject}
      onTabChange={setActiveTab}
      onRequirementsChange={setRequirements}
      onBlocksChange={setBlocks}
      onComponentsChange={setComponents}
      onChatMessagesChange={setChatMessages}
    />
  );
}

export default App;

const centerStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  background: "#09090b",
  color: "#f4f4f5",
  fontFamily: "Inter, system-ui, sans-serif",
};

const errorBoxStyle: React.CSSProperties = {
  maxWidth: 560,
  width: "100%",
  background: "#111114",
  border: "1px solid #3f3f46",
  borderRadius: 12,
  padding: 20,
};

const preStyle: React.CSSProperties = {
  margin: 0,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  background: "#0b0b0e",
  border: "1px solid #27272a",
  borderRadius: 8,
  padding: 12,
  color: "#fca5a5",
  fontSize: 13,
};

const retryBtnStyle: React.CSSProperties = {
  marginTop: 12,
  background: "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "8px 16px",
  cursor: "pointer",
  fontSize: 13,
};
