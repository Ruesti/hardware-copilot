import { API_BASE_URL } from "./config";

export type ExportInstance = {
  ref: string;
  name: string;
  value: string;
  block: string;
  status: "mapped" | "fallback" | "unverified";
};

export type ExportReport = {
  instances: ExportInstance[];
  unmapped: {
    name: string | null;
    mpn: string | null;
    type: string | null;
    block_name: string;
    reason: string;
  }[];
  warnings: string[];
  counts: {
    mapped: number;
    fallback: number;
    unverified: number;
    unmapped: number;
    no_footprint: number;
  };
};

export type MountStyle = "smd" | "tht";

export async function fetchExportReport(
  projectId: string,
  mount: MountStyle,
): Promise<ExportReport> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/export/kicad/report?mount=${mount}`,
  );
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Export-Report fehlgeschlagen: ${res.status}`);
  }
  return res.json();
}

export function kicadDownloadUrl(projectId: string, mount: MountStyle): string {
  return `${API_BASE_URL}/projects/${projectId}/export/kicad?mount=${mount}`;
}
