import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BestandPanel } from "./BestandPanel";

const TEILE = [{ id: 1, bezeichnung: "100nF X7R 0805", menge: 250,
                 klasse: "abblock_c", herstellerNr: "", fach: "A/3" }];
const DETAIL = { ...TEILE[0], eckdaten: "50 V", datenblattUrl: "",
                 alternativen: [],
                 preise: [{ quelle: "LCSC", preisEur: 0.02, url: "", datum: "2026-09-08" }] };

function mockFetch(routen: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn((eingabe: RequestInfo | URL) => {
    const url = String(eingabe);
    const passend = Object.entries(routen).find(([k]) => url.includes(k));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve(passend ? passend[1] : []) } as Response);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("BestandPanel", () => {
  it("zeigt Liste und lädt Detail bei Klick", async () => {
    mockFetch({ "/bestand/teile/1": DETAIL, "/bestand/teile": TEILE,
                "/bestand/klassen": ["abblock_c"] });
    render(<BestandPanel />);

    await screen.findByText(/100nF X7R 0805/);
    await userEvent.click(screen.getByText(/100nF X7R 0805/));

    await waitFor(() =>
      expect(screen.getByText(/Stand vom 2026-09-08/)).toBeInTheDocument());
  });

  it("Formular legt Teil an und meldet", async () => {
    mockFetch({ "/bestand/klassen": [], "/bestand/teile": TEILE });
    render(<BestandPanel />);
    await screen.findByText(/100nF/);

    await userEvent.click(screen.getByText("+ Teil anlegen"));
    expect(screen.getByLabelText("Bezeichnung")).toBeInTheDocument();
    expect(screen.getByLabelText("Fach (Regal/Position)")).toBeInTheDocument();
  });

  it("rendert javascript-URLs nicht als Link", async () => {
    const detail = { ...DETAIL, datenblattUrl: "javascript:alert(1)" };
    mockFetch({ "/bestand/teile/1": detail, "/bestand/teile": TEILE,
                "/bestand/klassen": [] });
    render(<BestandPanel />);
    await screen.findByText(/100nF X7R 0805/);
    await userEvent.click(screen.getByText(/100nF X7R 0805/));

    await waitFor(() =>
      expect(screen.getByText(/javascript:alert\(1\)/)).toBeInTheDocument());
    expect(screen.getByText(/javascript:alert\(1\)/).closest("a")).toBeNull();
  });
});
