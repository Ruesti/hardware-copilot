import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { WissensPanel } from "./WissensPanel";

const REGELN = [
  { id: "R-005", bereich: "schaltregler", aussage: "Hot Loop klein halten.",
    staerke: "muss", stufe: "belegt", klasse: "schaltregler" },
  { id: "R-008", bereich: "schaltregler", aussage: "FB-Massefuß eigener Weg.",
    staerke: "sollte", stufe: "vermutung", klasse: "schaltregler" },
];
const VOLL = { id: "R-008", bereich: "schaltregler", aussage: "FB-Massefuß eigener Weg.",
  begruendung: "Störarme Referenz.", staerke: "sollte", stufe: "vermutung",
  datum_eintrag: "2026-09-08", datum_geprueft: "2026-09-08", ausnahmen: [],
  quelle: { typ: "keine", titel: "", dokument: "", fundstelle: "", url: "", zitat: "" },
  geltung: { klasse: "schaltregler" } };
const VOLL_MIT_QUELLE = { id: "R-005", bereich: "schaltregler", aussage: "Hot Loop klein halten.",
  begruendung: "Kurze Wege reduzieren Störungen.", staerke: "muss", stufe: "belegt",
  datum_eintrag: "2026-09-08", datum_geprueft: "2026-09-08", ausnahmen: [],
  quelle: { typ: "datenblatt", titel: "TB", dokument: "D1", fundstelle: "S. 1",
            url: "https://example.com/x.pdf", zitat: "Z" },
  geltung: { klasse: "schaltregler" } };

function mockFetch(routen: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn((eingabe: RequestInfo | URL) => {
    const url = String(eingabe);
    const passend = Object.entries(routen).find(([k]) => url.includes(k));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve(passend ? passend[1] : []) } as Response);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("WissensPanel", () => {
  it("zeigt Regeln mit Stufen und ⚠-Marker im Volltext", async () => {
    mockFetch({ "/wissen/regeln/R-008": VOLL, "/wissen/regeln": REGELN,
                "/wissen/klassen": ["schaltregler"] });
    render(<WissensPanel />);

    await screen.findByText(/Hot Loop klein halten/);
    await userEvent.click(screen.getByText(/FB-Massefuß eigener Weg/));

    await waitFor(() =>
      expect(screen.getAllByText(/⚠ VERMUTUNG/).length).toBeGreaterThan(0));
  });

  it("zeigt quelle.url im Regel-Detail als Link", async () => {
    mockFetch({ "/wissen/regeln/R-005": VOLL_MIT_QUELLE, "/wissen/regeln": REGELN,
                "/wissen/klassen": ["schaltregler"] });
    render(<WissensPanel />);

    await userEvent.click(await screen.findByText(/Hot Loop klein halten/));

    const link = await screen.findByText("https://example.com/x.pdf");
    expect(link.closest("a")).not.toBeNull();
    expect(link.closest("a")).toHaveAttribute("href", "https://example.com/x.pdf");
  });

  it("wissen-geaendert lädt die Regeln des aktiven Sub-Tabs neu", async () => {
    mockFetch({ "/wissen/regeln/R-008": VOLL, "/wissen/regeln": REGELN,
                "/wissen/klassen": ["schaltregler"] });
    render(<WissensPanel />);
    await screen.findByText(/Hot Loop klein halten/);

    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    const zaehleRegelnAufrufe = () =>
      fetchMock.mock.calls.filter((c) => String(c[0]).includes("/wissen/regeln?")).length;
    const vorher = zaehleRegelnAufrufe();

    act(() => { window.dispatchEvent(new CustomEvent("wissen-geaendert")); });

    await waitFor(() => expect(zaehleRegelnAufrufe()).toBeGreaterThan(vorher));
  });

  it("wechselt zur Lücken-Tabelle", async () => {
    mockFetch({ "/wissen/luecken": [{ datum: "2026-09-08", frage: "F?",
                                      grund: "kein Beleg", status: "offen" }],
                "/wissen/regeln": [], "/wissen/klassen": [] });
    render(<WissensPanel />);

    await userEvent.click(screen.getByText("Lücken"));

    await screen.findByText("kein Beleg");
  });
});
