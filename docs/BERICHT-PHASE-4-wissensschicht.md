# BERICHT Block E + Phase 4 — Heikel-Mechanik und Verified Blocks

Datum: 2026-09-08. Format nach §0: was gebaut, was getestet, was offen, welche Annahme sich als falsch erwiesen hat. Reihenfolge auf Betreiber-Anweisung: erst Block E, dann Phase 4.

## Was gebaut

**Block E — Frage statt Anweisung:**
- `heikel.toml` im Wissens-Repo (Wissen bleibt bei F5): vier Bereiche nach E1 (Netzspannung, Akku-Laden, Hochstrom/Thermik, Funk/Zertifizierung), Fragen im E3-Stil „Entscheidung mit Optionen", Fundstellen nach E4 aus den Regel-Quellen — wo keine existiert, ehrlich als quellenlos markiert.
- Auslösung nach E2 doppelt: Klassen-/Achsen-Flags UND strukturelle Schwellen über die neuen numerischen Fall-Achsen `spannung_v` (Netz: ≥ 50 V, §0-Entscheid) und `strom_a` (≥ 5 A, Design-Entscheidung, anpassbar). Greift auch bei Lücken, nicht nur bei getroffenen Regeln.
- Netzspannung unterdrückt zusätzlich die Kleinspannungs-Regeln mit ausdrücklicher Begründung — der GRENZEN.md-Punkt 5 („gefährlich-autoritativ") ist damit geschlossen.
- Dazu die beiden kleineren GRENZEN-Punkte: Katalog-Validierung (unbekannte Klassen werden mit Katalog gemeldet, unbekannte Achsenwerte gewarnt — nichts wird mehr still geschluckt) und C6-Fix (leere Ergebnisse werden immer protokolliert, auch ohne `frage`-Text).

**Phase 4 — Verified Blocks:**
- `blocks.py` + drei Tools (`record_block`, `search_blocks`, `get_block`), Serverumfang jetzt 8 Tools.
- Erfassung erzwingt das D2-Schema: ohne Messwerte, Messbedingungen, getestete Grenzen oder Ausschnitt wird nicht gespeichert („ein Verified Block ohne gemessen wäre kein Nachweis").
- D3: Der Ausschnitt wird als eigene Datei neben der Block-TOML eingefroren (`B-XXX-ausschnitt.txt` — Vereinfachung gegenüber dem Ordner-Entwurf, im Schema vermerkt).
- D4 ist in jede Ausgabe eingebaut: Suche und Volltext tragen den Hinweis, dass Übertragung auf Ähnliches Vermutung plus Differenzliste ist.
- C5 bleibt beim Menschen: `record_block` ändert nie Regel-Stufen, es liefert bei verknüpften Regeln nur den Hinweis, dass jetzt im Wissens-Repo hochgestuft werden kann.

## Was getestet

- 18 neue Tests (test-first: RED je Modul beobachtet, dann implementiert), gesamt 51 — alle grün.
- Live gegen die echte Regelbasis: Der 230-V-Fall liefert jetzt die E3-Frage plus Unterdrückungsgrund statt vier BELEGT-Stempeln; der Akku-Fall stellt die Schutz-/Ladestrom-/NTC-Frage vor die vier Regeln.
- **Damit ist die Phase-4-Vorgabe aus §0 erfüllt: Die Erfassung ist fertig, bevor der Split-Flap-Controller gebaut wird.** Es existiert noch kein realer Block — richtig so: `record_block` ist erst nach echtem Aufbau mit echten Messwerten zu benutzen.

## Was offen

- Das Verified-Block-Schema bleibt vorläufig (D5): Die Revision nach den ersten echten Blöcken vom Split-Flap-Aufbau ist eingeplant und kein Scheitern.
- Teilabdeckungs-Kennzeichnung (GRENZEN.md Punkt 4) weiterhin offen.
- Die `strom_a`-Schwelle (5 A) ist Design-Entscheidung ohne Norm-Anker — bei Bedarf in heikel.toml ändern.
- Der eingebundene Server lädt die neuen Tools erst nach Merge (der user-Scope-Eintrag zeigt auf den Haupt-Checkout).

## Welche Annahme sich als falsch erwiesen hat

- „Lücken-Protokollierung nur mit frage-Parameter schützt vor Müll" (Phase-2-Entwurf): Der Phase-3-Vergleichstest zeigte, dass genau dadurch echte Lücken still verloren gingen. Umgedreht — protokolliert wird immer; vor Müll schützt jetzt die Katalog-Validierung (Tippfehler-Klassen erzeugen keine Lücken-Einträge, sondern eine Katalog-Meldung).
