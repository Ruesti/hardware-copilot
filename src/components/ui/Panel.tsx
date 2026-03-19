import type { PropsWithChildren, ReactNode } from "react";

type PanelProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}>;

export function Panel({ title, subtitle, actions, children }: PanelProps) {
  return (
    <section
      style={{
        background: "#111114",
        border: "1px solid #27272a",
        borderRadius: 16,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <header
        style={{
          padding: "14px 16px",
          borderBottom: "1px solid #27272a",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 15, fontWeight: 600 }}>{title}</div>
          {subtitle ? (
            <div style={{ fontSize: 12, color: "#a1a1aa", marginTop: 2 }}>
              {subtitle}
            </div>
          ) : null}
        </div>
        {actions}
      </header>

      <div
        style={{
          padding: 16,
          minHeight: 0,
          overflow: "auto",
        }}
      >
        {children}
      </div>
    </section>
  );
}