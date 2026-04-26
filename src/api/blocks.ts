import { API_BASE_URL } from "./config";
import type { DesignBlock, BlocksResponse, TrustLevel } from "../types/project";

export async function fetchBlocks(projectId: string): Promise<BlocksResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/blocks`);
  if (!res.ok) throw new Error(`Failed to fetch blocks: ${res.status}`);
  return res.json();
}

export async function createBlock(
  projectId: string,
  data: { name: string; description?: string; trustLevel?: TrustLevel }
): Promise<DesignBlock> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/blocks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: data.name,
      description: data.description,
      trust_level: data.trustLevel,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create block: ${res.status}`);
  return res.json();
}

export async function updateBlock(
  projectId: string,
  blockId: string,
  data: { name?: string; description?: string; trustLevel?: TrustLevel }
): Promise<DesignBlock> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/blocks/${blockId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.name,
        description: data.description,
        trust_level: data.trustLevel,
      }),
    }
  );
  if (!res.ok) throw new Error(`Failed to update block: ${res.status}`);
  return res.json();
}

export async function deleteBlock(projectId: string, blockId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/blocks/${blockId}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error(`Failed to delete block: ${res.status}`);
}
