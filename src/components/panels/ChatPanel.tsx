import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MotorVerbindung } from "../../api/motor";
import type { MotorEreignis } from "../../types/motor";

const RAND = "1px solid #18181b";
const GEDAEMPFT = "#a1a1aa";
const FEHLERFARBE = "#f87171";
const RUECKFRAGE_RAHMEN = "1px solid #facc15";

const FELD_STIL = { background: "#18181b", border: RAND, borderRadius: 6,
                     color: "#e4e4e7", padding: "6px 8px" };
const KNOPF_STIL = { background: "#27272a", border: "none", borderRadius: 6,
                      color: "#fafafa", padding: "6px 10px", cursor: "pointer" };
const KNOPF_STIL_LEISE = { background: "transparent", border: RAND, borderRadius: 6,
                            color: GEDAEMPFT, padding: "6px 10px", cursor: "pointer" };

type Eintrag =
  | { typ: "nutzer"; text: string }
  | { typ: "claude-text"; text: string }
  | { typ: "werkzeug"; id: string; anzeige: string; status: "laeuft" | "ok" | "fehler" }
  | { typ: "rueckfrage"; id: string; art: "werkzeug" | "frage"; text: string; optionen: string[] }
  | { typ: "gedaempft"; text: string; farbe?: string };

function kuerzen(text: string, max = 60): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

/** Baut die Anzeige-Einträge aus der rohen Motor-Ereignisliste — pure Funktion, testbar. */
export function baueEintraege(ereignisse: MotorEreignis[]): Eintrag[] {
  const eintraege: Eintrag[] = [];
  for (const e of ereignisse) {
    if (e.typ === "nutzer") {
      eintraege.push({ typ: "nutzer", text: e.text });
    } else if (e.typ === "text_haeppchen") {
      const letzter = eintraege[eintraege.length - 1];
      if (letzter && letzter.typ === "claude-text") {
        eintraege[eintraege.length - 1] = { typ: "claude-text", text: letzter.text + e.text };
      } else {
        eintraege.push({ typ: "claude-text", text: e.text });
      }
    } else if (e.typ === "werkzeug_gestartet") {
      eintraege.push({ typ: "werkzeug", id: e.id, anzeige: e.anzeige, status: "laeuft" });
    } else if (e.typ === "werkzeug_fertig") {
      const idx = eintraege.findIndex((x) => x.typ === "werkzeug" && x.id === e.id);
      if (idx !== -1) {
        const alt = eintraege[idx] as Extract<Eintrag, { typ: "werkzeug" }>;
        eintraege[idx] = { ...alt, status: e.fehler ? "fehler" : "ok" };
      }
    } else if (e.typ === "rueckfrage") {
      eintraege.push({ typ: "rueckfrage", id: e.id, art: e.art, text: e.text, optionen: e.optionen });
    } else if (e.typ === "fertig") {
      if (e.fehler) {
        eintraege.push({ typ: "gedaempft", text: `⚠ ${e.fehler}`, farbe: FEHLERFARBE });
      }
      if (e.kosten_usd != null) {
        eintraege.push({ typ: "gedaempft",
          text: `— fertig (${e.kosten_usd.toFixed(2).replace(".", ",")} $)` });
      }
    } else if (e.typ === "verlauf") {
      // wird vom Live-Handler abgefangen (siehe ChatPanel-useEffect) —
      // der Server verschachtelt verlauf-Ereignisse nie ineinander.
      break;
    }
  }
  return eintraege;
}

/** Ermittelt aus dem Verlauf, ob serverseitig noch eine Antwort läuft:
 *  letztes "nutzer" ohne folgendes "fertig" bedeutet laufend. Pure
 *  Funktion, testbar — wird beim `verlauf`-Reconnect-Ereignis genutzt,
 *  um den Stopp-Knopf korrekt zu (re-)aktivieren. */
export function laeuftAusVerlauf(ereignisse: MotorEreignis[]): boolean {
  for (let i = ereignisse.length - 1; i >= 0; i--) {
    const e = ereignisse[i];
    if (e.typ === "fertig") return false;
    if (e.typ === "nutzer") return true;
  }
  return false;
}

export function ChatPanel() {
  const verbindungRef = useRef<MotorVerbindung | null>(null);
  const [alleEreignisse, setAlleEreignisse] = useState<MotorEreignis[]>([]);
  const [beantwortet, setBeantwortet] = useState<Record<string, string>>({});
  const [laeuft, setLaeuft] = useState(false);
  const [eingabe, setEingabe] = useState("");
  const [ablehnenOffen, setAblehnenOffen] = useState<Record<string, boolean>>({});
  const [ablehnenText, setAblehnenText] = useState<Record<string, string>>({});
  const [antwortText, setAntwortText] = useState<Record<string, string>>({});
  // Optimistisch verbunden: WS-Handshake ist meist sofort durch, so gibt es
  // bei normalem Verbindungsaufbau keinen Warn-Flackerer. Der Callback holt
  // uns bei einem echten Abbruch (close/error) auf `false`.
  const [verbunden, setVerbunden] = useState(true);

  useEffect(() => {
    const verbindung = new MotorVerbindung((e: MotorEreignis) => {
      if (e.typ === "verlauf") {
        setAlleEreignisse(e.ereignisse);
        setLaeuft(laeuftAusVerlauf(e.ereignisse));
        // Verlauf-Replay zeigt Rückfrage-Karten erneut aus den rohen
        // Ereignissen auf — ohne Reset blieben sie durch den lokalen
        // `beantwortet`-State fälschlich als "beantwortet" markiert.
        // Unbedenklich: der Server ist seit pop(id, None) idempotent,
        // eine erneute Antwort auf eine längst beantwortete Rückfrage
        // verpufft dort folgenlos.
        setBeantwortet({});
        return;
      }
      setAlleEreignisse((prev) => [...prev, e]);
      if (e.typ === "fertig") setLaeuft(false);
      if (e.typ === "werkzeug_fertig" && e.name.startsWith("mcp__bestand")) {
        window.dispatchEvent(new CustomEvent("bestand-geaendert"));
      }
      if (e.typ === "werkzeug_fertig" && e.name.startsWith("mcp__wissensschicht")) {
        window.dispatchEvent(new CustomEvent("wissen-geaendert"));
      }
      if (e.typ === "werkzeug_fertig" &&
          (e.name.startsWith("mcp__bestand__projekt") ||
           e.name.startsWith("mcp__bestand__position"))) {
        window.dispatchEvent(new CustomEvent("projekt-geaendert"));
      }
    }, setVerbunden);
    verbindungRef.current = verbindung;
    return () => verbindung.schliessen();
  }, []);

  const eintraege = useMemo(() => baueEintraege(alleEreignisse), [alleEreignisse]);

  const markiereBeantwortet = useCallback((id: string, kurz: string) => {
    setBeantwortet((prev) => ({ ...prev, [id]: kurz }));
  }, []);

  const senden = () => {
    if (laeuft) return;
    const text = eingabe.trim();
    if (!text) return;
    verbindungRef.current?.senden(text);
    setEingabe("");
    setLaeuft(true);
  };

  const onEingabeKeyDown = (ev: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      if (laeuft) return; // Text bleibt im Feld stehen, kein Senden während laufender Antwort
      senden();
    }
  };

  const abbrechen = () => verbindungRef.current?.abbrechen();

  const neuStarten = () => {
    if (!window.confirm("Wirklich neu starten? Der bisherige Verlauf wird verworfen.")) return;
    verbindungRef.current?.neustart();
    setAlleEreignisse([]);
    setBeantwortet({});
    setLaeuft(false);
  };

  const erlauben = (id: string) => {
    verbindungRef.current?.rueckfrageAntworten(id, true);
    markiereBeantwortet(id, "Erlauben");
  };

  const ablehnenBestaetigen = (id: string) => {
    const begruendung = ablehnenText[id]?.trim();
    verbindungRef.current?.rueckfrageAntworten(id, false, begruendung || undefined);
    markiereBeantwortet(id, begruendung ? `Ablehnen: ${begruendung}` : "Ablehnen");
  };

  const optionAntworten = (id: string, option: string) => {
    verbindungRef.current?.rueckfrageAntworten(id, true, option);
    markiereBeantwortet(id, option);
  };

  const freitextAntworten = (id: string) => {
    const text = antwortText[id]?.trim();
    if (!text) return;
    verbindungRef.current?.rueckfrageAntworten(id, true, text);
    markiereBeantwortet(id, text);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16,
                     display: "flex", flexDirection: "column", gap: 10 }}>
        {eintraege.map((eintrag, i) => {
          if (eintrag.typ === "nutzer") {
            return (
              <div key={i} style={{ alignSelf: "flex-end", maxWidth: "75%",
                                     background: "#27272a", borderRadius: 12,
                                     padding: "8px 12px", whiteSpace: "pre-wrap" }}>
                {eintrag.text}
              </div>
            );
          }
          if (eintrag.typ === "claude-text") {
            return (
              <div key={i} style={{ alignSelf: "flex-start", maxWidth: "85%",
                                     whiteSpace: "pre-wrap" }}>
                {eintrag.text}
              </div>
            );
          }
          if (eintrag.typ === "werkzeug") {
            const symbol = eintrag.status === "fehler" ? "⚠" : eintrag.status === "ok" ? "✓" : "⚙";
            const farbe = eintrag.status === "fehler" ? FEHLERFARBE : GEDAEMPFT;
            return (
              <div key={i} style={{ color: farbe, fontSize: 13 }}>
                {`${symbol} ${eintrag.anzeige}`}
              </div>
            );
          }
          if (eintrag.typ === "gedaempft") {
            return (
              <div key={i} style={{ color: eintrag.farbe ?? GEDAEMPFT, fontSize: 13 }}>
                {eintrag.text}
              </div>
            );
          }

          // rueckfrage
          const antwort = beantwortet[eintrag.id];
          if (antwort) {
            return (
              <div key={i} style={{ color: GEDAEMPFT, fontSize: 13 }}>
                {`beantwortet: ${kuerzen(antwort)}`}
              </div>
            );
          }
          return (
            <div key={i} style={{ border: RUECKFRAGE_RAHMEN, borderRadius: 8, padding: 12,
                                   display: "flex", flexDirection: "column", gap: 8 }}>
              <div>{eintrag.text}</div>
              {eintrag.art === "werkzeug" ? (
                <>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button type="button" onClick={() => erlauben(eintrag.id)} style={KNOPF_STIL}>
                      Erlauben
                    </button>
                    <button type="button" style={KNOPF_STIL_LEISE}
                      onClick={() => setAblehnenOffen((p) => ({ ...p, [eintrag.id]: true }))}>
                      Ablehnen
                    </button>
                  </div>
                  {ablehnenOffen[eintrag.id] && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      <textarea
                        value={ablehnenText[eintrag.id] ?? ""}
                        onChange={(e) =>
                          setAblehnenText((p) => ({ ...p, [eintrag.id]: e.target.value }))}
                        placeholder="Begründung (optional)"
                        style={{ ...FELD_STIL, minHeight: 50 }}
                      />
                      <button type="button" onClick={() => ablehnenBestaetigen(eintrag.id)}
                        style={{ ...KNOPF_STIL, alignSelf: "flex-start" }}>
                        Ablehnen bestätigen
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {eintrag.optionen.map((option) => (
                      <button key={option} type="button" style={KNOPF_STIL}
                        onClick={() => optionAntworten(eintrag.id, option)}>
                        {option}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      value={antwortText[eintrag.id] ?? ""}
                      onChange={(e) => setAntwortText((p) => ({ ...p, [eintrag.id]: e.target.value }))}
                      placeholder="Freitext-Antwort"
                      style={{ ...FELD_STIL, flex: 1 }}
                    />
                    <button type="button" onClick={() => freitextAntworten(eintrag.id)} style={KNOPF_STIL}>
                      Antworten
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {!verbunden && (
        <div style={{ padding: "4px 12px", fontSize: 12, color: FEHLERFARBE }}>
          ⚠ nicht verbunden — verbinde neu …
        </div>
      )}
      <div style={{ display: "flex", gap: 8, padding: 12, borderTop: RAND }}>
        <textarea
          value={eingabe}
          onChange={(e) => setEingabe(e.target.value)}
          onKeyDown={onEingabeKeyDown}
          placeholder={laeuft
            ? "Antwort läuft — Stopp zum Abbrechen"
            : "Nachricht an Claude — Enter sendet, Shift+Enter Zeilenumbruch"}
          style={{ ...FELD_STIL, flex: 1, minHeight: 44, resize: "vertical" }}
        />
        <button type="button" onClick={senden} disabled={laeuft} style={KNOPF_STIL}>
          Senden
        </button>
        {laeuft && (
          <button type="button" onClick={abbrechen}
            style={{ ...KNOPF_STIL_LEISE, color: FEHLERFARBE }}>
            Stopp
          </button>
        )}
        <button type="button" onClick={neuStarten} style={KNOPF_STIL_LEISE}>
          Neu starten
        </button>
      </div>
    </div>
  );
}
