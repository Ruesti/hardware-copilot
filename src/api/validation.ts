import type { ValidationResponse } from "../types/validation";

export async function fetchValidation(): Promise<ValidationResponse> {
  const response = await fetch("http://127.0.0.1:8000/validation");

  if (!response.ok) {
    throw new Error(`Failed to fetch validation: ${response.status}`);
  }

  return response.json();
}