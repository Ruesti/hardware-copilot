import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { baueEintraege, ChatPanel, laeuftAusVerlauf } from "./ChatPanel";

const mockMotor = vi.hoisted(() => ({
  senden: vi.fn(),
  rueckfrageAntworten: vi.fn(),
  abbrechen: vi.fn(),
  neustart: vi.fn(),
  schliessen: vi.fn(),
  aufEreignis: null as ((e: unknown) => void) | null,
  aufStatus: null as ((verbunden: boolean) => void) | null,
}));

vi.mock("../../api/motor", () => {
  class MotorVerbindungMock {
    senden = mockMotor.senden;
    rueckfrageAntworten = mockMotor.rueckfrageAntworten;
    abbrechen = mockMotor.abbrechen;
    neustart = mockMotor.neustart;
    schliessen = mockMotor.schliessen;
    constructor(aufEreignis: (e: unknown) => void, aufStatus?: (v: boolean) => void) {
      mockMotor.aufEreignis = aufEreignis;
      mockMotor.aufStatus = aufStatus ?? null;
    }
  }
  return { MotorVerbindung: MotorVerbindungMock };
});

function feuere(ereignis: unknown) {
  act(() => { mockMotor.aufEreignis?.(ereignis); });
}

function statusFeuere(verbunden: boolean) {
  act(() => { mockMotor.aufStatus?.(verbunden); });
}

afterEach(() => {
  vi.clearAllMocks();
  mockMotor.aufEreignis = null;
  mockMotor.aufStatus = null;
});

describe("ChatPanel", () => {
  it("fügt aufeinanderfolgende text_haeppchen zu einem Absatz zusammen", () => {
    render(<ChatPanel />);

    feuere({ typ: "nutzer", text: "Frage?" });
    feuere({ typ: "text_haeppchen", text: "Hallo" });
    feuere({ typ: "text_haeppchen", text: "Welt" });

    expect(screen.getByText("Frage?")).toBeInTheDocument();
    expect(screen.getByText("HalloWelt")).toBeInTheDocument();
  });

  it("rueckfrage-Karte (werkzeug) — Erlauben ruft rueckfrageAntworten(id, true, ...)", async () => {
    render(<ChatPanel />);
    feuere({ typ: "rueckfrage", id: "rf-1", art: "werkzeug",
             text: "Darf ich bestand.menge_aendern ausführen?", optionen: [] });

    await userEvent.click(screen.getByText("Erlauben"));

    expect(mockMotor.rueckfrageAntworten).toHaveBeenCalledTimes(1);
    const [id, erlaubt, antwort] = mockMotor.rueckfrageAntworten.mock.calls[0];
    expect(id).toBe("rf-1");
    expect(erlaubt).toBe(true);
    expect(antwort == null).toBe(true);
  });

  it("werkzeug_fertig mit bestand-Werkzeug feuert bestand-geaendert", () => {
    render(<ChatPanel />);
    const spy = vi.fn();
    window.addEventListener("bestand-geaendert", spy);

    feuere({ typ: "werkzeug_gestartet", id: "w-1", name: "mcp__bestand__menge_aendern",
             anzeige: "bestand: menge_aendern" });
    feuere({ typ: "werkzeug_fertig", id: "w-1", name: "mcp__bestand__menge_aendern", fehler: false });

    expect(spy).toHaveBeenCalledTimes(1);
    window.removeEventListener("bestand-geaendert", spy);
  });

  it("werkzeug_fertig mit wissensschicht-Werkzeug feuert wissen-geaendert", () => {
    render(<ChatPanel />);
    const spy = vi.fn();
    window.addEventListener("wissen-geaendert", spy);

    feuere({ typ: "werkzeug_gestartet", id: "w-2", name: "mcp__wissensschicht__query_rules",
             anzeige: "wissen: query_rules" });
    feuere({ typ: "werkzeug_fertig", id: "w-2", name: "mcp__wissensschicht__query_rules", fehler: false });

    expect(spy).toHaveBeenCalledTimes(1);
    window.removeEventListener("wissen-geaendert", spy);
  });

  it("werkzeug_fertig mit projekt/position-Werkzeug feuert projekt-geaendert", () => {
    render(<ChatPanel />);
    const spy = vi.fn();
    window.addEventListener("projekt-geaendert", spy);

    feuere({ typ: "werkzeug_gestartet", id: "w-3", name: "mcp__bestand__position_hinzufuegen",
             anzeige: "bestand: position_hinzufuegen" });
    feuere({ typ: "werkzeug_fertig", id: "w-3", name: "mcp__bestand__position_hinzufuegen",
             fehler: false });

    expect(spy).toHaveBeenCalledTimes(1);
    window.removeEventListener("projekt-geaendert", spy);
  });

  it("laeuftAusVerlauf erkennt laufende Antwort", () => {
    expect(laeuftAusVerlauf([{ typ: "nutzer", text: "Hi" }])).toBe(true);
    expect(
      laeuftAusVerlauf([
        { typ: "nutzer", text: "Hi" },
        { typ: "fertig", fehler: null },
      ]),
    ).toBe(false);
    expect(laeuftAusVerlauf([])).toBe(false);
  });

  it("zeigt Stopp nach verlauf mit laufender Antwort", async () => {
    render(<ChatPanel />);
    feuere({ typ: "verlauf", ereignisse: [{ typ: "nutzer", text: "Hi" }] });
    expect(await screen.findByText("Stopp")).toBeInTheDocument();
  });

  it("zeigt Verbindungs-Warnung bei aufStatus(false) und blendet sie bei true wieder aus", () => {
    render(<ChatPanel />);
    expect(screen.queryByText(/nicht verbunden/)).not.toBeInTheDocument();

    statusFeuere(false);
    expect(screen.getByText(/nicht verbunden/)).toBeInTheDocument();

    statusFeuere(true);
    expect(screen.queryByText(/nicht verbunden/)).not.toBeInTheDocument();
  });

  it("verlauf setzt beantwortet zurück — Rückfrage-Karte wird nach Reconnect wieder klickbar", async () => {
    render(<ChatPanel />);
    feuere({ typ: "rueckfrage", id: "rf-9", art: "werkzeug", text: "Darf ich X?", optionen: [] });
    await userEvent.click(screen.getByText("Erlauben"));
    expect(screen.getByText(/beantwortet:/)).toBeInTheDocument();

    feuere({ typ: "verlauf", ereignisse: [
      { typ: "rueckfrage", id: "rf-9", art: "werkzeug", text: "Darf ich X?", optionen: [] },
    ] });

    expect(screen.queryByText(/beantwortet:/)).not.toBeInTheDocument();
    expect(screen.getByText("Erlauben")).toBeInTheDocument();
  });

  it("fertig mit fehler UND kosten rendert beide Zeilen", () => {
    const eintraege = baueEintraege([
      { typ: "nutzer", text: "Hi" },
      { typ: "fertig", fehler: "Zeitüberschreitung", kosten_usd: 0.12 },
    ]);
    expect(eintraege).toContainEqual({ typ: "gedaempft", text: "⚠ Zeitüberschreitung",
                                        farbe: "#f87171" });
    expect(eintraege).toContainEqual({ typ: "gedaempft", text: "— fertig (0,12 $)" });
  });

  it("Senden ist während laeuft deaktiviert", async () => {
    render(<ChatPanel />);
    feuere({ typ: "verlauf", ereignisse: [{ typ: "nutzer", text: "Hi" }] });

    expect(await screen.findByText("Stopp")).toBeInTheDocument();
    expect(screen.getByText("Senden")).toBeDisabled();
  });
});
