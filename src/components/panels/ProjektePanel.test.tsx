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
});
