import { BestandPanel } from "../panels/BestandPanel";
import { ChatPanel } from "../panels/ChatPanel";
import { ProjektePanel } from "../panels/ProjektePanel";
import { WissensPanel } from "../panels/WissensPanel";

export type TabId = "bestand" | "projekte" | "wissen" | "chat";

const TABS: { id: TabId; label: string }[] = [
  { id: "bestand", label: "Bestand" },
  { id: "projekte", label: "Projekte" },
  { id: "wissen", label: "Wissen" },
  { id: "chat", label: "Chat" },
];

type Props = { tab: TabId; onTabChange: (t: TabId) => void };

export function AppShell({ tab, onTabChange }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh",
                  background: "#09090b", color: "#e4e4e7" }}>
      <header style={{ display: "flex", alignItems: "center", gap: 16,
                       padding: "10px 16px", borderBottom: "1px solid #18181b" }}>
        <strong>Hardware-Copilot</strong>
        <nav style={{ display: "flex", gap: 4 }}>
          {TABS.map((t) => (
            <button key={t.id} onClick={() => onTabChange(t.id)}
              style={{ padding: "6px 14px", borderRadius: 6, border: "none",
                       cursor: "pointer",
                       background: tab === t.id ? "#27272a" : "transparent",
                       color: tab === t.id ? "#fafafa" : "#a1a1aa" }}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main style={{ flex: 1, minHeight: 0, display: "flex" }}>
        {tab === "bestand" ? <BestandPanel />
          : tab === "projekte" ? <ProjektePanel />
          : tab === "wissen" ? <WissensPanel />
          : <ChatPanel />}
      </main>
    </div>
  );
}
