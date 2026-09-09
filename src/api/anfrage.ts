import { API_BASE_URL } from "./config";

export async function anfrage<T>(pfad: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${pfad}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const daten = await res.json().catch(() => null);
    throw new Error(daten?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}
