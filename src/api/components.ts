import { API_BASE_URL } from "./config";
import type { ComponentItem, ComponentsResponse, TrustLevel } from "../types/project";

export async function fetchComponents(projectId: string): Promise<ComponentsResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/components`);
  if (!res.ok) throw new Error(`Failed to fetch components: ${res.status}`);
  return res.json();
}

export async function createComponent(
  projectId: string,
  data: {
    name: string;
    type?: string;
    value?: string;
    package?: string;
    manufacturer?: string;
    mpn?: string;
    description?: string;
    trustLevel?: TrustLevel;
    blockId?: string;
  }
): Promise<ComponentItem> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/components`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: data.name,
      type: data.type,
      value: data.value,
      package: data.package,
      manufacturer: data.manufacturer,
      mpn: data.mpn,
      description: data.description,
      trust_level: data.trustLevel,
      block_id: data.blockId,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create component: ${res.status}`);
  return res.json();
}

export async function updateComponent(
  projectId: string,
  cmpId: string,
  data: Partial<{
    name: string;
    type: string;
    value: string;
    package: string;
    manufacturer: string;
    mpn: string;
    description: string;
    trustLevel: TrustLevel;
    blockId: string;
  }>
): Promise<ComponentItem> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/components/${cmpId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.name,
        type: data.type,
        value: data.value,
        package: data.package,
        manufacturer: data.manufacturer,
        mpn: data.mpn,
        description: data.description,
        trust_level: data.trustLevel,
        block_id: data.blockId,
      }),
    }
  );
  if (!res.ok) throw new Error(`Failed to update component: ${res.status}`);
  return res.json();
}

export async function deleteComponent(projectId: string, cmpId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/components/${cmpId}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error(`Failed to delete component: ${res.status}`);
}

export async function suggestComponents(
  projectId: string
): Promise<{ created: number; components: ComponentItem[] }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/suggest-components`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Suggest components failed: ${res.status}`);
  return res.json();
}

export async function draftCircuit(
  projectId: string
): Promise<{ summary: string; blocksCreated: number }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/draft-circuit`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Draft circuit failed: ${res.status}`);
  return res.json();
}

export async function fetchComponentDatasheet(
  projectId: string,
  cmpId: string
): Promise<{ id: string; filename: string; sourceUrl: string; extractedData: Record<string, unknown> }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/components/${cmpId}/fetch-datasheet`,
    { method: "POST" }
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Fetch failed: ${res.status}`);
  }
  return res.json();
}
