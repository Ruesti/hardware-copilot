import { API_BASE_URL } from "./config";
import type { DatasheetsResponse } from "../types/project";

export async function fetchDatasheets(projectId: string): Promise<DatasheetsResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/datasheets`);
  if (!res.ok) throw new Error(`Failed to fetch datasheets: ${res.status}`);
  return res.json();
}

export async function uploadDatasheet(
  projectId: string,
  file: File
): Promise<{ id: string; filename: string; extractedData: Record<string, unknown> }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/datasheet`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Upload failed: ${res.status}`);
  }
  return res.json();
}
