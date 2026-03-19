type TopBarProps = {
  projectName: string;
  phase: string;
};

export function TopBar({ projectName, phase }: TopBarProps) {
  return (
    <header
      style={{
        height: 56,
        borderBottom: "1px solid #27272a",
        background: "#0f0f12",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
      }}
    >
      <div>
        <div style={{ fontSize: 14, color: "#a1a1aa" }}>Current project</div>
        <div style={{ fontSize: 16, fontWeight: 600 }}>{projectName}</div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          color: "#e4e4e7",
          fontSize: 13,
        }}
      >
        <span style={{ color: "#a1a1aa" }}>Phase</span>
        <span
          style={{
            border: "1px solid #27272a",
            background: "#18181b",
            borderRadius: 999,
            padding: "6px 10px",
            textTransform: "capitalize",
          }}
        >
          {phase}
        </span>
      </div>
    </header>
  );
}