import { useEffect, useRef, useState } from "react";
import { streamChat, streamInterviewChat, clearChat } from "../../api/chat";
import { createRequirement } from "../../api/requirements";
import { draftCircuit, suggestComponents } from "../../api/components";
import { suggestConnections } from "../../api/diagram";
import { CircuitOverview } from "../diagram/CircuitOverview";
import { SchematicModal } from "../diagram/SchematicModal";
import { SpecSidebar } from "./SpecSidebar";
import type { ChatMessage, DiagramBlock, BlockConnection, ComponentItem, Requirement } from "../../types/project";

const REQ_TAG_RE = /<req\s+title="([^"]+)"\s+description="([^"]+)"\s*\/>/;

type Props = {
  projectId: string;
  messages: ChatMessage[];
  onMessagesChange: (msgs: ChatMessage[]) => void;
  diagramBlocks: DiagramBlock[];
  diagramConnections: BlockConnection[];
  components: ComponentItem[];
  requirements: Requirement[];
  onDiagramRefresh: () => void;
  onRequirementsChange: (items: Requirement[]) => void;
  /**
   * Wenn true: rechte Sidebar (SpecSidebar/CircuitOverview) und das interne
   * SchematicModal werden ausgeblendet — der einbettende Container kümmert sich um beides.
   */
  embedded?: boolean;
  /**
   * Wird nach jedem abgeschlossenen Assistant-Stream oder erfolgreichen
   * AI-Action (Draft/Suggest/Connections) aufgerufen. Workbench nutzt das für Auto-Refresh.
   */
  onAssistantTurn?: (content: string, source: "stream" | "draft" | "suggest" | "connections") => void;
  /** Initialer Zustand des Interview-Toggles. Workbench nutzt das, um Interview standardmäßig an zu lassen. */
  defaultInterviewMode?: boolean;
};

export function ChatPanel({
  projectId,
  messages,
  onMessagesChange,
  diagramBlocks,
  diagramConnections,
  components,
  requirements,
  onDiagramRefresh,
  onRequirementsChange,
  embedded = false,
  onAssistantTurn,
  defaultInterviewMode = false,
}: Props) {
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [aiAction, setAiAction] = useState<string | null>(null);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [interviewMode, setInterviewMode] = useState(defaultInterviewMode);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const selectedBlock = diagramBlocks.find((b) => b.id === selectedBlockId) ?? null;
  const hasBlocks = diagramBlocks.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const handleSend = async (text: string) => {
    const msg = text.trim();
    if (!msg || streaming) return;
    setInput("");

    const userMsg: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: msg,
    };
    onMessagesChange([...messages, userMsg]);
    setStreaming(true);
    setStreamingText("");

    const controller = new AbortController();
    abortRef.current = controller;
    let collected = "";

    const streamFn = interviewMode ? streamInterviewChat : streamChat;

    await streamFn({
      projectId,
      message: msg,
      signal: controller.signal,
      onChunk: (chunk) => {
        collected += chunk;
        setStreamingText(collected.replace(REQ_TAG_RE, "").trim());
      },
      onDone: async () => {
        // Extract and save requirement if present
        const match = REQ_TAG_RE.exec(collected);
        if (match) {
          try {
            const newReq = await createRequirement(projectId, {
              title: match[1],
              description: match[2],
            });
            onRequirementsChange([...requirements, newReq]);
          } catch {
            // non-critical
          }
        }
        const displayContent = collected.replace(REQ_TAG_RE, "").trim();
        const assistantMsg: ChatMessage = {
          id: `tmp-${Date.now()}-a`,
          role: "assistant",
          content: displayContent,
        };
        onMessagesChange([...messages, userMsg, assistantMsg]);
        setStreamingText("");
        setStreaming(false);
        onAssistantTurn?.(collected, "stream");
      },
      onError: (err) => {
        const errMsg: ChatMessage = {
          id: `tmp-${Date.now()}-err`,
          role: "assistant",
          content: `Error: ${err}`,
        };
        onMessagesChange([...messages, userMsg, errMsg]);
        setStreamingText("");
        setStreaming(false);
      },
    });
  };

  const handleAiAction = async (action: "draft" | "suggest" | "connections") => {
    if (streaming || aiAction) return;

    const labels: Record<typeof action, string> = {
      draft: "Drafting circuit…",
      suggest: "Suggesting components…",
      connections: "Suggesting connections…",
    };
    setAiAction(labels[action]);

    try {
      if (action === "draft") {
        const result = await draftCircuit(projectId);
        let body: string;
        if (result.blocksCreated === 0 && requirements.length === 0) {
          body =
            "Noch keine Anforderungen erfasst. Aktiviere oben den **Interview**-Button — die KI stellt dann gezielte Fragen und legt automatisch Anforderungen an, aus denen sich das Blockschaltbild ergibt.";
        } else if (result.blocksCreated === 0) {
          body = `Keine neuen Blöcke nötig.\n\n${result.summary}`;
        } else {
          body = `**Circuit drafted!** ${result.blocksCreated} Block(s) hinzugefügt.\n\n${result.summary}`;
        }
        const notice: ChatMessage = {
          id: `tmp-${Date.now()}`,
          role: "assistant",
          content: body,
        };
        onMessagesChange([...messages, notice]);
        onDiagramRefresh();
        onAssistantTurn?.(notice.content, "draft");
      } else if (action === "suggest") {
        const result = await suggestComponents(projectId);
        const notice: ChatMessage = {
          id: `tmp-${Date.now()}`,
          role: "assistant",
          content: `**Components suggested!** ${result.created} component(s) added to the project. Switch to the Components tab to review.`,
        };
        onMessagesChange([...messages, notice]);
        onDiagramRefresh();
        onAssistantTurn?.(notice.content, "suggest");
      } else {
        const result = await suggestConnections(projectId);
        const notice: ChatMessage = {
          id: `tmp-${Date.now()}`,
          role: "assistant",
          content: `**Connections suggested!** ${result.created} connection(s) added between blocks.`,
        };
        onMessagesChange([...messages, notice]);
        onDiagramRefresh();
        onAssistantTurn?.(notice.content, "connections");
      }
    } catch (err) {
      const errMsg: ChatMessage = {
        id: `tmp-${Date.now()}`,
        role: "assistant",
        content: `Action failed: ${err instanceof Error ? err.message : String(err)}`,
      };
      onMessagesChange([...messages, errMsg]);
    } finally {
      setAiAction(null);
    }
  };

  const handleClear = async () => {
    if (!confirm("Clear all chat messages?")) return;
    await clearChat(projectId);
    onMessagesChange([]);
  };

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background: "#09090b",
        overflow: "hidden",
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          padding: "8px 16px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          gap: 6,
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 12, color: "#52525b", flex: 1 }}>
          Engineering Copilot
        </span>
        <button
          onClick={() => setInterviewMode((m) => !m)}
          style={{
            background: interviewMode ? "#7c3aed" : "transparent",
            color: interviewMode ? "#fff" : "#7c3aed",
            border: "1px solid #7c3aed",
            borderRadius: 7,
            padding: "4px 10px",
            cursor: "pointer",
            fontSize: 12,
            fontWeight: interviewMode ? 600 : 400,
          }}
          title="Interview-Modus: Claude stellt gezielte Fragen und speichert Anforderungen automatisch"
        >
          {interviewMode ? "● Interview" : "Interview"}
        </button>
        {!embedded && (
          <>
            <ActionButton
              label={aiAction === "Drafting circuit…" ? "Drafting…" : "Draft Circuit"}
              loading={aiAction === "Drafting circuit…"}
              disabled={!!aiAction || streaming}
              onClick={() => handleAiAction("draft")}
              color="#7c3aed"
            />
            <ActionButton
              label={aiAction === "Suggesting components…" ? "Suggesting…" : "Suggest Components"}
              loading={aiAction === "Suggesting components…"}
              disabled={!!aiAction || streaming}
              onClick={() => handleAiAction("suggest")}
              color="#0891b2"
            />
            <ActionButton
              label={aiAction === "Suggesting connections…" ? "Connecting…" : "Suggest Connections"}
              loading={aiAction === "Suggesting connections…"}
              disabled={!!aiAction || streaming || !hasBlocks}
              onClick={() => handleAiAction("connections")}
              color="#059669"
            />
          </>
        )}
        <button onClick={handleClear} style={ghostBtnStyle} title="Clear chat">
          ✕
        </button>
      </div>

      {/* Main content row */}
      <div style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden" }}>
        {/* Left: chat */}
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          {/* Messages */}
          <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "16px" }}>
            {messages.length === 0 && !streamingText && (
              <div
                style={{
                  color: "#3f3f46",
                  fontSize: 13,
                  textAlign: "center",
                  marginTop: 40,
                }}
              >
                Start the conversation — describe your requirements or ask for a circuit draft.
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}

              {streamingText && (
                <MessageBubble
                  msg={{ id: "streaming", role: "assistant", content: streamingText }}
                  streaming
                />
              )}
            </div>
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: "12px 16px",
              borderTop: "1px solid #18181b",
              flexShrink: 0,
            }}
          >
            <div style={{ display: "flex", gap: 8 }}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(input);
                  }
                }}
                disabled={streaming}
                placeholder="Describe requirements or ask Claude… (Enter to send, Shift+Enter for newline)"
                rows={2}
                style={{
                  flex: 1,
                  background: "#111114",
                  color: "#f4f4f5",
                  border: "1px solid #27272a",
                  borderRadius: 10,
                  padding: "10px 12px",
                  fontSize: 13,
                  outline: "none",
                  resize: "none",
                  lineHeight: 1.5,
                  fontFamily: "inherit",
                }}
              />
              <button
                onClick={() => handleSend(input)}
                disabled={streaming || !input.trim()}
                style={{
                  background: streaming ? "#1d2030" : "#2563eb",
                  color: "#fff",
                  border: "none",
                  borderRadius: 10,
                  padding: "0 18px",
                  cursor: streaming ? "not-allowed" : "pointer",
                  fontSize: 13,
                  fontWeight: 500,
                  alignSelf: "stretch",
                  opacity: streaming || !input.trim() ? 0.5 : 1,
                }}
              >
                {streaming ? "…" : "Send"}
              </button>
            </div>
          </div>
        </div>

        {/* Right column: SpecSidebar in interview mode, CircuitOverview otherwise.
             Im embedded-Modus übernimmt der Container das Rendering. */}
        {!embedded && interviewMode && (
          <SpecSidebar
            requirements={requirements}
            blocks={diagramBlocks}
            components={components}
          />
        )}
        {!embedded && !interviewMode && hasBlocks && (
          <CircuitOverview
            blocks={diagramBlocks}
            connections={diagramConnections}
            onBlockClick={setSelectedBlockId}
          />
        )}
      </div>

      {/* Schematic modal — nur außerhalb des Workbench */}
      {!embedded && selectedBlock && (
        <SchematicModal
          projectId={projectId}
          block={selectedBlock}
          components={components}
          onClose={() => setSelectedBlockId(null)}
        />
      )}
    </div>
  );
}

function MessageBubble({
  msg,
  streaming = false,
}: {
  msg: ChatMessage;
  streaming?: boolean;
}) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        alignSelf: isUser ? "flex-end" : "flex-start",
        maxWidth: "85%",
        background: isUser ? "#1e3a5f" : "#111114",
        border: `1px solid ${isUser ? "#1d4ed8" : "#27272a"}`,
        borderRadius: 12,
        padding: "10px 14px",
      }}
    >
      <div
        style={{
          fontSize: 11,
          color: isUser ? "#93c5fd" : "#52525b",
          marginBottom: 5,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {msg.role}
      </div>
      <div
        style={{
          fontSize: 13,
          lineHeight: 1.6,
          color: "#e4e4e7",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {msg.content}
        {streaming && (
          <span
            style={{
              display: "inline-block",
              width: 8,
              height: 13,
              background: "#60a5fa",
              marginLeft: 2,
              verticalAlign: "text-bottom",
              animation: "blink 1s step-end infinite",
            }}
          />
        )}
      </div>
    </div>
  );
}

function ActionButton({
  label,
  loading,
  disabled,
  onClick,
  color,
}: {
  label: string;
  loading: boolean;
  disabled: boolean;
  onClick: () => void;
  color: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: "transparent",
        color: disabled ? "#3f3f46" : color,
        border: `1px solid ${disabled ? "#27272a" : color}`,
        borderRadius: 7,
        padding: "4px 10px",
        cursor: disabled ? "not-allowed" : "pointer",
        fontSize: 12,
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {loading ? "…" : label}
    </button>
  );
}

const ghostBtnStyle: React.CSSProperties = {
  background: "transparent",
  color: "#52525b",
  border: "none",
  cursor: "pointer",
  fontSize: 14,
  padding: "4px 6px",
  borderRadius: 6,
};
