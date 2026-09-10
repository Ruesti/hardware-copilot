export interface TeilKurz {
  id: number;
  bezeichnung: string;
  menge: number;
  klasse: string;
  herstellerNr: string;
  fach: string | null;
}

export interface AlternativeEintrag {
  bezeichnung: string;
  herstellerNr: string;
  hinweis: string;
  datum: string;
}

export interface PreisEintrag {
  quelle: string;
  preisEur: number;
  url: string;
  datum: string;
}

export interface TeilDetail extends Omit<TeilKurz, "fach"> {
  fach: string | null;
  eckdaten: string;
  datenblattUrl: string;
  alternativen: AlternativeEintrag[];
  preise: PreisEintrag[];
}

export interface TeilNeu {
  bezeichnung: string;
  menge: number;
  fach: string;
  klasse?: string;
  herstellerNr?: string;
  eckdaten?: string;
  datenblattUrl?: string;
}
