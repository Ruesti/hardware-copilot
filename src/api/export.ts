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

export function pcbDownloadUrl(projectId: string, mount: MountStyle): string {
  return `${API_BASE_URL}/projects/${projectId}/export/kicad/pcb?mount=${mount}`;
}

export function guideUrl(projectId: string, mount: MountStyle): string {
  return `${API_BASE_URL}/projects/${projectId}/export/kicad/guide?mount=${mount}`;
}

export type OpenResult = {
  path: string;
  opened: boolean;
  reason: string | null;
  pcbNote: string | null;
  files: string[];
};

export async function openInKicad(
  projectId: string,
  mount: MountStyle,
): Promise<OpenResult> {
  const res = await fetch(
    `${API_BASE_URL}/projects/${projectId}/export/kicad/open?mount=${mount}`,
    { method: "POST" },
  );
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Öffnen fehlgeschlagen: ${res.status}`);
  }
  return res.json();
}

export type KicadStatus = {
  installed: boolean;
  version: string | null;
  gui: boolean;
  symbols: boolean;
  pcbnew: boolean;
  installHint: string | null;
};

export async function fetchKicadStatus(): Promise<KicadStatus> {
  const res = await fetch(`${API_BASE_URL}/system/kicad`);
  if (!res.ok) throw new Error(`KiCad-Status fehlgeschlagen: ${res.status}`);
  return res.json();
}

export type InstallResult = {
  started: boolean;
  reason: string;
  command?: string;
};

export async function startKicadInstall(): Promise<InstallResult> {
  const res = await fetch(`${API_BASE_URL}/system/kicad/install`, { method: "POST" });
  if (!res.ok) throw new Error(`Installation fehlgeschlagen: ${res.status}`);
  return res.json();
}
