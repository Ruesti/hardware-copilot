import { API_BASE_URL } from "./config";
import type {
  BlockConnection,
  ComponentItem,
  ComponentsResponse,
  DiagramBlock,
  TrustLevel,
} from "../types/project";

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

async function extractDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    return (body as { detail?: string }).detail ?? `${fallback}: ${res.status}`;
  } catch {
    return `${fallback}: ${res.status}`;
  }
}

export async function suggestComponents(
  projectId: string
): Promise<{ created: number; components: ComponentItem[] }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/suggest-components`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(await extractDetail(res, "Suggest components failed"));
  return res.json();
}

export async function draftCircuit(
  projectId: string
): Promise<{ summary: string; blocksCreated: number; removedBlockIds?: string[] }> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/draft-circuit`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(await extractDetail(res, "Draft circuit failed"));
  return res.json();
}

export type RefreshDesignResult = {
  blocks: DiagramBlock[];
  components: ComponentItem[];
  connections: BlockConnection[];
  removedBlockIds: string[];
};

export async function refreshDesign(
  projectId: string,
  schematicMode: "auto" | "manual" = "auto"
): Promise<RefreshDesignResult> {
  const url = new URL(`${API_BASE_URL}/projects/${projectId}/refresh-design`);
  url.searchParams.set("schematic_mode", schematicMode);
  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Refresh design failed: ${res.status}`);
  }
  return res.json();
}

export async function setSchematicValidated(
  projectId: string,
  blockId: string,
  validated: boolean
): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/blocks/${blockId}/validate-schematic`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ validated }),
    }
  );
  if (!res.ok) throw new Error(`Validate schematic failed: ${res.status}`);
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
