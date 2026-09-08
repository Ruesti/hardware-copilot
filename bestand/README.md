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
