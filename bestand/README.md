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

## Tools — Projekte/Stückliste (Spec §2, Etappe E5)

| Tool | Zweck |
|---|---|
| `projekt_anlegen` | Neues Projekt (Schaltungsentwurf/Baugruppe) anlegen. |
| `position_hinzufuegen` | Stückliste-Position hinzufügen; Referenz wie im Schaltplan (C3, U1), `pins` = Pin→Netz fürs spätere KiCad, `klasse` aus dem Achsenkatalog. |
| `position_verknuepfen` | Position nachträglich mit einem Bestandsteil (T-<id>) verknüpfen. |
| `projekt_zeigen` | Stückliste mit Bestandsabgleich (da/knapp/fehlt) und Fehlteile-Kosten. |
| `projekt_abbuchen` | Verknüpfte Positionen abbuchen und Projekt abschließen; Unterdeckung bricht komplett ab. |

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

## Gate-Lauf E5 (2026-09-10)

Ende-zu-Ende mit echter Claude-Session im headless Browser: Chat-Anfrage
„Lege ein Projekt Blink-Board an …" → KI nutzte `projekt_anlegen` und
`position_hinzufuegen` (U1/C1/C2 mit Bestands-Verknüpfung und Pin-Netzen,
R1 unverknüpft). Projekt-Tab zeigte die BOM gruppiert (MCU/Sonstiges/
Versorgung) mit Status-Badges (da/nicht zugeordnet), Händlerpreisen mit
„Stand vom" und der Kopfzeile „3 von 4 Positionen im Bestand · Fehlteile
≈ 0,00 € · 1 ohne Preis". „Als gebaut abbuchen" über die UI: „[P-1]
abgebucht: 3 Positionen.", Status → gebaut, Bestand-Tab zeigte 248/1.

**Gate BESTANDEN** — Chat erzeugt Projekt mit vollständiger Stückliste,
Tab zeigt Abgleich + Summe, Abbuchen reduziert Bestand und loggt Verbrauch.

## Gate-Lauf E6 (2026-09-11)

Ende-zu-Ende im headless Browser gegen den laufenden Stack (Gate-DB mit
Projekt „Lade-Board": U1 = MCP73831 ohne `kicad_symbol` — die Bibliotheks-
Kaskade über die Hersteller-Nr. musste greifen —, C1/C2/R1 mit expliziten
Symbolen und Pin-Netzen, R7 bewusst ohne Zuordnung; echtes Wissens-Repo).
Befund:

- UI-Export: Report-Box „✓ 4 Symbole", „⚠ R7 — kein KiCad-Symbol —
  kicad_symbol angeben oder Teil in parts.yaml aufnehmen", Warnungen zu
  Einzelanschluss-Netzen (PROG, LED_K → no_connect), Export-Pfad;
  „Anleitung ansehen" und „In KiCad öffnen" (Meldung) funktionieren. ✓
- Erzeugte Dateien: `.kicad_sch`, `.kicad_pcb` (+ `.kicad_pro`/`.kicad_prl`
  von pcbnew), `anleitung.html`. ✓
- **ERC als Wahrheitsinstanz:** `kicad-cli sch erc` (KiCad 9.0.2) auf dem
  UI-erzeugten Schaltplan → **0 Verstöße**. ✓
- PCB via pcbnew geladen: 4 Footprints (U1/C1/C2/R1) in Baugruppen-Spalten,
  7 Netze, **0 Leiterbahnen** (ungeroutet, wie spezifiziert). ✓
- Anleitung: 7 projektbezogene Regel-Karten (3× abblock_c „betrifft: C1,
  C2", 4× akku_lader „betrifft: U1") mit Stufen-Badges (6× BELEGT,
  1× ⚠ VERMUTUNG), Quellen und Zitaten; Heikel-Warnblock „⚠ Heikle
  Bereiche" (akku_laden) oben. ✓

**Gate BESTANDEN** — ein Klick liefert ERC-sauberen Schaltplan, ungeroutete
Platine mit Baugruppen-Platzierung und eine Routing-Anleitung, die
ausschließlich aus der Wissensbasis gespeist ist.
