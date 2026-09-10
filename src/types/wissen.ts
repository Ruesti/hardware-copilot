export interface RegelKurz {
  id: string;
  bereich: string;
  aussage: string;
  staerke: string;
  stufe: string;
  klasse: string;
}

export interface RegelVoll {
  id: string;
  bereich: string;
  aussage: string;
  begruendung: string;
  staerke: string;
  stufe: string;
  datum_eintrag: string;
  datum_geprueft: string;
  ausnahmen: string[];
  quelle: Record<string, string>;
  geltung: Record<string, string>;
}

export interface BlockKurz {
  id: string;
  titel: string;
  kernbauteil: string;
  topologie: string;
}

export type BlockVoll = BlockKurz & { volltext: string };

export interface LueckeEintrag {
  datum: string;
  frage: string;
  grund: string;
  status: string;
}
