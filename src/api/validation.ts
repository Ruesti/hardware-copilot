import { API_BASE_URL } from "./config";
import type { ValidationResponse } from "../types/validation";

export async function fetchValidation(): Promise<ValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/validation`);

  if (!response.ok) {
    throw new Error(`Failed to fetch validation: ${response.status}`);
  }

  return response.json();
}