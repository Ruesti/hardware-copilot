import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
};

export default function App() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "offline">("checking");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then(async (res) => {
        if (!res.ok) throw new Error("health check failed");
        return (await res.json()) as HealthResponse;
      })
      .then((data) => {
        setBackendStatus(data.status === "ok" ? "ok" : "offline");
      })
      .catch(() => {
        setBackendStatus("offline");
      });
  }, []);

  return (
    <div style={styles.app}>
      <aside style={styles.left}>
        <div>
          <h1 style={styles.h1}>Hardware Copilot</h1>
          <p style={styles.muted}>v1 workspace</p>
        </div>

        <nav style={styles.nav}>
          <button style={styles.navButton}>Dashboard</button>
          <button style={styles.navButton}>Design Workspace</button>
          <button style={styles.navButton}>Components</button>
          <button style={styles.navButton}>Validation</button>
          <button style={styles.navButton}>Settings</button>
        </nav>
      </aside>

      <main style={styles.main}>
        <div style={styles.card}>
          <h2 style={styles.h2}>Workspace</h2>
          <p style={styles.text}>
            Backend status: <strong>{backendStatus}</strong>
          </p>
          <p style={styles.muted}>
            Nächster Schritt: App Shell mit ChatPanel, DesignTree und Inspector.
          </p>
        </div>
      </main>

      <aside style={styles.right}>
        <h3 style={styles.h3}>Inspector</h3>
        <p style={styles.muted}>Noch leer.</p>
      </aside>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: "100vh",
    display: "grid",
    gridTemplateColumns: "240px 1fr 320px",
    background: "#09090b",
    color: "#f4f4f5",
    fontFamily: "Inter, system-ui, sans-serif",
  },
  left: {
    borderRight: "1px solid #27272a",
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 24,
    background: "#0f0f12",
  },
  main: {
    padding: 24,
  },
  right: {
    borderLeft: "1px solid #27272a",
    padding: 16,
    background: "#0f0f12",
  },
  h1: {
    fontSize: 20,
    margin: 0,
  },
  h2: {
    fontSize: 22,
    marginTop: 0,
  },
  h3: {
    fontSize: 14,
    marginTop: 0,
    color: "#e4e4e7",
  },
  muted: {
    color: "#a1a1aa",
    fontSize: 14,
  },
  text: {
    fontSize: 15,
    color: "#e4e4e7",
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  navButton: {
    background: "#18181b",
    color: "#f4f4f5",
    border: "1px solid #27272a",
    borderRadius: 10,
    padding: "10px 12px",
    textAlign: "left",
    cursor: "pointer",
  },
  card: {
    background: "#111114",
    border: "1px solid #27272a",
    borderRadius: 16,
    padding: 24,
  },
};