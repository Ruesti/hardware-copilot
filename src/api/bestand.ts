import { anfrage } from "./anfrage";
import type { TeilDetail, TeilKurz, TeilNeu } from "../types/bestand";

export function fetchTeile(suche = "", klasse = ""): Promise<TeilKurz[]> {
  const p = new URLSearchParams();
  if (suche) p.set("suche", suche);
  if (klasse) p.set("klasse", klasse);
  return anfrage(`/bestand/teile?${p}`);
}

export const fetchTeil = (id: number): Promise<TeilDetail> =>
  anfrage(`/bestand/teile/${id}`);

export const createTeil = (teil: TeilNeu): Promise<{ meldung: string; id: number }> =>
  anfrage("/bestand/teile", { method: "POST", body: JSON.stringify(teil) });

export const patchMenge = (id: number, delta: number): Promise<{ meldung: string; menge: number }> =>
  anfrage(`/bestand/teile/${id}/menge`, { method: "PATCH", body: JSON.stringify({ delta }) });

export const leuchten = (id: number): Promise<{ meldung: string }> =>
  anfrage(`/bestand/teile/${id}/leuchten`, { method: "POST", body: JSON.stringify({}) });

export const fetchBestandKlassen = (): Promise<string[]> => anfrage("/bestand/klassen");
