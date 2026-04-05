import { useEffect, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { fetchProject } from "./api/project";
import { fetchComponents } from "./api/components";
import type { ProjectState, Selection, ComponentItem } from "./types/project";

function App() {
  const [project, setProject] = useState<ProjectState | null>(null);
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [selection, setSelection] = useState<Selection>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [projectData, componentsResponse] = await Promise.all([
          fetchProject(),
          fetchComponents(),
        ]);

        if (!isCancelled) {
          setProject(projectData);
          setComponents(componentsResponse.items);
        }
      } catch (err) {
        console.error("Failed to load app data:", err);

        let message = "Unknown error while loading app data";

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
          setComponents([]);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadData();

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
            The project data could not be loaded from the backend.
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
      components={components}
      selection={selection}
      onSelect={setSelection}
    />
  );
}

export default App;