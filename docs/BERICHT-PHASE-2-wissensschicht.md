# BERICHT Phase 2 — Server mit Abfrage

Datum: 2026-09-08. Format nach §0: was gebaut, was getestet, was offen, welche Annahme sich als falsch erwiesen hat.

## Was gebaut

- MCP-Server `wissensschicht/` (Python, MCP-SDK 2.x, stdio), rein auf Abruf (F2), nur lesend gegenüber der Regelbasis — einzige Schreiboperation ist das Lücken-Protokoll (C6).
- Fünf Tools (F1 ohne Verified Blocks): `query_rules` (Kurzform, F4), `get_rule` (F3-Volltext: Markdown + eingebettetes JSON, C4-Marker ⚠ VERMUTUNG), `check_hint` (C2: nur abstufen; Anwendungs-Teil strukturell auf Vermutung gedeckelt, C3), `report_gap`, `list_gaps`.
- Match-Semantik (B2/A3): Pflichtachse `klasse` muss treffen; weitere Regel-Achsen müssen gleichen, wenn der Fall sie angibt — gibt der Fall sie nicht an, trifft die Regel, die Bedingung wird aber ausdrücklich als **unbestätigt** gemeldet.
- Store validiert beim Laden die Kern-Invariante: *belegt* nur mit vollständiger Primärquelle, *Vermutung* nie mit Primärquellen-Typ — eine unehrliche Regelbasis startet nicht.

## Was getestet

- 33 Tests (pytest), test-first entwickelt: Store-Validierung, Match-Semantik inkl. Unbestätigt-Mechanik, F3/C4-Format, C2-Abstufung, Lücken-Protokoll, Dienst-Schicht, Tool-Registrierung. Alle grün.
- **Gate-Lauf mit realem Schaltungsausschnitt** (`esp32-logger-tht.kicad_sch`: ESP32-S3-WROOM-1, XC6220-LDO, MCP73831-LiPo-Lader, USB-C): Abfrage über `mcu_wifi + versorgung_eingang + abblock_c` mit `antenne=pcb_onboard` lieferte 12 Regeln — Hinweise fachlich passend, Stufen ehrlich (3 × ⚠ VERMUTUNG klar getrennt). `check_hint` stufte eine zu hohe Anwendungs-Behauptung (belegt) korrekt auf Vermutung ab. Abfrage zur Klasse `ldo` (keine Regel) benannte die Lücke und protokollierte sie real.
- End-to-End über stdio: echter Serverprozess beantwortet `initialize` und `tools/list` korrekt.

**Gate aus §0 („Ein realer Schaltungsausschnitt liefert Hinweise, die stimmen und deren Stufen ehrlich sind"): BESTANDEN.**

## Was offen

- Numerische Geltungs-Achsen (`f_schalt_min_hz`, `strom_max_a`, …) sind im Schema definiert, aber im Matcher nicht implementiert — keine der 20 Regeln braucht sie bisher (bewusst kein Vorratsbau; nachrüsten, sobald eine Regel sie nutzt).
- Heikel-Mechanik aus Block E (Flag + Schwellen, Fragen statt Anweisungen) ist nicht Teil von Phase 2 — braucht autorisierte Frage-Texte, eigener Schritt.
- Verified-Block-Werkzeuge: Phase 4.
- Der Fall wird erzählt (A3); lesender KiCad-Zugriff kommt frühestens mit Phase 4.

## Welche Annahme sich als falsch erwiesen hat

- **MCP-SDK-API:** Der Server war gegen `FastMCP` (SDK 1.x) geplant; installiert wurde SDK 2.x, wo FastMCP zu `MCPServer` umbenannt ist. Import angepasst.
- **Chip-Familien-Blindheit der Klasse `mcu_wifi`:** Der Gate-Fall ist ein ESP32-**S3**, die Quellen von R-009–R-011 sind die ESP32-Guidelines. Der Rat stimmt inhaltlich, aber die Herkunft ist familien-spezifisch — als Lücke protokolliert (S3-Guidelines als Quelle nachtragen, Achse `chip_familie` erwägen). Genau die Art Grenze, die Phase 3 systematisch suchen soll.
