import { API_BASE_URL } from "./config";

export type UsageEntry = {
  createdAt: string;
  endpoint: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheCreateTokens: number;
};

export type UsageSummary = {
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCacheReadTokens: number;
  totalCacheCreateTokens: number;
  totalCostUsd: number;
  recent: UsageEntry[];
};

export async function fetchUsage(projectId: string): Promise<UsageSummary> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/usage`);
  if (!res.ok) throw new Error(`Failed to fetch usage: ${res.status}`);
  return res.json();
}
