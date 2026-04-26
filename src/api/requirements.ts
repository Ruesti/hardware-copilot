import { API_BASE_URL } from "./config";
import type { Requirement, RequirementsResponse } from "../types/project";

export async function fetchRequirements(projectId: string): Promise<RequirementsResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/requirements`);
  if (!res.ok) throw new Error(`Failed to fetch requirements: ${res.status}`);
  return res.json();
}

export async function createRequirement(
  projectId: string,
  data: { title: string; description?: string; status?: string }
): Promise<Requirement> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/requirements`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create requirement: ${res.status}`);
  return res.json();
}

export async function updateRequirement(
  projectId: string,
  reqId: string,
  data: { title?: string; description?: string; status?: string }
): Promise<Requirement> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/requirements/${reqId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  );
  if (!res.ok) throw new Error(`Failed to update requirement: ${res.status}`);
  return res.json();
}

export async function deleteRequirement(projectId: string, reqId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/requirements/${reqId}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error(`Failed to delete requirement: ${res.status}`);
}
