import { useEffect, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import type { ProjectState, Selection } from "./types/project";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [project, setProject] = useState<ProjectState | null>(null);
  const [selection, setSelection] = useState<Selection>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    const loadProject = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/project`);

        if (!response.ok) {
          throw new Error(`Failed to load project: HTTP ${response.status}`);
        }

        const data: ProjectState = await response.json();

        if (!isCancelled) {
          setProject(data);
        }
      } catch (err) {
        console.error("Failed to load project:", err);

        let message = "Unknown error while loading project";

        if (err instanceof Error) {
          message = err.message;
        } else {
          try {
            message = JSON.stringify(err);
          } catch {
            message = String(err);
          }
        }

        if (!isCancelled) {
          setError(message);
          setProject(null);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadProject();

    return () => {
      isCancelled = true;
    };
  }, []);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#0f172a",
          color: "#e2e8f0",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        Loading project...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#0f172a",
          color: "#e2e8f0",
          fontFamily: "Inter, system-ui, sans-serif",
          padding: 24,
        }}
      >
        <div
          style={{
            maxWidth: 640,
            width: "100%",
            background: "#111827",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: 20,
          }}
        >
          <h1
            style={{
              margin: "0 0 12px 0",
              fontSize: 20,
              fontWeight: 600,
            }}
          >
            Backend connection error
          </h1>

          <p
            style={{
              margin: "0 0 16px 0",
              color: "#cbd5e1",
              lineHeight: 1.5,
            }}
          >
            The project could not be loaded from the backend.
          </p>

          <pre
            style={{
              margin: 0,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              background: "#0b1220",
              border: "1px solid #334155",
              borderRadius: 8,
              padding: 12,
              color: "#fca5a5",
              fontSize: 14,
            }}
          >
            {error}
          </pre>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#0f172a",
          color: "#e2e8f0",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        No project data available.
      </div>
    );
  }

  return (
    <AppShell
      project={project}
      selection={selection}
      onSelect={setSelection}
    />
  );
}

export default App;