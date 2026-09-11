import { Fragment, useCallback, useEffect, useState } from "react";
import { fetchTeile, leuchten } from "../../api/bestand";
import { anleitungUrl, createProjekt, fetchProjekt, fetchProjekte, kicadExport,
         kicadOeffnen, positionZuordnen, projektAbbuchen } from "../../api/projekte";
import type { TeilKurz } from "../../types/bestand";
import type { KicadExportErgebnis, PositionZeile, ProjektDetail,
              ProjektKurz } from "../../types/projekte";

const RAND = "1px solid #18181b";
const GEDAEMPFT = "#a1a1aa";
const FEHLERFARBE = "#f87171";
const ERFOLGSFARBE = "#4ade80";
const WARNFARBE = "#facc15";

const FELD_STIL = { background: "#18181b", border: RAND, borderRadius: 6,
                     color: "#e4e4e7", padding: "6px 8px" };
const KNOPF_STIL = { background: "#27272a", border: "none", borderRadius: 6,
                      color: "#fafafa", padding: "6px 10px", cursor: "pointer" };
const KNOPF_STIL_LEISE = { background: "transparent", border: RAND, borderRadius: 6,
                            color: GEDAEMPFT, padding: "6px 10px", cursor: "pointer" };
const KNOPF_KLEIN = { ...KNOPF_STIL, padding: "2px 8px", fontSize: 12 };

const STATUS_TEXT: Record<PositionZeile["status"], string> = {
  da: "da", knapp: "knapp", fehlt: "fehlt", nicht_zugeordnet: "nicht zugeordnet",
};
const STATUS_FARBE: Record<PositionZeile["status"], string> = {
  da: "#4ade80", knapp: "#facc15", fehlt: "#f87171", nicht_zugeordnet: "#facc15",
};

const euro = (n: number) =>
  n.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const bestandZelle = (pos: PositionZeile) => {
  if (!pos.bestand) return "—";
  return pos.bestand.fach ? `${pos.bestand.menge} · Fach ${pos.bestand.fach}` : `${pos.bestand.menge}`;
};

const preisZelle = (pos: PositionZeile) =>
  pos.preis
    ? `${euro(pos.preis.preisEur)} € · ${pos.preis.quelle} (Stand ${pos.preis.datum})`
    : "—";

/** Gruppiert Positionen nach Baugruppe (leer → „Sonstiges") und sortiert die Gruppen alphabetisch. */
function gruppiere(positionen: PositionZeile[]): [string, PositionZeile[]][] {
  const map = new Map<string, PositionZeile[]>();
  for (const p of positionen) {
    const gruppe = p.baugruppe.trim() || "Sonstiges";
    const liste = map.get(gruppe);
    if (liste) liste.push(p); else map.set(gruppe, [p]);
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b, "de"));
}

export function ProjektePanel() {
  const [projekte, setProjekte] = useState<ProjektKurz[]>([]);
  const [auswahl, setAuswahl] = useState<ProjektDetail | null>(null);
  const [meldung, setMeldung] = useState("");
  const [fehler, setFehler] = useState("");
  const [formularOffen, setFormularOffen] = useState(false);
  const [name, setName] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [teile, setTeile] = useState<TeilKurz[]>([]);
  const [zuordnenOffenId, setZuordnenOffenId] = useState<number | null>(null);
  const [zuordnenWert, setZuordnenWert] = useState("");
  const [aufgeklappt, setAufgeklappt] = useState<Record<number, boolean>>({});
  const [kicadLaeuft, setKicadLaeuft] = useState(false);
  const [kicadErgebnis, setKicadErgebnis] = useState<KicadExportErgebnis | null>(null);

  const laden = useCallback(() => {
    fetchProjekte()
      .then((p) => { setProjekte(p); setFehler(""); })
      .catch((e) => setFehler(e.message));
  }, []);

  const detailLaden = useCallback((id: number) =>
    fetchProjekt(id)
      .then((p) => { setAuswahl(p); setFehler(""); })
      .catch((e) => setFehler(e.message)),
  []);

  useEffect(() => { laden(); }, [laden]);

  // Live-Spiegel: ChatPanel meldet Projekt/Positions-Änderungen aus Werkzeugaufrufen.
  const auswahlId = auswahl?.id;
  useEffect(() => {
    const h = () => {
      laden();
      if (auswahlId != null) detailLaden(auswahlId);
    };
    window.addEventListener("projekt-geaendert", h);
    return () => window.removeEventListener("projekt-geaendert", h);
  }, [laden, detailLaden, auswahlId]);

  // Projektwechsel: vorheriger KiCad-Report gehört zum alten Projekt, nicht zum neuen.
  useEffect(() => { setKicadErgebnis(null); }, [auswahlId]);

  const anlegen = (ev: React.FormEvent) => {
    ev.preventDefault();
    createProjekt(name, beschreibung || undefined)
      .then((r) => {
        setMeldung(r.meldung);
        setFehler("");
        setFormularOffen(false);
        setName("");
        setBeschreibung("");
        laden();
      })
      .catch((e) => setFehler(e.message));
  };

  const abbuchen = () => {
    if (!auswahl) return;
    if (!window.confirm(`„${auswahl.name}“ wirklich als gebaut abbuchen?`)) return;
    projektAbbuchen(auswahl.id)
      .then((r) => {
        setMeldung(r.meldung);
        setFehler("");
        laden();
        detailLaden(auswahl.id);
      })
      .catch((e) => setFehler(e.message));
  };

  const fachLeuchten = (teilId: number) =>
    leuchten(teilId)
      .then((r) => { setMeldung(r.meldung); setFehler(""); })
      .catch((e) => setFehler(e.message));

  const zuordnenOeffnen = (posId: number) => {
    setZuordnenOffenId(posId);
    setZuordnenWert("");
    if (teile.length === 0) {
      fetchTeile().then(setTeile).catch((e) => setFehler(e.message));
    }
  };

  const zuordnenBestaetigen = (pos: PositionZeile) => {
    if (!auswahl || !zuordnenWert) return;
    positionZuordnen(auswahl.id, pos.referenz, Number(zuordnenWert))
      .then((r) => {
        setMeldung(r.meldung);
        setFehler("");
        setZuordnenOffenId(null);
        laden();
        detailLaden(auswahl.id);
      })
      .catch((e) => setFehler(e.message));
  };

  const preisUmschalten = (posId: number) =>
    setAufgeklappt((p) => ({ ...p, [posId]: !p[posId] }));

  const kicadExportStarten = () => {
    if (!auswahl) return;
    setKicadLaeuft(true);
    kicadExport(auswahl.id)
      .then((r) => { setKicadErgebnis(r); setFehler(""); })
      .catch((e) => setFehler(e.message))
      .finally(() => setKicadLaeuft(false));
  };

  const kicadAnleitungAnsehen = () => {
    if (!auswahl) return;
    window.open(anleitungUrl(auswahl.id), "_blank");
  };

  const kicadInOeffnen = () => {
    if (!auswahl) return;
    kicadOeffnen(auswahl.id)
      .then((r) => { setMeldung(r.meldung); setFehler(""); })
      .catch((e) => setFehler(e.message));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* Liste links */}
        <div style={{ width: 360, display: "flex", flexDirection: "column",
                       borderRight: RAND, minHeight: 0 }}>
          <div style={{ padding: 12, borderBottom: RAND }}>
            <button type="button" onClick={() => setFormularOffen((o) => !o)} style={KNOPF_STIL}>
              + Projekt anlegen
            </button>
          </div>

          {formularOffen && (
            <form onSubmit={anlegen}
              style={{ display: "flex", flexDirection: "column", gap: 8,
                        padding: 12, borderBottom: RAND }}>
              <label htmlFor="projekt-name">Name</label>
              <input id="projekt-name" required value={name}
                onChange={(e) => setName(e.target.value)} style={FELD_STIL} />

              <label htmlFor="projekt-beschreibung">Beschreibung</label>
              <input id="projekt-beschreibung" value={beschreibung}
                onChange={(e) => setBeschreibung(e.target.value)} style={FELD_STIL} />

              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" style={KNOPF_STIL}>Anlegen</button>
                <button type="button" onClick={() => setFormularOffen(false)}
                  style={KNOPF_STIL_LEISE}>
                  Abbrechen
                </button>
              </div>
            </form>
          )}

          <div style={{ overflowY: "auto", flex: 1 }}>
            {projekte.map((p) => (
              <div key={p.id}
                onClick={() => detailLaden(p.id)}
                style={{ padding: "8px 12px", borderBottom: RAND, cursor: "pointer",
                          background: auswahl?.id === p.id ? "#18181b" : "transparent" }}>
                <div>{`[P-${p.id}] ${p.name}`}</div>
                <div style={{ color: GEDAEMPFT, fontSize: 12, marginTop: 4 }}>
                  {`${p.status} · ${p.positionen} Positionen · `}
                  <span style={{ color: p.fehlen > 0 ? FEHLERFARBE : GEDAEMPFT }}>
                    {`${p.fehlen} fehlen`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail rechts */}
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16 }}>
          {!auswahl ? (
            <div style={{ color: GEDAEMPFT }}>Kein Projekt ausgewählt.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                             alignItems: "flex-start" }}>
                <div>
                  <h2 style={{ margin: 0 }}>
                    {`[P-${auswahl.id}] ${auswahl.name} — ${auswahl.status}`}
                  </h2>
                  <div style={{ color: GEDAEMPFT, marginTop: 4 }}>
                    {auswahl.beschreibung || "—"}
                  </div>
                </div>
                {auswahl.status === "offen" && (
                  <button type="button" onClick={abbuchen} style={KNOPF_STIL}>
                    Als gebaut abbuchen
                  </button>
                )}
              </div>

              <div>
                {`${auswahl.zusammenfassung.gedeckt} von ${auswahl.zusammenfassung.positionen} `}
                {`Positionen im Bestand · Fehlteile ≈ ${euro(auswahl.zusammenfassung.fehlteileKostenEur)} €`}
                {auswahl.zusammenfassung.ohnePreis > 0 &&
                  ` · ${auswahl.zusammenfassung.ohnePreis} ohne Preis`}
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: GEDAEMPFT, borderBottom: RAND }}>
                    <th style={{ padding: "4px 6px" }}>Referenz</th>
                    <th style={{ padding: "4px 6px" }}>Bezeichnung</th>
                    <th style={{ padding: "4px 6px" }}>benötigt</th>
                    <th style={{ padding: "4px 6px" }}>Bestand</th>
                    <th style={{ padding: "4px 6px" }}>Status</th>
                    <th style={{ padding: "4px 6px" }}>Preis</th>
                    <th style={{ padding: "4px 6px" }}>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {gruppiere(auswahl.positionen).map(([gruppe, zeilen]) => (
                    <Fragment key={gruppe}>
                      <tr>
                        <td colSpan={7} style={{ padding: "8px 6px 2px", color: GEDAEMPFT }}>
                          {gruppe}
                        </td>
                      </tr>
                      {zeilen.map((pos) => (
                        <Fragment key={pos.id}>
                          <tr style={{ borderBottom: RAND }}>
                            <td style={{ padding: "4px 6px", fontFamily: "monospace" }}>
                              {pos.referenz}
                            </td>
                            <td style={{ padding: "4px 6px" }}>{pos.bezeichnung}</td>
                            <td style={{ padding: "4px 6px" }}>{pos.menge}</td>
                            <td style={{ padding: "4px 6px" }}>{bestandZelle(pos)}</td>
                            <td style={{ padding: "4px 6px" }}>
                              <span style={{ color: STATUS_FARBE[pos.status],
                                             opacity: pos.status === "nicht_zugeordnet" ? 0.7 : 1 }}>
                                {STATUS_TEXT[pos.status]}
                              </span>
                            </td>
                            <td style={{ padding: "4px 6px",
                                         cursor: pos.allePreise.length > 0 ? "pointer" : "default" }}
                                onClick={() => pos.allePreise.length > 0 && preisUmschalten(pos.id)}>
                              {preisZelle(pos)}
                            </td>
                            <td style={{ padding: "4px 6px" }}>
                              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                                {pos.bestand?.fach && pos.teilId !== null && (
                                  <button type="button" style={KNOPF_KLEIN}
                                    onClick={() => fachLeuchten(pos.teilId as number)}>
                                    Fach leuchten
                                  </button>
                                )}
                                {pos.teilId === null && (
                                  zuordnenOffenId === pos.id ? (
                                    <span style={{ display: "flex", gap: 4, alignItems: "center" }}>
                                      <select value={zuordnenWert}
                                        onChange={(e) => setZuordnenWert(e.target.value)}
                                        style={{ ...FELD_STIL, padding: "2px 4px" }}>
                                        <option value="">Teil wählen…</option>
                                        {teile.map((t) => (
                                          <option key={t.id} value={t.id}>
                                            {`[T-${t.id}] ${t.bezeichnung}`}
                                          </option>
                                        ))}
                                      </select>
                                      <button type="button" style={KNOPF_KLEIN}
                                        onClick={() => zuordnenBestaetigen(pos)}>
                                        Bestätigen
                                      </button>
                                    </span>
                                  ) : (
                                    <button type="button" style={KNOPF_KLEIN}
                                      onClick={() => zuordnenOeffnen(pos.id)}>
                                      Zuordnen
                                    </button>
                                  )
                                )}
                              </div>
                            </td>
                          </tr>
                          {aufgeklappt[pos.id] && pos.allePreise.length > 0 && (
                            <tr>
                              <td colSpan={7} style={{ padding: "2px 6px 8px" }}>
                                {pos.allePreise.map((preis, i) => (
                                  <div key={i} style={{ color: GEDAEMPFT, fontSize: 12 }}>
                                    {`${preis.quelle}: ${euro(preis.preisEur)} € — Stand vom ${preis.datum}`}
                                  </div>
                                ))}
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>

              {auswahl.positionen.length > 0 && (
                <div>
                  <h3 style={{ margin: "0 0 8px" }}>KiCad</h3>
                  <button type="button" onClick={kicadExportStarten} disabled={kicadLaeuft}
                    style={KNOPF_STIL}>
                    {kicadLaeuft ? "exportiere …" : "KiCad-Export"}
                  </button>

                  {kicadErgebnis && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 8 }}>
                      <div style={{ color: ERFOLGSFARBE }}>
                        {`✓ ${kicadErgebnis.report.uebernommen} Symbole`}
                      </div>
                      {kicadErgebnis.report.uebersprungen.map((u) => (
                        <div key={u.referenz} style={{ color: WARNFARBE }}>
                          {`⚠ ${u.referenz} — ${u.grund}`}
                        </div>
                      ))}
                      {kicadErgebnis.report.warnungen.map((w, i) => (
                        <div key={i} style={{ color: GEDAEMPFT }}>{w}</div>
                      ))}
                      {kicadErgebnis.report.pcbHinweis && (
                        <div style={{ color: GEDAEMPFT }}>{kicadErgebnis.report.pcbHinweis}</div>
                      )}
                      <div style={{ fontFamily: "monospace", color: GEDAEMPFT }}>
                        {kicadErgebnis.ordner}
                      </div>
                      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                        <button type="button" onClick={kicadAnleitungAnsehen}
                          style={KNOPF_STIL_LEISE}>
                          Anleitung ansehen
                        </button>
                        <button type="button" onClick={kicadInOeffnen} style={KNOPF_STIL_LEISE}>
                          In KiCad öffnen
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
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
