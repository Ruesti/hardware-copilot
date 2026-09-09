# Bestand — MCP-Server (Etappe E1)

Bestands-Datenbank des Hardware-Copilot-Cockpits: Welche Bauteile habe ich,
wo liegen sie, was kosten sie, welche Alternativen sind vermerkt? Entwurf:
`docs/superpowers/specs/2026-09-08-cockpit-bestand-leuchtregal-design.md`.

## Voraussetzungen

- Python ≥ 3.11, MCP-SDK 2.x: `pip install "mcp>=2,<3"` (venv der
  Wissensschicht kann mitbenutzt werden)
- Schreibbarer DB-Pfad — Default `~/.hardware-copilot/bestand.db`

## Einbinden in Claude Code

```bash
claude mcp add bestand -e BESTAND_DB=$HOME/.hardware-copilot/bestand.db \
  -- python -m bestand.server
```

Optional, sobald das Leucht-Regal existiert (Etappe E3):
`-e BESTAND_REGAL_URL=http://<regal-ip>/leuchten`

## Tools (Spec §3.2, E1-Umfang)

| Tool | Zweck |
|---|---|
| `teil_suchen` | Teilstring-Suche (Kurzzeilen); exakte "T-<id>" liefert Volltext mit Alternativen und Preisen (immer mit Stand-Datum). |
| `teil_anlegen` | Teil erfassen; Fach "Regal/Position", unbekannte Fächer werden angelegt. |
| `menge_aendern` | Menge relativ (+zugekauft/−verbraucht); unter 0 abgelehnt. |
| `alternative_vermerken` | Austausch-Bauteil zum Teil notieren. |
| `preis_cachen` | Recherchierten Preis mit Quelle ablegen; Datum setzt der Server. |
| `fach_leuchten` | Regal-Fach aufleuchten lassen; ohne Regal nur Fach-Auskunft. |

## Tests

```bash
python -m pytest bestand/tests/
```

Die Zuordnung Fach→LED (`faecher.led_nummer`) und die Regal-Firmware folgen
in Etappe E3; App-Panels in E2.

## Gate-Lauf E1 (2026-09-08)

Ende-zu-Ende über echte headless Claude-Code-Sessions gegen den eingebundenen
Server (temporäre Registrierung `bestand-gate`, eigene Demo-DB): 5 Demo-Teile
angelegt (2 × 10 µF verwechselbar, TPS54331, ESP32-S3, 100 nF). Befund:

- „Welchen 10-µF-Kondensator habe ich?" → beide Treffer mit korrekten Mengen
  (80/25) und Fächern (A/1, A/2), 100 nF korrekt nicht dabei. ✓
- Verbrauch: `menge_aendern(T-5, −3)` → „Menge jetzt 247". ✓
- `preis_cachen` → Antwort und Volltext tragen „Stand vom 2026-09-08". ✓
- `fach_leuchten(T-1)` ohne Regal → „Kein Regal konfiguriert — liegt in
  Fach A/1" (Regal ist optional). ✓
- Fehlgriff `T-99` → „⚠ Kein Teil mit ID T-99." statt Erfindung. ✓

**Gate BESTANDEN.** Die Befüllung mit dem realen Bestand steht noch aus
(Demo-DB wurde nicht übernommen); die produktive Einbindung zeigt auf
`~/.hardware-copilot/bestand.db` und wird mit dem Merge dieses Branches aktiv.

## Gate-Lauf E2 (2026-09-08)

Ende-zu-Ende im echten Browser (headless Chromium via playwright-core) am
gebauten Frontend (`vite preview`) gegen das laufende Cockpit-Backend
(eigene Gate-DB; Wissens-Panel gegen das echte hardware-wissen-Repo mit
38 Regeln). Befund:

- Bestand: Teil über das Formular angelegt → erscheint in der Liste mit
  Anlege-Meldung; „+1" hebt die Menge auf 251; Detail zeigt Leerzustände
  („keine vermerkt" / „keine Preise erfasst") und den Leuchten-Knopf. ✓
- Wissen: Regeln geladen, Stufe-Filter „vermutung" wirkt (belegte Regeln
  verschwinden), Volltext trägt den ⚠-VERMUTUNG-Marker, Begründung, Quelle
  („keine (Herleitung)"), Geltung und Ausnahmen. ✓
- Lücken-Tab rendert das Protokoll. ✓

**Gate BESTANDEN** — Spec-Kriterium wörtlich erfüllt: Bestand pflegen und
Regeln stöbern komplett ohne Terminal.
