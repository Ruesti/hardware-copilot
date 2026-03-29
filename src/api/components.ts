import type { ComponentsResponse } from "../types/component";

export async function fetchComponents(): Promise<ComponentsResponse> {
  const response = await fetch("http://127.0.0.1:8000/components");

  if (!response.ok) {
    throw new Error(`Failed to fetch components: ${response.status}`);
  }

  return response.json();
}