import { API_BASE_URL } from "./config";
import type { BlocksResponse } from "../types/project";

export async function fetchBlocks(): Promise<BlocksResponse> {
  const response = await fetch(`${API_BASE_URL}/blocks`);

  if (!response.ok) {
    throw new Error(`Failed to fetch blocks: ${response.status}`);
  }

  return response.json();
}