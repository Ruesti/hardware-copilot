# Motor — Chat-Einbettung (Etappe E4)

Die neutrale Motor-Schnittstelle des Cockpits (Spec §3.5): `schnittstelle.py`
definiert das Ereignis-Wire-Format (`text_haeppchen`, `werkzeug_gestartet`,
`werkzeug_fertig`, `rueckfrage`, `fertig`) und das Motor-Protokoll — ohne ein
einziges Claude-spezifisches Feld. `claude_motor.py` ist Motor 1: eine
Claude-Session übers Agent SDK (`claude-agent-sdk`), mit den MCP-Servern
`bestand` und `wissensschicht` als Werkzeugen und `can_use_tool`-Rückfragen,
die als Karten im Chat-Panel landen. `router.py` hängt genau eine Session an
`/motor/ws` (Verlauf im Speicher, Reconnect-fest, Neustart-Knopf).

Auth: wie Claude Code — Abo-Login der claude-CLI; ist `ANTHROPIC_API_KEY`
gesetzt, wird darüber abgerechnet. Ein zweiter Motor (andere KI) dockt an,
indem er das Protokoll aus `schnittstelle.py` implementiert und in
`router.motor_fabrik` eingesetzt wird.

## Gate-Lauf E4 (2026-09-09)

Ende-zu-Ende mit ECHTER Claude-Session im headless Browser (Chromium,
gebautes Frontend, Backend mit Gate-DB; Wissens-Panel-Repo = echtes
hardware-wissen mit 38 Regeln):

- Anfrage im Chat-Tab: „Welche 100-nF-Kondensatoren habe ich im Bestand,
  und welche Wissensschicht-Regel gilt für deren Platzierung? Buche danach
  2 Stück von T-1 ab."
- Stopp-Knopf erschien während der Antwort und verschwand bei `fertig`. ✓
- Werkzeug-Zeilen: `✓ bestand: teil_suchen`, `✓ wissensschicht: query_rules`,
  `✓ bestand: menge_aendern`, `✓ wissensschicht: get_rule` — ohne Rückfragen
  (MCP-Werkzeuge freigegeben). ✓
- Antwort: Bestandstreffer [T-1] mit Menge/Fach, Regel-Kurzformen R-001/002/004
  mit Stufe BELEGT, Volltext von R-001 wörtlich inkl. Quelle und Zitat. ✓
- Bestand-Tab danach: Menge 248 (KI-Abbuchung über dieselbe Datenschicht). ✓

**Gate BESTANDEN** — eine echte Anfrage läuft komplett in der App, die Panels
zeigen die Wirkung. Bewusst nicht Teil des Gates: der KiCad-Teil (Konnect) —
auf dem Entwicklungsrechner ohne KiCad nicht prüfbar; die Anbindung ist ein
`mcp_servers`-Eintrag bzw. `setting_sources` und folgt als eigener Schritt.

## Konnect / weitere Werkzeuge

Konnect (KiCad-Anbindung, Spec §3.5) ist maschinenabhängig als MCP-Server
registriert — auf dem Entwicklungs-NUC gar nicht, auf dem PC des Nutzers
schon. Statt Konnect fest zu verdrahten, liest `zusatz_server_aus_claude_config()`
dieselbe Config, die auch die Claude-Code-CLI selbst nutzt (`~/.claude.json`,
user-Scope-Server unter `mcpServers`) und übernimmt stdio-Einträge, deren
Name den Namensfilter enthält (case-insensitiv als Teilstring). Standard-Filter:
`"konnect"`, erweiterbar über die kommagetrennte Env `MOTOR_ZUSATZ_SERVER`
(z. B. `MOTOR_ZUSATZ_SERVER=spezial,extra`). Gefundene Server werden `_optionen()`
zu den Basis-Servern (`bestand`, `wissensschicht`) hinzugemischt — bei
Namenskollision gewinnt die Basis — und ihre Werkzeuge per
`mcp__<name>__*` in `allowed_tools` freigegeben; der System-Prompt bekommt
dynamisch einen Zusatzsatz. Fehlt die Config oder ist Konnect nicht
registriert, liefert die Discovery ein leeres Dict (kein Fehler) und der
Motor läuft mit den zwei Basis-Servern weiter.
