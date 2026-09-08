# Design: Cockpit-App, Bestands-DB und Leucht-Regal

Datum: 2026-09-08 · Status: vom User freigegeben (Abschnitte 1–5 einzeln bestätigt)

## 1. Ausgangslage und Entscheidung

Die Wissensschicht (§0, Phasen 1–4) läuft als MCP-Server neben Konnect — bewusst ohne
eigene App. Offen geblieben war (§0 A4, vertagt): Inventar, BOM, Preise. Diese
Entscheidung wird jetzt getroffen: **Der User braucht eine sichtbare Oberfläche.**
Er muss sehen: Welches Bauteil habe ich? Alternativen? Preis? Bezugsquelle? Was ist
beim Schaltplan/Routing zu beachten, was wurde schon verifiziert gebaut, was lief schief?

Geklärter Ist-Stand: Nur Konnect (Claude Code ↔ KiCad) läuft real. Leucht-Regal und
Bestandsliste existieren noch nicht.

Geklärte Anforderungen:

- **Beide Nutzungsmodi gleichwertig:** live neben der KI-Session mitverfolgen **und**
  eigenständig ohne KI arbeiten (Bestand pflegen, Teil suchen, Wissen stöbern).
- **Zielbild: voller Chat in der App.** Die Schaltungsanfrage soll langfristig in der
  App gestellt werden; Claude Code wird Maschinenraum.
- **KI-Offenheit als „offene Steckdose":** Die Werkzeugschicht (MCP) ist ohnehin
  KI-agnostisch. Die App bindet die KI über eine neutrale Motor-Schnittstelle an;
  ein zweiter, beliebiger Motor wird erst gebaut, wenn er wirklich gewollt ist.
- **Alle vier Erfassungswege** in den Bestand (manuell, Bestell-Import, Foto-KI,
  Projekt-Verbrauch) — aber als Etappen, manuell zuerst.

Gewählter Ansatz (A): Vorhandene Tauri-Workbench wiederbeleben; erster Motor =
Claude Agent SDK über das bestehende Abo-Login (kein API-Schlüssel).

## 2. Architektur-Grundsatz

**Die Panels zeigen nie Chat-Text, sondern immer den Datenbestand.** Alles, was die
KI tut, landet in der gemeinsamen Datenschicht; die App schaut nur dorthin. Dadurch
funktioniert sie mit und ohne KI-Session identisch.

```
┌─────────────────── Tauri-App (vorhandenes Gerüst) ───────────────────┐
│  Bestand-Panel │ Teil-Detail (Alternativen,   │ Wissens-Panel │ Chat │
│  (suchen,      │ Preis, Bezugsquelle,         │ (Regeln,      │      │
│   pflegen)     │ „Fach leuchten“)             │ Verified      │      │
│                │                              │ Blocks, Lücken)│     │
└───────┬────────┴──────────────┬───────────────┴───────┬───────┴──┬───┘
        │      FastAPI-Backend (liest/schreibt Daten, steuert Regal) │
        ▼                                                    Motor-Schnittstelle
┌── Datenschicht ──────────────────────────────┐        (neutraler Ereignis-Strom)
│ bestand.db (SQLite): Teile, Fächer, Mengen,  │                  │
│   Preis-Cache, Projekt-Verbrauch             │                  ▼
│ hardware-wissen-Repo: Regeln, Verified       │      Motor 1: Claude Agent SDK
│   Blocks, Lücken-Protokoll (existiert)       │      (Abo-Login; nutzt dieselben
└──────────────▲───────────────────────────────┘       MCP-Server)
               │                                              │
      ┌────────┴──────── MCP-Werkzeugschicht (KI-offen) ──────┴────────┐
      │ Konnect (KiCad, existiert) │ Wissensschicht (existiert)        │
      │ NEU: Bestand-MCP — Teile suchen/anlegen/abbuchen, Alternativen,│
      │      Preise cachen, Regal-Fach leuchten lassen                 │
      └────────────────────────────────────────────────────────────────┘
                               │ WLAN (HTTP)
                               ▼
                    Leucht-Regal: ESP32 + LED je Fach
```

Ausführungsort: App samt Backend laufen auf dem Arbeitsrechner des Users (PC/Laptop;
der NUC ist bildschirmlos und bleibt Entwicklungsmaschine). Das Regal hängt im WLAN.

## 3. Komponenten

### 3.1 Bestands-DB (SQLite-Datei im FastAPI-Backend)

Tabellen:

- `teile` — Bezeichnung, Hersteller-Nummer, Bauteilklasse (dieselben Klassen wie im
  Achsenkatalog des Wissens-Repos, damit KI und Wissen dieselbe Sprache sprechen),
  Menge, Eckdaten, Datenblatt-Link, Fach-Zuordnung.
- `faecher` — Regal, Position, LED-Nummer.
- `preis_cache` — Teil, Quelle, Preis, Link, **Datum** (Preise veralten; das Datum
  wird immer mit angezeigt).
- `projekte` / `verbrauch` — für die spätere Abbuchung (Etappe E5+).

Eine einzige Datei, trivial zu sichern.

### 3.2 Bestand-MCP-Server (neu; Python, Bauart wie `wissensschicht/`)

Werkzeuge: `teil_suchen`, `teil_anlegen`, `menge_aendern`, `alternative_vermerken`,
`preis_cachen`, `fach_leuchten`.

Sofort in Claude Code einbindbar — Nutzen vor jeder App-UI („welchen 10-µF-Kondensator
habe ich da?" im Terminal). Die spätere App-KI nutzt exakt denselben Server. Preise
besorgt anfangs die KI per Recherche und legt sie über `preis_cachen` ab;
Händler-APIs (Mouser/LCSC) sind eine eigene spätere Etappe.

### 3.3 Leucht-Regal (ESP32 + adressierbarer LED-Streifen, eine LED pro Fach)

Bewusst dumm: Die Firmware kann genau eine Sache — per WLAN einen HTTP-Befehl
entgegennehmen: „Fach 17, Farbe, Dauer". Die Zuordnung Teil→Fach→LED kennt nur die
DB; das Backend übersetzt. Farben: Grün = „hier liegt dein Teil",
Blau = „hier einsortieren". Kein Display, keine Taster, keine Logik im Regal —
alles Kluge bleibt im Backend, damit die Firmware nie angefasst werden muss.

### 3.4 App-Panels (im vorhandenen Workbench-Gerüst)

- **Bestand-Panel** — suchen, filtern, Menge ändern, Teil anlegen (der manuelle
  Erfassungsweg).
- **Teil-Detail** — Eckdaten, Datenblatt, vermerkte Alternativen, Preis-Historie mit
  Datum, Knopf „Fach leuchten".
- **Wissens-Panel** — Regeln filterbar nach Klasse und Stufe, Verified Blocks,
  Lücken-Protokoll; dieselben Dateien, die die Wissensschicht der KI serviert, nur
  lesbar aufbereitet. ⚠-Marker (Vermutung) werden unverändert angezeigt.

Alle Panels reden ausschließlich mit dem FastAPI-Backend, nie mit der KI. Die alte
Strecke „App generiert selbst KiCad" (Spec→Draft→Export-Model→Generator) entfällt
und wird beim Umbau entrümpelt.

### 3.5 Chat-Panel + Motor-Schnittstelle

Dauerverbindung (WebSocket) zum Backend mit genau fünf Ereignistypen:
`text_haeppchen`, `werkzeug_gestartet`, `werkzeug_fertig`, `rueckfrage`
(Heikel-Fragen der Wissensschicht, Rechte-Nachfragen), `fertig`.
Werkzeug-Ereignisse erscheinen als kompakte Zeile („Konnect: Schaltplan angelegt");
die inhaltlichen Folgen zeigen die Panels über die Datenschicht.

Motor 1: Claude-Agent-SDK-Session mit den drei MCP-Servern, angemeldet über das
bestehende Abo. Die Schnittstelle enthält kein Claude-spezifisches Feld — das ist
die offene Steckdose. Ein zweiter Motor (eigene Schleife über OpenRouter/Ollama o. ä.)
ist bewusst NICHT Teil dieses Designs; er bleibt möglich, wird aber erst gebaut,
wenn er gewollt ist.

## 4. Datenfluss

**Mit KI** („Bau mir den 12-V-auf-5-V-Zweig"): Chat → Motor fragt Bestand-MCP
(was ist da?) → Wissensschicht (Regeln; Heikel-Rückfragen erscheinen als `rueckfrage`
im Chat) → Konnect (Schaltplan) → gewählte Teile, Alternativen, Preise landen per
Bestand-MCP in der DB. Jede DB-Änderung löst ein „Daten geändert"-Signal an die
Panels aus: links erscheint live, was gewählt wurde. Beim Bestücken:
`fach_leuchten` → Regal leuchtet grün, Fach für Fach.

**Ohne KI** („Wo ist mein 100-nF-Kondensator?"): Bestand-Panel → Backend → SQLite →
Teil-Detail (Menge, Fach, Datenblatt, Preise mit Datum) → Knopf „Fach leuchten" →
Backend → ESP32. Kein Motor beteiligt.

## 5. Etappen (jede einzeln nutzbar, mit eigenem Gate)

- **E1 — Bestands-DB + Bestand-MCP (ohne App).** Schema, MCP-Server, Einbindung in
  Claude Code. *Gate: „Welchen 10-µF-Kondensator habe ich?" wird im Terminal korrekt
  beantwortet; Teile lassen sich anlegen.* Zuerst: sofortiger Nutzen, kleinste
  Unsicherheit.
- **E2 — App-Cockpit.** Bestand-Panel, Teil-Detail, Wissens-Panel ans Backend;
  Workbench entrümpeln. *Gate: Bestand pflegen und Regeln stöbern ohne Terminal.*
- **E3 — Leucht-Regal.** Firmware (ein HTTP-Befehl), LED-Streifen, `faecher`-Zuordnung,
  App-Knopf und MCP-Werkzeug. *Gate: Fach leuchtet auf App-Knopf und auf KI-Zuruf.*
- **E4 — Chat-Einbettung.** Motor-Schnittstelle, Agent-SDK-Anbindung, Chat-Panel.
  Bewusst zuletzt: größtes Neuland; alles davor ist auch ohne es voll brauchbar.
  *Gate: eine echte Schaltungsanfrage läuft komplett in der App, Panels spiegeln live.*
- **E5+ — einzeln entscheidbar, später:** Bestell-Import (CSV Reichelt/Mouser/LCSC),
  Foto-Erfassung per KI, Verbrauchs-Abbuchung pro Projekt, Händler-Preis-APIs.

## 6. Fehlerverhalten und Tests

Grundsatz: **Die DB ist die Wahrheit, alles andere darf ausfallen.**

- Regal nicht erreichbar → klare Meldung; sonst ändert sich nichts.
- Preis-Cache alt → sichtbar „Stand vom …", nie stillschweigend als aktuell verkauft.
- Motor stürzt ab → Chat meldet Abbruch; Panels zeigen weiter den letzten DB-Stand.
- MCP-Server sind eigenständige Prozesse, einzeln neustartbar.
- Wissensschicht-Grundsätze unverändert: Stufen nie hochstufen, Lücken offen benennen,
  ⚠-Marker durchreichen.

Tests: pytest für Backend, DB-Schicht und Bestand-MCP (Bauart wie die
Wissensschicht-Tests); pro Etappe ein Gate-Lauf an einem echten Fall (bewährter
§0-Stil). Die Firmware bleibt so klein, dass ein Testskript plus Sichtprüfung genügt.

## 7. Ausdrücklich nicht Teil dieses Designs

- Zweiter KI-Motor (modell-agnostische Eigenbau-Schleife) — Steckdose ja, Motor nein.
- Händler-Preis-APIs, Bestell-Import, Foto-Erfassung, Verbrauchs-Abbuchung (E5+,
  je eigene Entscheidung).
- Jede Form von „App generiert KiCad direkt" — KiCad-Arbeit läuft ausschließlich
  über Konnect.
- Mechanik/Details der Regal-Hardware (Fächerzahl, Netzteil, Gehäuse) — wird in der
  E3-Planung entschieden.
