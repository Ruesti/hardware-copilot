# Wissensschicht — MCP-Server (Phase 2)

Der lesende MCP-Server der Wissens- und Herkunftsschicht: Er beantwortet Schaltungs- und Layout-Fragen ausschließlich aus der Regelbasis im Wissens-Repo und weist zu jedem Hinweis die Herkunftsstufe aus (belegt / verifiziert / Vermutung). Entwurfsgrundlage: `docs/section0-wissensschicht.md` (§0, Blöcke A–F).

## Voraussetzungen

- Python ≥ 3.11 (tomllib), MCP-SDK 2.x: `pip install "mcp>=2,<3"`
- Das Wissens-Repo (Regelbasis) — Pfad über `WISSENSSCHICHT_REPO`, Default `~/projects/hardware-wissen`

## Einbinden in Claude Code

```bash
claude mcp add wissensschicht -e WISSENSSCHICHT_REPO=$HOME/projects/hardware-wissen \
  -- python -m wissensschicht.server
```

(Bei venv: den Python-Pfad des venv angeben.)

## Tools (§0 F1, Phase-2-Umfang)

| Tool | Zweck |
|---|---|
| `query_rules` | Regeln zu einem Fall (Klassen + Achsen) — Kurzform: ID, Stufe, Aussage. Leeres Ergebnis benennt die Lücke und protokolliert sie (C6). Unbekannte Klassen/Achsenwerte werden gemeldet statt still geschluckt. |
| `get_rule` | Volltext einer Regel: Begründung, Quelle mit Fundstelle und Zitat, Geltung, Ausnahmen — Markdown + eingebettetes JSON (F3). |
| `check_hint` | Hinweis-Entwurf prüfen: Server stuft nur ab, nie hoch (C2); Anwendungs-Teil ist immer höchstens Vermutung (C3). |
| `report_gap` | Wissenslücke ins Lücken-Protokoll eintragen. |
| `list_gaps` | Lücken-Protokoll auflisten. |
| `record_block` | Verified Block erfassen (Phase 4, §0 D1-D3): real gebauter, vermessener Aufbau mit Messbedingungen, Grenzen und eingefrorenem Ausschnitt. |
| `search_blocks` | Verified Blocks durchsuchen — mit D4-Hinweis: Übertragung auf Ähnliches ist Vermutung plus Differenzliste. |
| `get_block` | Volltext eines Verified Blocks. |

Kontextverbrauch: zweistufig (F4) — `query_rules` liefert Kurzformen, Volltext nur per `get_rule`.

**Heikle Bereiche (§0 Block E):** `heikel.toml` im Wissens-Repo definiert Bereiche (Netzspannung, Akku-Laden, Hochstrom/Thermik, Funk/Zertifizierung) mit Fragen im E3-Stil. Ausgelöst über Klassen-/Achsen-Flags und die numerischen Fall-Achsen `spannung_v`/`strom_a` (Schwelle Netzspannung: ≥ 50 V). Die Frage steht vor allen Regeln; bei Netzspannung werden die Kleinspannungs-Regeln mit Begründung unterdrückt. Deshalb: Spannung und Strom des Falls bei `query_rules` immer mit angeben.

## Tests

```bash
python -m pytest wissensschicht/tests/
```

Verified-Block-Werkzeuge folgen in Phase 4; eine Ganzplan-Prüfung ist bewusst nicht Teil von Phase 2 (F2: rein auf Abruf).
