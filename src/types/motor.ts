// Wire-Format für den Motor-WebSocket (`/motor/ws`) — Feld "typ" als
// Diskriminante, exakt gemäß backend/app/motor/schnittstelle.py.
// ACHTUNG: `kosten_usd` bleibt snake_case (so sendet es das Backend) —
// nicht in camelCase umbenennen.
export type MotorEreignis =
  | { typ: "text_haeppchen"; text: string }
  | { typ: "werkzeug_gestartet"; id: string; name: string; anzeige: string }
  | { typ: "werkzeug_fertig"; id: string; name: string; fehler: boolean }
  | {
      typ: "rueckfrage";
      id: string;
      art: "werkzeug" | "frage";
      text: string;
      optionen: string[];
    }
  | { typ: "fertig"; fehler: string | null; kosten_usd?: number | null }
  | { typ: "nutzer"; text: string }
  | { typ: "verlauf"; ereignisse: MotorEreignis[] };
