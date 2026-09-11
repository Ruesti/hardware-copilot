import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProjektePanel } from "./ProjektePanel";

const PROJEKTE = [{ id: 1, name: "Blink-Board", status: "offen", positionen: 2, fehlen: 1 }];

const POSITION_DA = {
  id: 1, referenz: "C1", bezeichnung: "100nF X7R 0805", menge: 4, klasse: "abblock_c",
  baugruppe: "Netzteil", teilId: 5, pins: null, kicadSymbol: "", kicadFootprint: "",
  notiz: "", bestand: { menge: 250, fach: "A/3" }, status: "da",
  preis: { preisEur: 0.02, quelle: "LCSC", datum: "2026-09-08", url: "" }, allePreise: [],
};

const POSITION_UNASSIGNED = {
  id: 2, referenz: "R1", bezeichnung: "10k 0603", menge: 2, klasse: "widerstand",
  baugruppe: "", teilId: null, pins: null, kicadSymbol: "", kicadFootprint: "",
  notiz: "", bestand: null, status: "nicht_zugeordnet", preis: null, allePreise: [],
};

const PROJEKT_DETAIL = {
  id: 1, name: "Blink-Board", beschreibung: "Test-Board", status: "offen",
  angelegtAm: "2026-09-01",
  positionen: [POSITION_DA, POSITION_UNASSIGNED],
  zusammenfassung: { positionen: 2, gedeckt: 1, fehlen: 1, fehlteileKostenEur: 0.5, ohnePreis: 0 },
};

const KICAD_ERGEBNIS = {
  ordner: "/exporte/blink-board",
  schaltplan: "/exporte/blink-board/blink-board.kicad_sch",
  pcb: "/exporte/blink-board/blink-board.kicad_pcb",
  anleitung: "/exporte/blink-board/anleitung.html",
  report: {
    uebernommen: 1,
    uebersprungen: [{ referenz: "R7", bezeichnung: "10k 0603", grund: "kein KiCad-Symbol hinterlegt" }],
    warnungen: ["PCB enthält unbestückte Positionen."],
    pcbHinweis: "Bauteile sind unverbunden platziert — bitte in KiCad routen.",
  },
};

function mockFetch(routen: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn((eingabe: RequestInfo | URL) => {
    const url = String(eingabe);
    const passend = Object.entries(routen).find(([k]) => url.includes(k));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve(passend ? passend[1] : []) } as Response);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("ProjektePanel", () => {
  it("zeigt Liste und lädt Detail bei Klick — Zusammenfassung, Status-Badge, Gruppenkopf", async () => {
    mockFetch({ "/projekte/1": PROJEKT_DETAIL, "/projekte": PROJEKTE });
    render(<ProjektePanel />);

    await screen.findByText(/\[P-1\] Blink-Board/);
    await userEvent.click(screen.getByText(/\[P-1\] Blink-Board/));

    await waitFor(() =>
      expect(screen.getByText(/1 von 2 Positionen im Bestand/)).toBeInTheDocument());
    expect(screen.getByText(/Fehlteile ≈/)).toBeInTheDocument();
    expect(screen.getByText("da")).toBeInTheDocument();
    expect(screen.getByText("Netzteil")).toBeInTheDocument();
    expect(screen.getByText("Sonstiges")).toBeInTheDocument();
  });

  it("Zeile mit teilId null zeigt Zuordnen, Zeile mit Status da zeigt es nicht", async () => {
    mockFetch({ "/projekte/1": PROJEKT_DETAIL, "/projekte": PROJEKTE });
    render(<ProjektePanel />);

    await screen.findByText(/\[P-1\] Blink-Board/);
    await userEvent.click(screen.getByText(/\[P-1\] Blink-Board/));

    await waitFor(() => expect(screen.getByText("Zuordnen")).toBeInTheDocument());
    expect(screen.getAllByText("Zuordnen")).toHaveLength(1);
    expect(screen.getByText("Fach leuchten")).toBeInTheDocument();
  });

  it("KiCad-Export ruft kicadExport und rendert die Report-Box mit R7 und Grund", async () => {
    mockFetch({
      "/projekte/1/kicad-export": KICAD_ERGEBNIS,
      "/projekte/1": PROJEKT_DETAIL,
      "/projekte": PROJEKTE,
    });
    render(<ProjektePanel />);

    await screen.findByText(/\[P-1\] Blink-Board/);
    await userEvent.click(screen.getByText(/\[P-1\] Blink-Board/));

    await waitFor(() => expect(screen.getByText("KiCad-Export")).toBeInTheDocument());
    await userEvent.click(screen.getByText("KiCad-Export"));

    await waitFor(() => expect(screen.getByText(/✓ 1 Symbole/)).toBeInTheDocument());
    expect(screen.getByText(/R7/)).toBeInTheDocument();
    expect(screen.getByText(/kein KiCad-Symbol hinterlegt/)).toBeInTheDocument();
  });

  it("„Anleitung ansehen“ ruft window.open mit anleitungUrl(id)", async () => {
    mockFetch({
      "/projekte/1/kicad-export": KICAD_ERGEBNIS,
      "/projekte/1": PROJEKT_DETAIL,
      "/projekte": PROJEKTE,
    });
    const oeffnenSpion = vi.spyOn(window, "open").mockImplementation(() => null);
    render(<ProjektePanel />);

    await screen.findByText(/\[P-1\] Blink-Board/);
    await userEvent.click(screen.getByText(/\[P-1\] Blink-Board/));

    await waitFor(() => expect(screen.getByText("KiCad-Export")).toBeInTheDocument());
    await userEvent.click(screen.getByText("KiCad-Export"));

    await waitFor(() => expect(screen.getByText("Anleitung ansehen")).toBeInTheDocument());
    await userEvent.click(screen.getByText("Anleitung ansehen"));

    expect(oeffnenSpion).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/projekte/1/kicad-anleitung", "_blank");
    oeffnenSpion.mockRestore();
  });
});
