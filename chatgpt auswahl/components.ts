import { API_BASE_URL } from "./config";
import type { ComponentsResponse } from "../types/component";

export async function fetchComponents(): Promise<ComponentsResponse> {
  const response = await fetch(`${API_BASE_URL}/components`);

  if (!response.ok) {
    throw new Error(`Failed to fetch components: ${response.status}`);
  }

  return response.json();
}