import { Panel } from "../ui/Panel";
import type { ChatMessage } from "../../types/project";

type ChatPanelProps = {
  messages: ChatMessage[];
};

export function ChatPanel({ messages }: ChatPanelProps) {
  return (
    <Panel
      title="Copilot Chat"
      subtitle="Requirements and architecture discussion"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              border: "1px solid #27272a",
              background: message.role === "user" ? "#18181b" : "#101826",
              borderRadius: 12,
              padding: 12,
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: "#a1a1aa",
                marginBottom: 6,
                textTransform: "uppercase",
              }}
            >
              {message.role}
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.5 }}>{message.content}</div>
          </div>
        ))}

        <div
          style={{
            marginTop: 8,
            display: "grid",
            gridTemplateColumns: "1fr auto",
            gap: 8,
          }}
        >
          <input
            placeholder="Describe the next requirement or ask for a refinement..."
            style={{
              background: "#09090b",
              color: "#f4f4f5",
              border: "1px solid #27272a",
              borderRadius: 10,
              padding: "12px 14px",
              outline: "none",
            }}
          />
          <button
            style={{
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: 10,
              padding: "0 16px",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </div>
      </div>
    </Panel>
  );
}