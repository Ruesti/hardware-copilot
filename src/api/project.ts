import { API_BASE_URL } from "./config";
import type { ProjectState } from "../types/project";

export async function fetchProject(): Promise<ProjectState> {
  const response = await fetch(`${API_BASE_URL}/project`);

  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.status}`);
  }

  return response.json();
}