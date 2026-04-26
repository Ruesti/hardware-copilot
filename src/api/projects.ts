import { API_BASE_URL } from "./config";
import type { Project, ProjectListItem, ProjectsListResponse } from "../types/project";

export async function fetchProjects(): Promise<ProjectListItem[]> {
  const res = await fetch(`${API_BASE_URL}/projects`);
  if (!res.ok) throw new Error(`Failed to fetch projects: ${res.status}`);
  const data: ProjectsListResponse = await res.json();
  return data.items;
}

export async function fetchProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}`);
  if (!res.ok) throw new Error(`Failed to fetch project: ${res.status}`);
  return res.json();
}

export async function createProject(name: string, phase = "Draft"): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, phase }),
  });
  if (!res.ok) throw new Error(`Failed to create project: ${res.status}`);
  return res.json();
}

export async function updateProject(
  projectId: string,
  data: { name?: string; phase?: string }
): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update project: ${res.status}`);
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.status}`);
}
