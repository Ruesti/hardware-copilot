import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "./ChatPanel";

const mockMotor = vi.hoisted(() => ({
  senden: vi.fn(),
  rueckfrageAntworten: vi.fn(),
  abbrechen: vi.fn(),
  neustart: vi.fn(),
  schliessen: vi.fn(),
  aufEreignis: null as ((e: unknown) => void) | null,
}));

vi.mock("../../api/motor", () => {
  class MotorVerbindungMock {
    senden = mockMotor.senden;
    rueckfrageAntworten = mockMotor.rueckfrageAntworten;
    abbrechen = mockMotor.abbrechen;
    neustart = mockMotor.neustart;
    schliessen = mockMotor.schliessen;
    constructor(aufEreignis: (e: unknown) => void) {
      mockMotor.aufEreignis = aufEreignis;
    }
  }
  return { MotorVerbindung: MotorVerbindungMock };
});

function feuere(ereignis: unknown) {
  act(() => { mockMotor.aufEreignis?.(ereignis); });
}

afterEach(() => {
  vi.clearAllMocks();
  mockMotor.aufEreignis = null;
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
});
