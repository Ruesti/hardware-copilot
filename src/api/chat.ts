import { API_BASE_URL } from "./config";
import type { ChatHistoryResponse } from "../types/project";

export async function fetchChat(projectId: string): Promise<ChatHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/chat`);
  if (!res.ok) throw new Error(`Failed to fetch chat: ${res.status}`);
  return res.json();
}

export async function clearChat(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/chat`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to clear chat: ${res.status}`);
}

export type StreamChatOptions = {
  projectId: string;
  message: string;
  onChunk: (text: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
  signal?: AbortSignal;
};

export async function streamChat({
  projectId,
  message,
  onChunk,
  onDone,
  onError,
  signal,
}: StreamChatOptions): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/projects/${projectId}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: message }),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    onError(err instanceof Error ? err.message : "Network error");
    return;
  }

  if (!response.ok || !response.body) {
    onError(`Stream failed: ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        try {
          const parsed = JSON.parse(payload) as { text?: string; done?: boolean };
          if (parsed.text) onChunk(parsed.text);
          if (parsed.done) onDone();
        } catch {
          // skip malformed chunks
        }
      }
    }
  } catch (err) {
    if ((err as Error).name !== "AbortError") {
      onError(err instanceof Error ? err.message : "Stream read error");
    }
  } finally {
    reader.releaseLock();
  }
}
