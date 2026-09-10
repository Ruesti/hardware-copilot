import type { PreisEintrag } from "./bestand";

export type { PreisEintrag };

export interface ProjektKurz {
  id: number;
  name: string;
  status: "offen" | "gebaut";
  positionen: number;
  fehlen: number;
}

export interface PositionZeile {
  id: number;
  referenz: string;
  bezeichnung: string;
  menge: number;
  klasse: string;
  baugruppe: string;
  teilId: number | null;
  pins: Record<string, string> | null;
  kicadSymbol: string;
  kicadFootprint: string;
  notiz: string;
  bestand: { menge: number; fach: string | null } | null;
  status: "da" | "knapp" | "fehlt" | "nicht_zugeordnet";
  preis: PreisEintrag | null;
  allePreise: PreisEintrag[];
}

export interface Zusammenfassung {
  positionen: number;
  gedeckt: number;
  fehlen: number;
  fehlteileKostenEur: number;
  ohnePreis: number;
}

export interface ProjektDetail {
  id: number;
  name: string;
  beschreibung: string;
  status: "offen" | "gebaut";
  angelegtAm: string;
  positionen: PositionZeile[];
  zusammenfassung: Zusammenfassung;
}
