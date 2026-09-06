import { useEffect, useState } from "react";
import {
  fetchExportReport,
  fetchKicadStatus,
  guideUrl,
  kicadDownloadUrl,
  openInKicad,
  pcbDownloadUrl,
  startKicadInstall,
  type ExportReport,
  type KicadStatus,
  type MountStyle,
  type OpenResult,
} from "../../api/export";

type Props = {
  projectId: string;
  onClose: () => void;
};

const btnPrimary: React.CSSProperties = {
  background: "#16a34a", color: "#fff", border: "none",
  borderRadius: 8, padding: "6px 14px", fontSize: 12,
  cursor: "pointer", textDecoration: "none",
};
const btnSecondary: React.CSSProperties = {
  background: "#0c0c0f", color: "#e4e4e7", border: "1px solid #27272a",
  borderRadius: 8, padding: "6px 14px", fontSize: 12,
  cursor: "pointer", textDecoration: "none",
};

export function ExportDialog({ projectId, onClose }: Props) {
  const [kicad, setKicad] = useState<KicadStatus | null>(null);
  const [installMsg, setInstallMsg] = useState<string | null>(null);
  const [installCmd, setInstallCmd] = useState<string | null>(null);
  const [mount, setMount] = useState<MountStyle | null>(null);
  const [report, setReport] = useState<ExportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [openResult, setOpenResult] = useState<OpenResult | null>(null);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    fetchKicadStatus().then(setKicad).catch(() => setKicad(null));
  }, []);

  // Nach Installations-Anstoß: Status regelmäßig auffrischen
  useEffect(() => {
    if (!installMsg || kicad?.installed) return;
    const timer = setInterval(() => {
      fetchKicadStatus().then((s) => {
        setKicad(s);
        if (s.installed) setInstallMsg("KiCad ist jetzt installiert.");
      }).catch(() => undefined);
    }, 5000);
    return () => clearInterval(timer);
  }, [installMsg, kicad?.installed]);

  const runExport = (m: MountStyle) => {
    setMount(m);
    setLoading(true);
    setError(null);
    fetchExportReport(projectId, m)
      .then(setReport)
      .catch((err) => setError(String(err?.message ?? err)))
      .finally(() => setLoading(false));
  };

  const doOpen = () => {
    if (!mount) return;
    setOpening(true);
    setOpenResult(null);
    openInKicad(projectId, mount)
      .then(setOpenResult)
      .catch((err) => setError(String(err?.message ?? err)))
      .finally(() => setOpening(false));
  };

  const doInstall = () => {
    startKicadInstall()
      .then((r) => {
        setInstallMsg(r.reason);
        setInstallCmd(r.command ?? null);
      })
      .catch((err) => setInstallMsg(String(err?.message ?? err)));
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 60,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#0c0c0f", border: "1px solid #27272a", borderRadius: 12,
          padding: 20, width: 500, maxHeight: "75vh", overflowY: "auto",
          color: "#e4e4e7", fontSize: 13,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 12 }}>KiCad-Export</div>

        {/* KiCad-Status */}
        {kicad && !kicad.installed && (
          <div
            style={{
              border: "1px solid #7c2d12", background: "#1c0a02",
              borderRadius: 8, padding: 10, marginBottom: 12, fontSize: 12,
            }}
          >
            <div style={{ color: "#fdba74", marginBottom: 6 }}>
              KiCad ist auf diesem Rechner nicht installiert — Export und Öffnen
              brauchen es.
            </div>
            <button onClick={doInstall} style={btnPrimary}>
              KiCad installieren
            </button>
            {installMsg && (
              <div style={{ marginTop: 8, color: "#a1a1aa" }}>{installMsg}</div>
            )}
            {installCmd && (
              <code
                style={{
                  display: "block", marginTop: 6, padding: 6,
                  background: "#18181b", borderRadius: 6, fontSize: 11,
                  userSelect: "all",
                }}
              >
                {installCmd}
              </code>
            )}
          </div>
        )}
        {kicad?.installed && kicad.version && (
          <div style={{ fontSize: 11, color: "#52525b", marginBottom: 10 }}>
            KiCad {kicad.version} gefunden
          </div>
        )}

        {/* Schritt 1: Bestückungsfrage */}
        {!report && !error && (
          <>
            <div style={{ marginBottom: 12, color: "#a1a1aa", fontSize: 12 }}>
              Wie soll bestückt werden? Das bestimmt die automatische
              Footprint-Zuordnung der Bauteile.
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => runExport("smd")} disabled={loading} style={btnPrimary}>
                SMD (Oberflächenmontage){loading && mount === "smd" ? "…" : ""}
              </button>
              <button onClick={() => runExport("tht")} disabled={loading} style={btnSecondary}>
                THT (bedrahtet / Handlöten){loading && mount === "tht" ? "…" : ""}
              </button>
            </div>
          </>
        )}

        {error && <div style={{ color: "#f87171", marginTop: 8 }}>{error}</div>}

        {/* Schritt 2: Report + Aktionen */}
        {report && mount && (
          <>
            <div style={{ display: "flex", gap: 12, margin: "4px 0 12px", fontSize: 12, flexWrap: "wrap" }}>
              <span style={{ color: "#86efac" }}>{report.counts.mapped} gemappt</span>
              <span style={{ color: "#a1a1aa" }}>{report.counts.fallback} Standard</span>
              <span style={{ color: "#fbbf24" }}>{report.counts.unverified} unbestätigt</span>
              <span style={{ color: "#f87171" }}>{report.counts.unmapped} ohne Symbol</span>
              <span style={{ color: "#a1a1aa" }}>{report.counts.no_footprint} ohne Footprint</span>
            </div>
            {report.unmapped.length > 0 && (
              <div style={{ marginBottom: 10 }}>
                <div style={{ color: "#f87171", fontSize: 12, marginBottom: 4 }}>
                  Nicht exportierbar (kein Bibliothekseintrag):
                </div>
                {report.unmapped.map((u, i) => (
                  <div key={i} style={{ fontSize: 12, color: "#a1a1aa" }}>
                    · {u.name ?? u.mpn ?? "?"} ({u.block_name})
                  </div>
                ))}
              </div>
            )}
            {report.warnings.length > 0 && (
              <details style={{ marginBottom: 10 }}>
                <summary style={{ cursor: "pointer", fontSize: 12, color: "#fbbf24" }}>
                  {report.warnings.length} Hinweise
                </summary>
                {report.warnings.map((w, i) => (
                  <div key={i} style={{ fontSize: 11, color: "#a1a1aa", marginTop: 4 }}>
                    · {w}
                  </div>
                ))}
              </details>
            )}

            <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
              <button onClick={doOpen} disabled={opening} style={btnPrimary}>
                {opening ? "Öffne…" : "In KiCad öffnen"}
              </button>
              <a href={kicadDownloadUrl(projectId, mount)} download style={btnSecondary}>
                Schaltplan speichern
              </a>
              <a href={pcbDownloadUrl(projectId, mount)} download style={btnSecondary}>
                Platine speichern
              </a>
              <a href={guideUrl(projectId, mount)} target="_blank" rel="noreferrer" style={btnSecondary}>
                Routing-Anleitung
              </a>
              <button onClick={onClose} style={btnSecondary}>Schließen</button>
            </div>

            {openResult && (
              <div
                style={{
                  marginTop: 12, padding: 10, borderRadius: 8, fontSize: 12,
                  border: "1px solid #27272a", color: "#a1a1aa",
                }}
              >
                {openResult.opened
                  ? "KiCad wurde gestartet."
                  : openResult.reason ?? "Dateien gespeichert."}
                <div style={{ marginTop: 4 }}>
                  Projektordner: <code style={{ userSelect: "all" }}>{openResult.path}</code>
                </div>
                {openResult.pcbNote && (
                  <div style={{ marginTop: 4, color: "#fbbf24" }}>{openResult.pcbNote}</div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
