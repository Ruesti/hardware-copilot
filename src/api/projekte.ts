import { anfrage } from "./anfrage";
import { API_BASE_URL } from "./config";
import type { KicadExportErgebnis, ProjektDetail, ProjektKurz } from "../types/projekte";

export const fetchProjekte = (): Promise<ProjektKurz[]> => anfrage("/projekte");

export const fetchProjekt = (id: number): Promise<ProjektDetail> =>
  anfrage(`/projekte/${id}`);

export const createProjekt = (
  name: string,
  beschreibung?: string
): Promise<{ meldung: string; id: number }> =>
  anfrage("/projekte", {
    method: "POST",
    body: JSON.stringify({ name, beschreibung: beschreibung ?? "" }),
  });

export const positionZuordnen = (
  projektId: number,
  referenz: string,
  teilId: number
): Promise<{ meldung: string }> =>
  anfrage(`/projekte/${projektId}/positionen/${encodeURIComponent(referenz)}/zuordnen`, {
    method: "POST",
    body: JSON.stringify({ teilId }),
  });

export const projektAbbuchen = (projektId: number): Promise<{ meldung: string }> =>
  anfrage(`/projekte/${projektId}/abbuchen`, { method: "POST", body: JSON.stringify({}) });

export const kicadExport = (projektId: number): Promise<KicadExportErgebnis> =>
  anfrage(`/projekte/${projektId}/kicad-export`, { method: "POST", body: JSON.stringify({}) });

export const kicadOeffnen = (projektId: number): Promise<{ meldung: string }> =>
  anfrage(`/projekte/${projektId}/kicad-oeffnen`, { method: "POST", body: JSON.stringify({}) });

export const anleitungUrl = (projektId: number): string =>
  `${API_BASE_URL}/projekte/${projektId}/kicad-anleitung`;
