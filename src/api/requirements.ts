import { API_BASE_URL } from "./config";
import type { RequirementsResponse } from "../types/project";

export async function fetchRequirements(): Promise<RequirementsResponse> {
  const response = await fetch(`${API_BASE_URL}/requirements`);

  if (!response.ok) {
    throw new Error(`Failed to fetch requirements: ${response.status}`);
  }

  return response.json();
}