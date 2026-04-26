import { API_BASE_URL } from "./config";
import type { BlockConnection, DiagramBlock } from "../types/project";

export type DiagramResponse = {
  blocks: DiagramBlock[];
  connections: BlockConnection[];
};

export async function fetchDiagram(projectId: string): Promise<DiagramResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/diagram`);
  if (!res.ok) throw new Error(`Failed to fetch diagram: ${res.status}`);
  return res.json();
}

export async function updateBlockPosition(
  projectId: string,
  blockId: string,
  x: number,
  y: number
): Promise<void> {
  await fetch(`${API_BASE_URL}/projects/${projectId}/blocks/${blockId}/position`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pos_x: x, pos_y: y }),
  });
}

export async function createConnection(
  projectId: string,
  data: { sourceBlockId: string; targetBlockId: string; label?: string; connType?: string }
): Promise<BlockConnection> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/connections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_block_id: data.sourceBlockId,
      target_block_id: data.targetBlockId,
      label: data.label ?? "",
      conn_type: data.connType ?? "signal",
    }),
  });
  if (!res.ok) throw new Error(`Failed to create connection: ${res.status}`);
  return res.json();
}

export async function deleteConnection(
  projectId: string,
  connId: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/connections/${connId}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error(`Failed to delete connection: ${res.status}`);
}

export async function suggestConnections(
  projectId: string
): Promise<{ created: number; connections: BlockConnection[] }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/suggest-connections`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Suggest connections failed: ${res.status}`);
  return res.json();
}

export async function describeBlockCircuit(
  projectId: string,
  blockId: string
): Promise<{ blockId: string; schematic: string }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/blocks/${blockId}/describe-circuit`,
    { method: "POST" }
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Failed: ${res.status}`);
  }
  return res.json();
}
