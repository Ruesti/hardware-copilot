const navItems = [
  "Dashboard",
  "Design Workspace",
  "Components",
  "Validation",
  "Settings",
];

export function Sidebar() {
  return (
    <aside
      style={{
        borderRight: "1px solid #27272a",
        background: "#0f0f12",
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 24,
      }}
    >
      <div>
        <h1 style={{ fontSize: 20, margin: 0 }}>Hardware Copilot</h1>
        <p style={{ fontSize: 13, color: "#a1a1aa", marginTop: 6 }}>
          v1 workspace
        </p>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {navItems.map((item, index) => (
          <button
            key={item}
            style={{
              background: index === 1 ? "#18181b" : "transparent",
              color: "#f4f4f5",
              border: "1px solid #27272a",
              borderRadius: 10,
              padding: "10px 12px",
              textAlign: "left",
              cursor: "pointer",
            }}
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
}