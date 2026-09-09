import { useCallback, useEffect, useState } from "react";
import { fetchBloecke, fetchBlock, fetchLuecken, fetchRegel, fetchRegeln,
         fetchWissenKlassen } from "../../api/wissen";
import type { BlockKurz, BlockVoll, LueckeEintrag, RegelKurz, RegelVoll } from "../../types/wissen";
import { istWebUrl } from "./urlSchema";

const RAND = "1px solid #18181b";
const GEDAEMPFT = "#a1a1aa";
const FEHLERFARBE = "#f87171";

const STUFEN_FARBEN: Record<string, string> = {
  vermutung: "#facc15",
  belegt: "#4ade80",
  verifiziert: "#60a5fa",
};

type SubTab = "regeln" | "blocks" | "luecken";

const SUB_TABS: { id: SubTab; label: string }[] = [
  { id: "regeln", label: "Regeln" },
  { id: "blocks", label: "Verified Blocks" },
  { id: "luecken", label: "Lücken" },
];

function Stufe({ stufe }: { stufe: string }) {
  const farbe = STUFEN_FARBEN[stufe] ?? GEDAEMPFT;
  return (
    <span style={{ color: farbe, fontSize: 12, fontWeight: "bold" }}>
      {stufe === "vermutung" ? "⚠ VERMUTUNG" : stufe}
    </span>
  );
}

export function WissensPanel() {
  const [subTab, setSubTab] = useState<SubTab>("regeln");
  const [fehler, setFehler] = useState("");

  // Regeln
  const [regeln, setRegeln] = useState<RegelKurz[]>([]);
  const [klassen, setKlassen] = useState<string[]>([]);
  const [klasse, setKlasse] = useState("");
  const [stufeFilter, setStufeFilter] = useState("");
  const [regelAuswahl, setRegelAuswahl] = useState<RegelVoll | null>(null);

  // Blocks
  const [bloecke, setBloecke] = useState<BlockKurz[]>([]);
  const [blockAuswahl, setBlockAuswahl] = useState<BlockVoll | null>(null);

  // Lücken
  const [luecken, setLuecken] = useState<LueckeEintrag[]>([]);

  const regelnLaden = useCallback(() => {
    fetchRegeln(klasse, stufeFilter)
      .then((r) => { setRegeln(r); setFehler(""); })
      .catch((e) => setFehler(e.message));
  }, [klasse, stufeFilter]);

  useEffect(() => {
    if (subTab === "regeln") regelnLaden();
  }, [subTab, regelnLaden]);

  useEffect(() => {
    fetchWissenKlassen().then(setKlassen).catch((e) => setFehler(e.message));
  }, []);

  const bloeckeLaden = useCallback(() => {
    fetchBloecke()
      .then((b) => { setBloecke(b); setFehler(""); })
      .catch((e) => setFehler(e.message));
  }, []);

  useEffect(() => {
    if (subTab === "blocks") bloeckeLaden();
  }, [subTab, bloeckeLaden]);

  const lueckenLaden = useCallback(() => {
    fetchLuecken()
      .then((l) => { setLuecken(l); setFehler(""); })
      .catch((e) => setFehler(e.message));
  }, []);

  useEffect(() => {
    if (subTab === "luecken") lueckenLaden();
  }, [subTab, lueckenLaden]);

  // Live-Spiegel: ChatPanel feuert dieses Event nach jedem abgeschlossenen
  // mcp__wissensschicht-Werkzeugaufruf (siehe ChatPanel.tsx). Lädt nur die
  // Daten des gerade aktiven Sub-Tabs neu, um unnötige Requests zu sparen.
  useEffect(() => {
    const neuLaden = () => {
      if (subTab === "regeln") regelnLaden();
      else if (subTab === "blocks") bloeckeLaden();
      else if (subTab === "luecken") lueckenLaden();
    };
    window.addEventListener("wissen-geaendert", neuLaden);
    return () => window.removeEventListener("wissen-geaendert", neuLaden);
  }, [subTab, regelnLaden, bloeckeLaden, lueckenLaden]);

  const regelLaden = (id: string) =>
    fetchRegel(id)
      .then((r) => { setRegelAuswahl(r); setFehler(""); })
      .catch((e) => setFehler(e.message));

  const blockLaden = (id: string) =>
    fetchBlock(id)
      .then((b) => { setBlockAuswahl(b); setFehler(""); })
      .catch((e) => setFehler(e.message));

  const wechsleTab = (t: SubTab) => {
    setSubTab(t);
    setRegelAuswahl(null);
    setBlockAuswahl(null);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <nav style={{ display: "flex", gap: 4, padding: 12, borderBottom: RAND }}>
        {SUB_TABS.map((t) => (
          <button key={t.id} type="button" onClick={() => wechsleTab(t.id)}
            style={{ padding: "6px 14px", borderRadius: 6, border: "none",
                     cursor: "pointer",
                     background: subTab === t.id ? "#27272a" : "transparent",
                     color: subTab === t.id ? "#fafafa" : GEDAEMPFT }}>
            {t.label}
          </button>
        ))}
      </nav>

      {subTab === "regeln" && (
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          <div style={{ width: 360, display: "flex", flexDirection: "column",
                         borderRight: RAND, minHeight: 0 }}>
            <div style={{ display: "flex", gap: 8, padding: 12, borderBottom: RAND }}>
              <select
                value={klasse}
                onChange={(e) => setKlasse(e.target.value)}
                style={{ flex: 1, background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }}
              >
                <option value="">alle Klassen</option>
                {klassen.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
              <select
                value={stufeFilter}
                onChange={(e) => setStufeFilter(e.target.value)}
                style={{ flex: 1, background: "#18181b", border: RAND, borderRadius: 6,
                          color: "#e4e4e7", padding: "6px 8px" }}
              >
                <option value="">alle Stufen</option>
                <option value="belegt">belegt</option>
                <option value="verifiziert">verifiziert</option>
                <option value="vermutung">vermutung</option>
              </select>
            </div>

            <div style={{ overflowY: "auto", flex: 1 }}>
              {regeln.map((r) => (
                <div key={r.id}
                  onClick={() => regelLaden(r.id)}
                  style={{ padding: "8px 12px", borderBottom: RAND, cursor: "pointer",
                            background: regelAuswahl?.id === r.id ? "#18181b" : "transparent" }}>
                  <div>{`[${r.id}] ${r.aussage}`}</div>
                  <div style={{ marginTop: 4 }}><Stufe stufe={r.stufe} /></div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16 }}>
            {!regelAuswahl ? (
              <div style={{ color: GEDAEMPFT }}>Keine Regel ausgewählt.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <h2 style={{ margin: 0 }}>{`[${regelAuswahl.id}] ${regelAuswahl.aussage}`}</h2>
                <div><Stufe stufe={regelAuswahl.stufe} /></div>

                <div>{`Begründung: ${regelAuswahl.begruendung}`}</div>
                <div>{`Stärke: ${regelAuswahl.staerke}`}</div>

                <div>
                  <div style={{ fontWeight: "bold", marginBottom: 4 }}>Quelle</div>
                  {regelAuswahl.quelle.typ === "keine" || !regelAuswahl.quelle.typ ? (
                    <div style={{ color: GEDAEMPFT }}>Quelle: keine (Herleitung)</div>
                  ) : (
                    <div>
                      <div>
                        {`Quelle: ${regelAuswahl.quelle.titel}`}
                        {regelAuswahl.quelle.dokument && ` (${regelAuswahl.quelle.dokument})`}
                      </div>
                      <div>{`Fundstelle: ${regelAuswahl.quelle.fundstelle || "—"}`}</div>
                      {regelAuswahl.quelle.url && (
                        <div>
                          Quelle-URL:{" "}
                          {istWebUrl(regelAuswahl.quelle.url)
                            ? <a href={regelAuswahl.quelle.url} target="_blank" rel="noreferrer"
                                 style={{ color: "#e4e4e7" }}>{regelAuswahl.quelle.url}</a>
                            : <span>{regelAuswahl.quelle.url}</span>}
                        </div>
                      )}
                      {regelAuswahl.quelle.zitat && (
                        <blockquote style={{ margin: "4px 0", padding: "4px 12px",
                                              borderLeft: "3px solid #27272a",
                                              color: GEDAEMPFT }}>
                          {regelAuswahl.quelle.zitat}
                        </blockquote>
                      )}
                    </div>
                  )}
                </div>

                <div>
                  <div style={{ fontWeight: "bold", marginBottom: 4 }}>Geltung</div>
                  <div>{Object.entries(regelAuswahl.geltung)
                    .map(([k, v]) => `${k}: ${v}`).join(", ") || "—"}</div>
                </div>

                <div>
                  <div style={{ fontWeight: "bold", marginBottom: 4 }}>Ausnahmen</div>
                  {regelAuswahl.ausnahmen.length === 0 ? (
                    <div style={{ color: GEDAEMPFT }}>— keine</div>
                  ) : (
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {regelAuswahl.ausnahmen.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {subTab === "blocks" && (
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          <div style={{ width: 360, overflowY: "auto", borderRight: RAND }}>
            {bloecke.map((b) => (
              <div key={b.id}
                onClick={() => blockLaden(b.id)}
                style={{ padding: "8px 12px", borderBottom: RAND, cursor: "pointer",
                          background: blockAuswahl?.id === b.id ? "#18181b" : "transparent" }}>
                <div>{`[${b.id}] ${b.titel}`}</div>
                <div style={{ color: GEDAEMPFT, fontSize: 12, marginTop: 4 }}>
                  {`${b.kernbauteil} · ${b.topologie}`}
                </div>
              </div>
            ))}
          </div>

          <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16 }}>
            {!blockAuswahl ? (
              <div style={{ color: GEDAEMPFT }}>Kein Block ausgewählt.</div>
            ) : (
              <div>
                <h2 style={{ margin: "0 0 12px" }}>{`[${blockAuswahl.id}] ${blockAuswahl.titel}`}</h2>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit",
                               margin: 0 }}>
                  {blockAuswahl.volltext}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {subTab === "luecken" && (
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: 16 }}>
          {luecken.length === 0 ? (
            <div style={{ color: GEDAEMPFT }}>— keine Lücken erfasst</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: RAND, padding: "6px 8px" }}>Datum</th>
                  <th style={{ textAlign: "left", borderBottom: RAND, padding: "6px 8px" }}>Frage</th>
                  <th style={{ textAlign: "left", borderBottom: RAND, padding: "6px 8px" }}>Grund</th>
                  <th style={{ textAlign: "left", borderBottom: RAND, padding: "6px 8px" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {luecken.map((l, i) => (
                  <tr key={i}>
                    <td style={{ borderBottom: RAND, padding: "6px 8px" }}>{l.datum}</td>
                    <td style={{ borderBottom: RAND, padding: "6px 8px" }}>{l.frage}</td>
                    <td style={{ borderBottom: RAND, padding: "6px 8px" }}>{l.grund}</td>
                    <td style={{ borderBottom: RAND, padding: "6px 8px" }}>{l.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {fehler && (
        <div style={{ padding: "6px 16px", borderTop: RAND, fontSize: 13 }}>
          <span style={{ color: FEHLERFARBE }}>{fehler}</span>
        </div>
      )}
    </div>
  );
}
