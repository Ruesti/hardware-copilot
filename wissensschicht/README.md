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
| `query_rules` | Regeln zu einem Fall (Klassen + Achsen) — Kurzform: ID, Stufe, Aussage. Leeres Ergebnis benennt die Lücke und protokolliert sie (C6). |
| `get_rule` | Volltext einer Regel: Begründung, Quelle mit Fundstelle und Zitat, Geltung, Ausnahmen — Markdown + eingebettetes JSON (F3). |
| `check_hint` | Hinweis-Entwurf prüfen: Server stuft nur ab, nie hoch (C2); Anwendungs-Teil ist immer höchstens Vermutung (C3). |
| `report_gap` | Wissenslücke ins Lücken-Protokoll eintragen. |
| `list_gaps` | Lücken-Protokoll auflisten. |

Kontextverbrauch: zweistufig (F4) — `query_rules` liefert Kurzformen, Volltext nur per `get_rule`.

## Tests

```bash
python -m pytest wissensschicht/tests/
```

Verified-Block-Werkzeuge folgen in Phase 4; eine Ganzplan-Prüfung ist bewusst nicht Teil von Phase 2 (F2: rein auf Abruf).
