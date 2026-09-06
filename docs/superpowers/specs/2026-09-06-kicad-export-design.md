# Design: KiCad-Export (Phase 5)

**Datum:** 2026-09-06
**Status:** vom User freigegeben (Brainstorming-Session, 4 Weichen einzeln entschieden)
**Kontext:** Funktionstest vom 2026-09-06 hat gezeigt: Die KI erzeugt korrekte Schaltungs-Topologien und Bauteilwahl, erfindet aber Pin-Nummern (MCP73831: 3 von 5 Pins falsch, DM3AT: CD-Pin falsch). Konsequenz: Pin-Fakten müssen deterministisch aus einer Bibliothek kommen.

## Entscheidungen (User, 2026-09-06)

| Frage | Entscheidung |
|---|---|
| Zielartefakt | **Schaltplan-Gerüst** als `.kicad_sch` (KiCad 9): Symbole platziert, nach Blöcken gruppiert, Verbindungen als globale Netz-Labels — keine gezeichneten Leitungszüge |
| Pin-Quelle | **Kuratierte Bibliothek + Datenblatt-Pipeline**: Repo-YAML als Fundament; neue Bauteile per Datenblatt-Extraktion als „unvalidiert", User bestätigt per Haken |
| KiCad-Ziel | **KiCad 9**; Installation auf dem NUC (headless) für automatische Validierung per `kicad-cli` |
| Generator | **Eigener S-Expression-Writer** (Ansatz A), keine Dritt-Bibliothek (kiutils o. ä.) |

## Grundprinzip

> Die KI liefert **Semantik** (welches Bauteil an welches Netz — im Funktionstest fehlerfrei), die Bibliothek liefert **Fakten** (welche Pin-Nummer welche Funktion hat — dort war die KI unzuverlässig), der Generator kombiniert beides **deterministisch**.

## Datenfluss

```
SQLite (Blöcke, Komponenten, Verbindungen)
        +  backend/library/parts.yaml (Pin-Fakten)
        ↓
  Export-Modell (Netzliste: Bauteil-Pin → Netzname)
        ↓
  S-Expression-Generator  →  .kicad_sch (KiCad 9, self-contained)
        ↓
  Validierung: kicad-cli sch erc (Testsuite, NUC)
```

## Komponenten

### 1. Bauteil-Bibliothek — `backend/library/parts.yaml`

Zwei Ebenen:

- **MPN-Einträge** (Schlüssel: Bestellnummer). Felder: `kicad_symbol` (z. B. `Battery_Management:MCP73831-2-OT`), `footprint`, `pin_map` (Pin-Nummer → Rolle, z. B. `1: STAT, 2: VSS, 3: VBAT, 4: VDD, 5: PROG`), `datasheet` (URL, Quelle der Prüfung), `validated: true`.
- **Typ-Fallbacks** für Passive/Zweipoler: `passive_resistor → Device:R`, `passive_capacitor → Device:C` etc. — kein MPN-Eintrag nötig.

Startbestand: die 8 aktiven Bauteile/Steckverbinder des Testprojekts als MPN-Einträge (ESP32-S3-WROOM-1-N8, SHT31-DIS-B, MCP73831T-2ACI/OT, XC6220A331MR-G, USB4135-GF-A, DM3AT-SF-PEJM5, S2B-PH-K-S, ESD5Z5.0T1G), jeder gegen das Datenblatt geprüft; die Passiven (R/C) laufen über die Typ-Fallbacks.

Bauteil ohne Eintrag → Platzhalter-Symbol im Schaltplan + Report-Eintrag „nicht gemappt". Kein Raten.

### 2. Netz-Ableitung (deterministisch)

Netznamen aus zwei Quellen:

- **Blockverbindungen** (`conn_type` + Label): `gnd → GND`; `i2c → SDA, SCL`; `spi → SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS`; USB-Signal → `USB_DP, USB_DN`; `power` → Netzname aus dem Label normalisiert (`3.3V → 3V3`, `VBUS 5V → VBUS`, `VBAT …` → `VBAT`).
- **Pin-Rollen der Bibliothek**: Versorgungspins (VDD/VCC) an das Versorgungsnetz des Blocks, VSS/GND an GND, Interface-Pins (SDA/SCL/…) an die entsprechenden Verbindungsnetze.

**Neues Feld `net_role`** an Komponenten (DB-Spalte + Pydantic + Prompt-Erweiterung von `suggest_components`/`refresh-design`): strukturierte Semantik wie `decoupling`, `pullup:SDA`, `pulldown:CC1`, `series:SPI_CLK`, `prog_resistor`. Damit werden Passive korrekt an Netze gehängt. Komponenten ohne `net_role` (z. B. Bestandsdaten): Pins bleiben unbeschriftet — ehrlich offen statt falsch geraten.

### 3. Generator — `backend/app/kicad/`

- Eigener S-Expression-Writer für das KiCad-9-Schaltplanformat.
- **Symbole eingebettet**: Definitionen werden aus der offiziellen KiCad-Bibliothek (`/usr/share/kicad/symbols/*.kicad_sym`) geparst und in die `lib_symbols`-Sektion der Datei kopiert → Datei ist self-contained, öffnet auf jedem Rechner identisch.
- **Layout**: Bauteile pro Funktionsblock auf Rasterplätzen gruppiert, Blocktitel als Text; Verbindungen ausschließlich als globale Labels an den Pins.
- **Metadaten**: Referenzen (U1, R1, C1 … je Typ durchnummeriert), Werte, Footprints; UUIDs deterministisch aus den DB-IDs abgeleitet (gleicher Datenstand → byte-identische Datei, saubere Diffs).

### 4. API + UI

- `GET /projects/{id}/export/kicad` → `.kicad_sch`-Download; Begleit-Report (JSON): pro Komponente `mapped` / `fallback` / `unmapped` / `unverified`.
- Workbench-Tab: Export-Button + Report-Anzeige.

### 5. Datenblatt-Pipeline (Etappe 5.2)

- Beschaffung: vorhandener Nexar-Fetcher (per MPN) **oder** vorhandener PDF-Upload.
- **Umbau der Analyse**: statt pypdf-Textextraktion (verliert Pin-Tabellen; im Test nachgewiesen) das PDF **nativ als Dokument-Block** an die Claude-API geben.
- Extraktion liefert Pin-Map + Symbol-/Footprint-Vorschlag → neuer Eintrag in DB-Tabelle `library_overrides` mit `validated=false`.
- UI: Validier-Haken pro Eintrag (Muster wie `schematic_validated`).
- Export-Vorrang: Repo-YAML (validiert) → DB validiert → DB unvalidiert (wird exportiert, aber im Report und am Symbol als `UNVERIFIED` markiert).

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| MPN ohne Bibliothekseintrag und ohne Typ-Fallback | Platzhalter-Symbol + Report `unmapped` |
| KiCad-Symbolname im Eintrag existiert nicht in der installierten Bibliothek | Export läuft weiter, Bauteil als Platzhalter, Report-Fehler |
| Projekt ohne Verbindungen | Datei nur mit platzierten Symbolen, keine Labels |
| `kicad-cli` nicht installiert | betroffene Integrationstests werden mit Hinweis übersprungen |
| Komponente ohne `net_role` | Pins unbeschriftet, Report-Hinweis |

## Tests (erste Testsuite des Repos, pytest)

- **Unit**: Netznamen-Normalisierung, Netz-Ableitung aus conn_type/Pin-Rollen/net_role, YAML-Bibliotheks-Parser, S-Expression-Serialisierung, Symbol-Extraktion aus `.kicad_sym`.
- **Golden-File**: Testprojekt (ESP32-Logger) → erzeugte Datei strukturell gegen Erwartung geprüft.
- **Integration (NUC, benötigt KiCad)**: `kicad-cli sch erc` auf der erzeugten Datei — Abnahmekriterium: öffnet fehlerfrei, ERC ohne Fehler (Warnungen dokumentiert).

## Etappen

- **5.1** Bibliothek (Format + Starterbestand + Fallbacks) + `net_role` + Netz-Ableitung + Generator + Export-Endpoint + UI-Button + pytest-Suite + kicad-cli-Validierung. **Abnahme:** Testprojekt exportiert eine in KiCad 9 fehlerfrei öffnende, ERC-saubere Datei.
- **5.2** Datenblatt-Pipeline: natives PDF-Lesen, Extraktion → unvalidierter Eintrag, Validier-UI, Nexar-Anbindung.
- **Nebenbei in 5.1:** Bugfix `GET /blocks` liefert `schematic_ascii` nicht mit (`list_blocks` selektiert die Spalte nicht).

## Außerhalb des Umfangs

- Gezeichnete Leitungszüge (Auto-Routing im Schaltplan)
- PCB-Layout-Generierung
- Sheet-Hierarchien (ein Blatt reicht für die Projektgröße)
- Abwärtskompatibilität zu KiCad 7/8
