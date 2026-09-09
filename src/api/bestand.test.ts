import { afterEach, describe, expect, it, vi } from "vitest";
import { createTeil, fetchTeile } from "./bestand";

const antwort = (daten: unknown, ok = true, status = 200) =>
  Promise.resolve({ ok, status, json: () => Promise.resolve(daten) } as Response);

afterEach(() => vi.unstubAllGlobals());

describe("api/bestand", () => {
  it("fetchTeile hängt Suchparameter an", async () => {
    const f = vi.fn((_eingabe: RequestInfo | URL) => antwort([]));
    vi.stubGlobal("fetch", f);

    await fetchTeile("100nF", "abblock_c");

    const url = String(f.mock.calls[0][0]);
    expect(url).toContain("/bestand/teile?");
    expect(url).toContain("suche=100nF");
    expect(url).toContain("klasse=abblock_c");
  });

  it("wirft die Backend-Meldung als Error", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      antwort({ detail: "Menge muss ≥ 0 sein, war -1." }, false, 400)));

    await expect(createTeil({ bezeichnung: "X", menge: -1, fach: "A/3" }))
      .rejects.toThrow("Menge muss ≥ 0 sein");
  });
});
