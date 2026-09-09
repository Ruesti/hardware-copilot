import { useCallback, useEffect, useState } from "react";
import { createTeil, fetchBestandKlassen, fetchTeil, fetchTeile,
         leuchten, patchMenge } from "../../api/bestand";
import type { TeilDetail, TeilKurz, TeilNeu } from "../../types/bestand";

const RAND = "1px solid #18181b";
const GEDAEMPFT = "#a1a1aa";
const FEHLERFARBE = "#f87171";

const istWebUrl = (url: string) =>
  url.startsWith("https://") || url.startsWith("http://");

type FormularState = {
  bezeichnung: string;
  menge: string;
  fach: string;
  klasse: string;
  herstellerNr: string;
  eckdaten: string;
  datenblattUrl: string;
};

const LEERES_FORMULAR: FormularState = {
  bezeichnung: "", menge: "1", fach: "", klasse: "",
  herstellerNr: "", eckdaten: "", datenblattUrl: "",
};

export function BestandPanel() {
  const [teile, setTeile] = useState<TeilKurz[]>([]);
  const [klassen, setKlassen] = useState<string[]>([]);
  const [suche, setSuche] = useState("");
  const [klasse, setKlasse] = useState("");
  const [auswahl, setAuswahl] = useState<TeilDetail | null>(null);
  const [meldung, setMeldung] = useState("");
  const [fehler, setFehler] = useState("");
  const [formularOffen, setFormularOffen] = useState(false);
  const [formular, setFormular] = useState<FormularState>(LEERES_FORMULAR);

  const laden = useCallback(() => {
    fetchTeile(suche, klasse)
      .then((t) => { setTeile(t); setFehler(""); })
      .catch((e) => setFehler(e.message));
  }, [suche, klasse]);

  useEffect(() => { laden(); }, [laden]);
  useEffect(() => {
    fetchBestandKlassen().then(setKlassen).catch((e) => setFehler(e.message));
  }, []);

  const detailLaden = (id: number) =>
    fetchTeil(id)
      .then((t) => { setAuswahl(t); setFehler(""); })
      .catch((e) => setFehler(e.message));

  const mengeAendern = (id: number, delta: number) =>
    patchMenge(id, delta)
      .then((r) => { setMeldung(r.meldung); setFehler(""); laden(); if (auswahl?.id === id) detailLaden(id); })
      .catch((e) => setFehler(e.message));

  const fachLeuchten = (id: number) =>
    leuchten(id)
      .then((r) => { setMeldung(r.meldung); setFehler(""); })
      .catch((e) => setFehler(e.message));

  const absenden = (ev: React.FormEvent) => {
    ev.preventDefault();
    const teil: TeilNeu = {
      bezeichnung: formular.bezeichnung,
      menge: Number(formular.menge),
      fach: formular.fach,
      klasse: formular.klasse || undefined,
      herstellerNr: formular.herstellerNr || undefined,
      eckdaten: formular.eckdaten || undefined,
      datenblattUrl: formular.datenblattUrl || undefined,
    };
    createTeil(teil)
      .then((r) => {
        setMeldung(r.meldung);
        setFehler("");
        setFormularOffen(false);
        setFormular(LEERES_FORMULAR);
        laden();
      })
      .catch((e) => setFehler(e.message));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* Liste links */}
        <div style={{ width: 360, display: "flex", flexDirection: "column",
                       borderRight: RAND, minHeight: 0 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8,
                         padding: 12, borderBottom: RAND }}>
            <input
              value={suche}
              onChange={(e) => setSuche(e.target.value)}
              placeholder="Suchen — Bezeichnung, Hersteller-Nr, Eckdaten"
              style={{ background: "#18181b", border: RAND, borderRadius: 6,
                        color: "#e4e4e7", padding: "6px 8px" }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <select
                value={klasse}
                onChange={(e) => setKlasse(e.target.value)}
                style={{ flex: 1, background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }}
              >
                <option value="">alle Klassen</option>
                {klassen.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
              <button
                type="button"
                onClick={() => setFormularOffen((o) => !o)}
                style={{ background: "#27272a", border: "none", borderRadius: 6,
                          color: "#fafafa", padding: "6px 10px", cursor: "pointer" }}
              >
                + Teil anlegen
              </button>
            </div>
          </div>

          {formularOffen && (
            <form onSubmit={absenden}
              style={{ display: "flex", flexDirection: "column", gap: 8,
                        padding: 12, borderBottom: RAND }}>
              <label htmlFor="teil-bezeichnung">Bezeichnung</label>
              <input id="teil-bezeichnung" required
                value={formular.bezeichnung}
                onChange={(e) => setFormular({ ...formular, bezeichnung: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <label htmlFor="teil-menge">Menge</label>
              <input id="teil-menge" type="number" min={0} required
                value={formular.menge}
                onChange={(e) => setFormular({ ...formular, menge: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <label htmlFor="teil-fach">Fach (Regal/Position)</label>
              <input id="teil-fach" required
                value={formular.fach}
                onChange={(e) => setFormular({ ...formular, fach: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <label htmlFor="teil-klasse">Klasse</label>
              <input id="teil-klasse" list="teil-klassen-liste"
                value={formular.klasse}
                onChange={(e) => setFormular({ ...formular, klasse: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />
              <datalist id="teil-klassen-liste">
                {klassen.map((k) => <option key={k} value={k} />)}
              </datalist>

              <label htmlFor="teil-herstellerNr">Hersteller-Nr</label>
              <input id="teil-herstellerNr"
                value={formular.herstellerNr}
                onChange={(e) => setFormular({ ...formular, herstellerNr: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <label htmlFor="teil-eckdaten">Eckdaten</label>
              <input id="teil-eckdaten"
                value={formular.eckdaten}
                onChange={(e) => setFormular({ ...formular, eckdaten: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <label htmlFor="teil-datenblattUrl">Datenblatt-URL</label>
              <input id="teil-datenblattUrl"
                value={formular.datenblattUrl}
                onChange={(e) => setFormular({ ...formular, datenblattUrl: e.target.value })}
                style={{ background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }} />

              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit"
                  style={{ background: "#27272a", border: "none", borderRadius: 6,
                            color: "#fafafa", padding: "6px 10px", cursor: "pointer" }}>
                  Anlegen
                </button>
                <button type="button" onClick={() => setFormularOffen(false)}
                  style={{ background: "transparent", border: RAND, borderRadius: 6,
                            color: GEDAEMPFT, padding: "6px 10px", cursor: "pointer" }}>
                  Abbrechen
                </button>
              </div>
            </form>
          )}

          <div style={{ overflowY: "auto", flex: 1 }}>
            {teile.map((t) => (
              <div key={t.id}
                onClick={() => detailLaden(t.id)}
                style={{ padding: "8px 12px", borderBottom: RAND, cursor: "pointer",
                          background: auswahl?.id === t.id ? "#18181b" : "transparent" }}>
                <div>{`[T-${t.id}] ${t.bezeichnung}`}</div>
                <div style={{ display: "flex", justifyContent: "space-between",
                               alignItems: "center", marginTop: 4 }}>
                  <span style={{ color: GEDAEMPFT, fontSize: 12 }}>
                    {`${t.menge} · ${t.fach ?? "—"} · ${t.klasse}`}
                  </span>
                  <span style={{ display: "flex", gap: 4 }}>
                    <button type="button"
                      onClick={(e) => { e.stopPropagation(); mengeAendern(t.id, -1); }}
                      style={{ background: "#27272a", border: "none", borderRadius: 4,
                                color: "#e4e4e7", padding: "2px 6px", cursor: "pointer" }}>
                      −1
                    </button>
                    <button type="button"
                      onClick={(e) => { e.stopPropagation(); mengeAendern(t.id, 1); }}
                      style={{ background: "#27272a", border: "none", borderRadius: 4,
                                color: "#e4e4e7", padding: "2px 6px", cursor: "pointer" }}>
                      +1
                    </button>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail rechts */}
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16 }}>
          {!auswahl ? (
            <div style={{ color: GEDAEMPFT }}>Kein Teil ausgewählt.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <h2 style={{ margin: 0 }}>{`[T-${auswahl.id}] ${auswahl.bezeichnung}`}</h2>

              <div>
                <div>{`Menge: ${auswahl.menge}`}</div>
                <div>{`Fach: ${auswahl.fach ?? "—"}`}</div>
                <div>{`Klasse: ${auswahl.klasse}`}</div>
                <div>{`Hersteller-Nr: ${auswahl.herstellerNr || "—"}`}</div>
                <div>{`Eckdaten: ${auswahl.eckdaten || "—"}`}</div>
                <div>
                  Datenblatt:{" "}
                  {!auswahl.datenblattUrl
                    ? <span style={{ color: GEDAEMPFT }}>— keine hinterlegt</span>
                    : istWebUrl(auswahl.datenblattUrl)
                    ? <a href={auswahl.datenblattUrl} target="_blank" rel="noreferrer"
                         style={{ color: "#e4e4e7" }}>{auswahl.datenblattUrl}</a>
                    : <span>{auswahl.datenblattUrl}</span>}
                </div>
              </div>

              <div>
                <div style={{ fontWeight: "bold", marginBottom: 4 }}>Alternativen</div>
                {auswahl.alternativen.length === 0 ? (
                  <div style={{ color: GEDAEMPFT }}>— keine vermerkt</div>
                ) : (
                  auswahl.alternativen.map((a, i) => (
                    <div key={i} style={{ borderBottom: RAND, padding: "4px 0" }}>
                      <div>{`${a.bezeichnung} (${a.herstellerNr})`}</div>
                      <div style={{ color: GEDAEMPFT, fontSize: 12 }}>
                        {`${a.hinweis} — Stand vom ${a.datum}`}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div>
                <div style={{ fontWeight: "bold", marginBottom: 4 }}>Preise</div>
                {auswahl.preise.length === 0 ? (
                  <div style={{ color: GEDAEMPFT }}>— keine Preise erfasst</div>
                ) : (
                  auswahl.preise.map((p, i) => (
                    <div key={i} style={{ borderBottom: RAND, padding: "4px 0" }}>
                      <div>{`${p.quelle}: ${p.preisEur.toFixed(2)} €`}</div>
                      <div style={{ color: GEDAEMPFT, fontSize: 12 }}>
                        {`Stand vom ${p.datum}`}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <button type="button" onClick={() => fachLeuchten(auswahl.id)}
                style={{ alignSelf: "flex-start", background: "#27272a", border: "none",
                          borderRadius: 6, color: "#fafafa", padding: "6px 10px",
                          cursor: "pointer" }}>
                Fach leuchten
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Statuszeile */}
      {(fehler || meldung) && (
        <div style={{ padding: "6px 16px", borderTop: RAND, fontSize: 13 }}>
          {fehler && <span style={{ color: FEHLERFARBE }}>{fehler}</span>}
          {fehler && meldung && " — "}
          {meldung && <span style={{ color: GEDAEMPFT }}>{meldung}</span>}
        </div>
      )}
    </div>
  );
}
