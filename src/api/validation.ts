import { API_BASE_URL } from "./config";
import type { ValidationResponse } from "../types/project";

export async function fetchValidation(projectId: string): Promise<ValidationResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/validation`);
  if (!res.ok) throw new Error(`Failed to fetch validation: ${res.status}`);
  return res.json();
}
