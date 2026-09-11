# Design: Projekte mit Stückliste, KiCad-Brücke, Design-Pass (E5–E7)

Datum: 2026-09-10 · Status: vom User freigegeben (Abschnitte 1–4 einzeln bestätigt)
Baut auf: `2026-09-08-cockpit-bestand-leuchtregal-design.md` (E1–E4 ausgeliefert)

## 1. Ausgangslage

Laptop-Test des Cockpits (E1–E4): Chat funktioniert; Kritik des Users:
(a) keine vollständige **Bauteilliste** — man sieht Regeln, aber keine
Projekt-Stückliste mit Bestandsabgleich; (b) **KiCad-Export fehlt** — der
alte Export (Branch `feat/kicad-export`, nie gemergt) fiel mit der alten
Welt weg; (c) die App ist **„weder schön noch übersichtlich"**.

Geklärte Entscheidungen:
- Projekte entstehen **durch die KI plus minimal manuell**.
- KiCad-Brücke: **kein Auto-Routing** („LLM bekommt das nicht anständig
  hin"), aber **Baugruppen-Platzierung** und **Routing-Anleitung aus der
  Wissensbasis** — „wenn das funktionieren würde, wäre großartig".
- Design: **dunkel verfeinern, als letzter Schritt** über alle Tabs.
- Mehrere Händler: Preis-Cache trägt bereits mehrere Quellen je Teil;
  BOM zeigt den günstigsten aktuellen Preis (aufklappbar), Fehlteile-Summe
  rechnet mit dem günstigsten. Händler-APIs bleiben spätere Etappe.

Etappen in dieser Reihenfolge: **E5 Projekte/Stückliste → E6 KiCad-Brücke
→ E7 Design-Pass** (Brücke braucht die BOM; Design zum Schluss über alles).

## 2. E5 — Projekte und Stückliste

### 2.1 Datenmodell (in `bestand.db`; Tabellen waren als E5+ vorgesehen)

- `projekte` — id, name, beschreibung, status (`offen`/`gebaut`),
  angelegt_am.
- `projekt_positionen` — id, projekt_id, **referenz** (C3, U1 — eindeutig
  je Projekt), bezeichnung, menge (benötigt, Default 1), klasse
  (Achsenkatalog-Vokabular), **baugruppe** (Freitext: „Versorgung",
  „MCU" — später PCB-Gruppierung), teil_id (nullable FK auf `teile`),
  **pins** (JSON Pin→Netz, z. B. `{"1": "GND", "2": "+3V3"}`, nullable),
  kicad_symbol (nullable), kicad_footprint (nullable), notiz.
- `verbrauch` — projekt_id, teil_id, menge, datum (Log der Abbuchung).

### 2.2 Bestandsabgleich (reine Ableitung, kein gespeicherter Zustand)

Je Position: mit `teil_id` → Vorrat aus `teile.menge` → Status **da**
(Vorrat ≥ benötigt), **knapp** (0 < Vorrat < benötigt), **fehlt**
(Vorrat 0); ohne Verknüpfung → **nicht zugeordnet**. Preis je Position:
**günstigster aktueller** Eintrag aus dem `preis_cache` des verknüpften
Teils, mit Händlername und „Stand vom"; alle Händler aufklappbar.
Kopfzeile je Projekt: „9 von 12 Positionen im Bestand · Fehlteile ≈ 3,40 €"
(Summe über günstigste Preise der fehlenden/knappen Positionen).

### 2.3 MCP-Werkzeuge (im bestehenden `bestand`-Server)

`projekt_anlegen(name, beschreibung="")` → [P-1];
`position_hinzufuegen(projekt_id, referenz, bezeichnung, menge=1,
klasse="", teil_id=None, baugruppe="", pins=None, kicad_symbol="",
kicad_footprint="", notiz="")`;
`position_verknuepfen(projekt_id, referenz, teil_id)`;
`projekt_zeigen(projekt_id)` — BOM mit Abgleich als Text (Terminal-tauglich);
`projekt_abbuchen(projekt_id)`.
Damit sofort im Chat UND Terminal nutzbar. Motor-System-Prompt-Zusatz:
*Beim Schaltungsentwurf ein Projekt anlegen und jede gewählte Komponente
als Position mit Referenz, Baugruppe und Pin-Netzen ablegen; Bestands-Teile
verknüpfen; KiCad-Symbol/Footprint mitliefern, wenn bekannt.*

### 2.4 Projekt-Tab (vierter Tab, Bauart wie Bestand-Tab)

Links Projektliste (`[P-1] ESP32-Logger — offen · 12 Positionen · 3
fehlen`) + minimales manuelles Anlegen (Name + Beschreibung). Rechts
Detail: **BOM-Tabelle gruppiert nach Baugruppe** — Spalten Referenz,
Bezeichnung, benötigt, Bestand (Menge · Fach), Status-Badge
(grün/gelb/rot), Preis (günstigster, Händler, Stand). Zeilen-Aktionen:
Fach leuchten (verknüpfte Teile), Teil zuordnen (Auswahl aus Bestand).
Projekt-Aktionen: **„Als gebaut abbuchen"** (Bestätigung; bucht alle
verknüpften Positionen ab, schreibt `verbrauch`, Status → `gebaut`),
ab E6 die Export-Knöpfe. Live-Spiegel: `projekt-geaendert`-Event bei
mcp__bestand-Projektwerkzeugen → Tab lädt nach. Backend: dünner Router
`/projekte` über denselben Dienst wie die MCP-Werkzeuge.

### 2.5 Fehlerverhalten

**Abbuchen lehnt ab, wenn eine verknüpfte Position nicht gedeckt ist**,
und benennt die Lücken (kein stilles Halb-Abbuchen). Nicht zugeordnete
Positionen blockieren das Abbuchen nicht (sie werden übersprungen und im
Ergebnis benannt). Referenz-Duplikat je Projekt → Fehler.

## 3. E6 — KiCad-Brücke

### 3.1 Portierung

Alte Bausteine aus `feat/kicad-export` nach `backend/app/kicad/`
übernehmen: `sexpr`, `sch_writer`, `symbols`, `library`, `footprints`,
`pcb`, `pcb_build_script`, `system` (pcbnew-Installations-Check). **Neu**:
Modell-Bauer aus Projekt-Positionen (ersetzt `netlist.build_export_model`
samt alter Blocks/Components-Kopplung). Symbol-Zuordnung dreistufig:
explizites `kicad_symbol`/`kicad_footprint` der Position gewinnt → sonst
kuratierte Bibliothek → sonst **Mapping-Report** („übersprungen: R7 —
kein Symbol"), nie stilles Fehlen.

### 3.2 Drei Artefakte je Export → `~/hardware-copilot-exporte/<slug>/`

1. **`.kicad_sch`** — Symbole mit Referenz und Wert; an belegten Pins
   Stummel-Drähte mit Netz-Labels aus `pins`. Direkt weiterverdrahtbar,
   ERC-fähig.
2. **`.kicad_pcb`** — **ungeroutet**; Bauteile nach **Baugruppe**
   gruppiert platziert (Spalte je Baugruppe, ICs links, Passive daneben),
   Pads mit Netzen (Ratsnest sichtbar). Braucht pcbnew-Python; fehlt es,
   entstehen Schaltplan+Anleitung trotzdem plus klarer Hinweis.
3. **Routing-Anleitung (HTML)** — **einzige Quelle: Wissensbasis.**
   Regeln gefiltert nach den Klassen der BOM, konkretisiert auf echte
   Referenzen („C3, C7 nah an die Versorgungspins von U1"), jede mit
   Stufe und Quelle (BELEGT mit Zitat / ⚠ VERMUTUNG); Warnblock bei
   betroffenen Heikel-Bereichen (heikel.toml). Die alten hartkodierten
   Heuristiken entfallen ersatzlos.

### 3.3 Bedienung

Projekt-Tab-Knopf „KiCad-Export" → Mapping-Report + Ausgabepfad +
„In KiCad öffnen"-Versuch (xdg-open; Fehlschlag wird nur gemeldet);
Anleitung zusätzlich im Tab anzeigbar. Endpunkt
`POST /projekte/{id}/kicad-export`.

## 4. E7 — Design-Pass (dunkel verfeinert, über alles)

- **Design-Tokens** zentral (Farben, Abstände, Schriftgrößen, Radien)
  statt verstreuter Hex-Werte.
- **Hierarchie/Dichte:** klare Titelzeilen, gedämpfte Metadaten, Tabellen
  mit Zeilentrennung, konsistente Detail-Karten; BOM-Tabelle als
  dichteste Fläche.
- **Farbe mit Bedeutung, sparsam:** grün/gelb/rot nur für Status, Gelb
  für ⚠/Rückfragen, Blau für verifiziert, ein Akzentton für Aktionen,
  sonst neutrale Grautöne.
- **Werkstatt-Charakter:** Monospace für Referenzen/IDs/Mengen, ruhige
  Serifenlose für Text, keine verspielten Effekte.
- Umsetzung mit Frontend-Design-Skill; keine Funktionsänderungen.

## 5. Gates

- **E5:** Echte Chat-Anfrage erzeugt Projekt mit vollständiger BOM;
  Projekt-Tab zeigt Abgleich + Fehlteile-Summe; Abbuchen reduziert
  Bestand und schreibt Verbrauchs-Log (Ablehnung bei Unterdeckung geprüft).
- **E6:** Für das Gate-Projekt entstehen parsebare `.kicad_sch` (mit
  Netz-Labels), `.kicad_pcb` (Baugruppen-Spalten; bzw. sauberer Hinweis
  ohne pcbnew) und Anleitung mit projektbezogenen Regeln inkl.
  Stufen/Quellen. KiCad-Öffnen = Gerätetest des Users am PC/Laptop.
- **E7:** Vorher/Nachher-Screenshots aller Tabs, Abnahme durch den User.

## 6. Ausdrücklich nicht Teil dieses Designs

- Auto-Routing jeder Art (bewusst ausgeschlossen).
- Händler-Preis-APIs (weiterhin spätere Etappe; Preise via KI-Recherche).
- Versionierung/Varianten von Projekten, Mehrplatinen-Projekte.
- Portierung des alten Chat/Draft-Backends — nur die KiCad-Bausteine
  wandern zurück.
