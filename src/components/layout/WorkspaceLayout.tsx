import type { ReactNode } from "react";

type WorkspaceLayoutProps = {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
  bottom: ReactNode;
};

export function WorkspaceLayout({
  left,
  center,
  right,
  bottom,
}: WorkspaceLayoutProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "380px 1fr 340px",
        gridTemplateRows: "1fr 180px",
        gap: 16,
        padding: 16,
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      <div style={{ minHeight: 0 }}>{left}</div>
      <div style={{ minHeight: 0 }}>{center}</div>
      <div style={{ minHeight: 0, gridRow: "1 / span 2" }}>{right}</div>
      <div style={{ minHeight: 0, gridColumn: "1 / span 2" }}>{bottom}</div>
    </div>
  );
}