import { afterEach, describe, expect, it, vi } from "vitest";
import { positionZuordnen, projektAbbuchen } from "./projekte";

const antwort = (daten: unknown, ok = true, status = 200) =>
  Promise.resolve({ ok, status, json: () => Promise.resolve(daten) } as Response);

afterEach(() => vi.unstubAllGlobals());

describe("api/projekte", () => {
  it("positionZuordnen ruft die richtige URL mit teilId-Body", async () => {
    const f = vi.fn((_eingabe: RequestInfo | URL, _init?: RequestInit) => antwort({ meldung: "ok" }));
    vi.stubGlobal("fetch", f);

    await positionZuordnen(1, "C1", 3);

    const [url, init] = f.mock.calls[0];
    expect(String(url)).toContain("/projekte/1/positionen/C1/zuordnen");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ teilId: 3 }));
  });

  it("wirft die Backend-Meldung als Error", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      antwort({ detail: "Projekt bereits abgebucht." }, false, 400)));

    await expect(projektAbbuchen(1)).rejects.toThrow("bereits abgebucht");
  });
});
