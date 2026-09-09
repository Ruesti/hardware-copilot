# E4: Chat-Einbettung — Motor-Schnittstelle + Claude-Agent-Motor + Chat-Panel

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voller Chat in der App (Spec §3.5): Das Chat-Panel spricht über eine neutrale Motor-Schnittstelle (WebSocket, 5 Ereignistypen) mit Motor 1 = Claude übers Claude Agent SDK; Bestand- und Wissens-Panel spiegeln live, was die KI über die Datenschicht ändert.

**Architecture:** Backend bekommt ein Paket `backend/app/motor/`: `schnittstelle.py` definiert die neutralen Ereignisse und das Motor-Protokoll (kein Claude-spezifisches Feld — die „offene Steckdose"), `claude_motor.py` implementiert es über `claude-agent-sdk` (`ClaudeSDKClient`, Mehrturn-Session, `can_use_tool`-Callback → Rückfrage-Ereignis), `router.py` hängt genau EINE globale Motor-Session an `/motor/ws` (Single-User-Desktop; Verlauf im Speicher, bei Reconnect zuerst Verlauf, dann live). Der Motor bekommt als Werkzeuge die zwei eigenen MCP-Server (bestand, wissensschicht) explizit konfiguriert — dieselben Prozesse, dieselbe DB wie Terminal-Claude. Frontend: dritter Tab „Chat" mit ChatPanel; bei `werkzeug_fertig` eines bestand-Werkzeugs feuert ein Browser-Event, auf das das BestandPanel mit Neuladen reagiert (Live-Spiegel).

**Tech Stack:** Python ≥ 3.11, FastAPI-WebSocket, `claude-agent-sdk` (bündelt die claude-CLI; Auth wie Claude Code — Abo-Login, bzw. `ANTHROPIC_API_KEY` falls gesetzt), React/TS + vitest.

## Global Constraints

- Alle Bezeichner, Meldungen, UI-Texte deutsch mit deutscher Typografie; ⚠-Marker der Wissensschicht nie unterschlagen.
- Die Motor-Schnittstelle (`schnittstelle.py` + Wire-Format) enthält KEIN Claude-spezifisches Feld. Ereignistypen exakt (Spec §3.5): `text_haeppchen`, `werkzeug_gestartet`, `werkzeug_fertig`, `rueckfrage`, `fertig`. Client→Motor: `nutzer`, `rueckfrage_antwort`, `abbrechen`, `neustart`.
- Claude-Aufrufe NUR in `claude_motor.py`; Router und Frontend kennen nur die Schnittstelle.
- Motor-MCP-Konfiguration aus denselben Umgebungsvariablen wie die MCP-Server selbst: `BESTAND_DB`, `WISSENSSCHICHT_REPO`; Python-Binary für die Server = `sys.executable` (das venv, in dem das Backend läuft — dort sind mcp + beide Pakete importierbar; `PYTHONPATH` auf Repo-Root setzen).
- Tests dürfen KEINE echte Claude-Session starten (Kosten!) — der Motor-Kern wird mit einem injizierten Fake-Client getestet; die echte Session läuft nur im Gate (Task 6).
- Python-Tests: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest <pfad> -v` vom Worktree-Root. Einmalig (Task 1 Step 0): `~/projects/hardware-copilot/.venv-wissen/bin/pip install claude-agent-sdk`.
- Frontend: `npx vitest run` und `npm run build` nach jedem Frontend-Task grün; vitest@4/jsdom@26 sind für Node 20 gepinnt — devDependencies nicht aktualisieren.
- SDK-Symbole (ClaudeSDKClient, ClaudeAgentOptions, Message-/Block-Typen, PermissionResultAllow/Deny) beim Implementieren gegen das INSTALLIERTE Paket verifizieren (`python -c "import claude_agent_sdk, inspect; ..."`) — bei Abweichung vom Plan-Code die installierte Realität nehmen und im Report vermerken.

---

### Task 1: Motor-Schnittstelle + Claude-Motor-Kern

**Files:**
- Create: `backend/app/motor/__init__.py` (leer), `backend/app/motor/schnittstelle.py`, `backend/app/motor/claude_motor.py`
- Test: `backend/tests/test_motor_kern.py`

**Interfaces:**
- Consumes: `claude-agent-sdk` (nur in claude_motor.py)
- Produces:
  - `schnittstelle.py`: `@dataclass Ereignis { typ: str, daten: dict }`-freie Variante — wir nutzen schlichte dicts als Wire-Format plus Konstanten; und das Protokoll:
    ```python
    class Motor(Protocol):
        async def start(self) -> None: ...
        async def frage(self, text: str) -> AsyncIterator[dict]: ...   # liefert Ereignis-Dicts bis inkl. {"typ": "fertig", ...}
        async def rueckfrage_antworten(self, rueckfrage_id: str, erlaubt: bool, antwort: str | None) -> None: ...
        async def abbrechen(self) -> None: ...
        async def stop(self) -> None: ...
    ```
  - Ereignis-Dicts (Wire-Format, camel-frei, deutsch):
    - `{"typ": "text_haeppchen", "text": str}`
    - `{"typ": "werkzeug_gestartet", "id": str, "name": str, "anzeige": str}` — `anzeige` z. B. `"bestand: teil_suchen"` (MCP-Namen `mcp__bestand__teil_suchen` → Server+Tool; andere Namen unverändert)
    - `{"typ": "werkzeug_fertig", "id": str, "name": str, "fehler": bool}`
    - `{"typ": "rueckfrage", "id": str, "art": "werkzeug" | "frage", "text": str, "optionen": list[str]}` — `art="frage"` wenn `tool_name == "AskUserQuestion"` (Fragetext + Options-Labels aus dem input), sonst `art="werkzeug"` mit `text = anzeige + kompakte Eingabe`
    - `{"typ": "fertig", "fehler": str | None, "kosten_usd": float | None}`
  - `claude_motor.py`: `class ClaudeMotor` implementiert das Protokoll. Konstruktor `ClaudeMotor(client_fabrik=None)` — `client_fabrik` ist injizierbar (Tests!); Default baut `ClaudeSDKClient(options=_optionen(self._can_use_tool))`. `_optionen()`:
    ```python
    def _optionen(can_use_tool) -> "ClaudeAgentOptions":
        repo = str(Path(__file__).resolve().parents[3])
        umgebung = {"PYTHONPATH": repo}
        return ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            cwd=repo,
            permission_mode="default",
            can_use_tool=can_use_tool,
            mcp_servers={
                "bestand": {"command": sys.executable, "args": ["-m", "bestand.server"],
                             "env": {**umgebung, "BESTAND_DB": os.environ.get("BESTAND_DB",
                                 str(Path.home() / ".hardware-copilot/bestand.db"))}},
                "wissensschicht": {"command": sys.executable, "args": ["-m", "wissensschicht.server"],
                             "env": {**umgebung, "WISSENSSCHICHT_REPO": os.environ.get("WISSENSSCHICHT_REPO",
                                 str(Path.home() / "projects/hardware-wissen"))}},
            },
            allowed_tools=["mcp__bestand", "mcp__wissensschicht"],
        )
    ```
    (`allowed_tools`-Präfixform beim Implementieren gegen das SDK verifizieren; falls Einzeltools nötig sind, alle 6+8 Toolnamen ausschreiben.)
    `SYSTEM_PROMPT` (deutsch, kurz): Rolle „Elektronik-Werkstatt-Kopilot im Hardware-Copilot-Cockpit", Werkzeuge benennen (Bestand, Wissensschicht), Wissens-Grundsätze (Regel-Blöcke wörtlich durchreichen, Stufen nie hochstufen, ⚠ VERMUTUNG nie entfernen), Antworten kompakt, deutsch.
  - Rückfragen-Mechanik: `_can_use_tool(tool_name, input_data, context)` legt ein `asyncio.Future` in `self._offene_rueckfragen[id]` an, pusht das `rueckfrage`-Ereignis in die interne Ereignis-Queue und `await`et das Future; `rueckfrage_antworten()` löst es auf (`PermissionResultAllow(...)` bzw. `PermissionResultDeny(message=antwort or "Vom Nutzer abgelehnt")`; bei `art="frage"` mit Antworttext: Allow mit `updated_input` inkl. `answers`).
  - `frage(text)`: `await client.query(text)`, dann über `client.receive_response()` iterieren und in Ereignisse übersetzen: TextBlock→`text_haeppchen`; ToolUseBlock→`werkzeug_gestartet`; ToolResultBlock (in beliebigem Message-Typ mit `content`-Liste)→`werkzeug_fertig`; ResultMessage→`fertig` (fehler = None bei subtype=="success", sonst subtype; kosten aus total_cost_usd). Da die Rückfrage-Ereignisse aus dem Callback parallel entstehen, laufen ALLE Ereignisse über eine `asyncio.Queue`, die `frage()` konsumiert (Producer: Übersetzer-Task + Callback).
  - `abbrechen()` → `client.interrupt()`; `stop()` → Client-Kontext schließen; `start()` → Client verbinden (Context-Manager-Äquivalent, je nach SDK `connect()`).

- [ ] **Step 0:** `~/projects/hardware-copilot/.venv-wissen/bin/pip install claude-agent-sdk` und SDK-Symbole inspizieren (`python -c "from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock, ToolUseBlock, ToolResultBlock; print('ok')"`).

- [ ] **Step 1: Failing Tests schreiben** (`backend/tests/test_motor_kern.py`) — mit Fake-Client (kein echtes SDK-Objekt nötig, nur die Feldnamen der echten Typen nachbauen bzw. die echten Typen instanziieren, wenn trivial konstruierbar):

```python
"""Motor-Kern: SDK-Messages → neutrale Ereignisse; Rückfragen-Roundtrip."""
import asyncio

import pytest

from backend.app.motor.claude_motor import ClaudeMotor, uebersetze_bloecke, werkzeug_anzeige


def test_werkzeug_anzeige_zerlegt_mcp_namen():
    assert werkzeug_anzeige("mcp__bestand__teil_suchen") == "bestand: teil_suchen"
    assert werkzeug_anzeige("WebSearch") == "WebSearch"


class FakeText:
    def __init__(self, text): self.text = text
class FakeToolUse:
    def __init__(self, id, name, input): self.id, self.name, self.input = id, name, input
class FakeToolResult:
    def __init__(self, tool_use_id, is_error): self.tool_use_id, self.is_error = tool_use_id, is_error


def test_uebersetze_bloecke_liefert_ereignisse():
    ereignisse = list(uebersetze_bloecke([
        FakeText("Hallo"),
        FakeToolUse("t1", "mcp__bestand__teil_suchen", {"suchbegriff": "100nF"}),
        FakeToolResult("t1", False),
    ], werkzeug_namen={}))

    assert ereignisse[0] == {"typ": "text_haeppchen", "text": "Hallo"}
    assert ereignisse[1]["typ"] == "werkzeug_gestartet"
    assert ereignisse[1]["anzeige"] == "bestand: teil_suchen"
    assert ereignisse[2] == {"typ": "werkzeug_fertig", "id": "t1",
                             "name": "mcp__bestand__teil_suchen", "fehler": False}


@pytest.mark.asyncio
async def test_rueckfrage_roundtrip_erlaubt():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)

    async def frage_stellen():
        return await motor._can_use_tool("Bash", {"command": "ls"}, None)

    aufgabe = asyncio.create_task(frage_stellen())
    ereignis = await asyncio.wait_for(motor._queue.get(), timeout=2)
    assert ereignis["typ"] == "rueckfrage"
    assert ereignis["art"] == "werkzeug"

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=True, antwort=None)
    ergebnis = await asyncio.wait_for(aufgabe, timeout=2)
    assert type(ergebnis).__name__ == "PermissionResultAllow"


@pytest.mark.asyncio
async def test_rueckfrage_ablehnen_traegt_nachricht():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)
    aufgabe = asyncio.create_task(motor._can_use_tool("Bash", {"command": "rm -rf"}, None))
    ereignis = await motor._queue.get()

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=False, antwort="zu riskant")
    ergebnis = await aufgabe
    assert type(ergebnis).__name__ == "PermissionResultDeny"
    assert "zu riskant" in ergebnis.message
```

(pytest-asyncio nötig: `pip install pytest-asyncio` in Step 0 mitinstallieren; `asyncio_mode=auto` in einer `backend/tests/pytest.ini` oder Marker wie gezeigt.)

- [ ] **Step 2: rot laufen lassen**, dann **Step 3: Implementierung** gemäß Interfaces-Block. `uebersetze_bloecke(bloecke, werkzeug_namen)` ist eine pure Funktion (testbar ohne Session): mappt Block-Objekte per Duck-Typing (`hasattr(b, "text")` → Text; `hasattr(b, "input")` → ToolUse; `hasattr(b, "tool_use_id")` → ToolResult; `werkzeug_namen` dict id→name füllt den Namen im fertig-Ereignis).

- [ ] **Step 4:** `pytest backend/tests/test_motor_kern.py -v` → 4 passed; danach kompletter Backend-Lauf grün (17 + 4 = 21).

- [ ] **Step 5: Commit** — `E4: Motor-Schnittstelle + Claude-Motor-Kern (Ereignis-Übersetzung, Rückfragen)`

---

### Task 2: WebSocket-Router `/motor/ws`

**Files:**
- Create: `backend/app/motor/router.py`
- Modify: `backend/app/main.py` (Router einbinden), `backend/requirements.txt` (`claude-agent-sdk`, `websockets`-Extra falls nötig — uvicorn[standard] kann WS)
- Test: `backend/tests/test_motor_router.py`

**Interfaces:**
- Consumes: `Motor`-Protokoll (Task 1); der echte `ClaudeMotor` wird per Modul-Fabrik `_motor_fabrik` erzeugt — in Tests durch einen `FakeMotor` ersetzt (`router.motor_fabrik = ...`).
- Produces: WS-Endpunkt `/motor/ws`:
  - Bei Connect: zuerst alle Ereignisse aus dem Sitzungs-Verlauf (`{"typ": "verlauf", "ereignisse": [...]}`), dann live.
  - Client→Server-Nachrichten: `{"typ": "nutzer", "text"}` (startet `frage()`-Task, Ereignisse gehen an alle verbundenen Clients und in den Verlauf; parallele zweite Anfrage während eine läuft → `{"typ": "fertig", "fehler": "beschäftigt — bitte warten"}` nur an den Sender), `{"typ": "rueckfrage_antwort", "id", "erlaubt", "antwort"}`, `{"typ": "abbrechen"}`, `{"typ": "neustart"}` (Motor stoppen, Verlauf leeren, neuen Motor via Fabrik).
  - Nutzer-Nachrichten landen auch im Verlauf als `{"typ": "nutzer", "text"}` (damit Reconnect den Dialog zeigt).
  - Ein Motor, lazily beim ersten Connect gestartet; Fehler beim Start → `fertig`-Ereignis mit Fehlertext.

- [ ] **Step 1: Failing Tests** (`backend/tests/test_motor_router.py`) — FastAPI TestClient `websocket_connect`, FakeMotor liefert ein festes Ereignis-Skript:

```python
"""Motor-Router: Verlauf, Dialog-Roundtrip, neustart — mit Fake-Motor."""
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.motor import router as motor_router


class FakeMotor:
    def __init__(self):
        self.rueckfragen = []
        self.gestoppt = False

    async def start(self):
        pass

    async def frage(self, text):
        yield {"typ": "text_haeppchen", "text": f"Echo: {text}"}
        yield {"typ": "fertig", "fehler": None, "kosten_usd": 0.01}

    async def rueckfrage_antworten(self, rueckfrage_id, erlaubt, antwort):
        self.rueckfragen.append((rueckfrage_id, erlaubt, antwort))

    async def abbrechen(self):
        pass

    async def stop(self):
        self.gestoppt = True


def test_dialog_und_verlauf(monkeypatch):
    monkeypatch.setattr(motor_router, "motor_fabrik", FakeMotor)
    motor_router.zustand_zuruecksetzen()
    client = TestClient(app)

    with client.websocket_connect("/motor/ws") as ws:
        assert ws.receive_json()["typ"] == "verlauf"
        ws.send_json({"typ": "nutzer", "text": "Hallo"})
        assert ws.receive_json() == {"typ": "text_haeppchen", "text": "Echo: Hallo"}
        assert ws.receive_json()["typ"] == "fertig"

    # Reconnect: Verlauf enthält Nutzer-Zeile + beide Ereignisse
    with client.websocket_connect("/motor/ws") as ws:
        verlauf = ws.receive_json()
        typen = [e["typ"] for e in verlauf["ereignisse"]]
        assert typen == ["nutzer", "text_haeppchen", "fertig"]


def test_neustart_leert_verlauf(monkeypatch):
    monkeypatch.setattr(motor_router, "motor_fabrik", FakeMotor)
    motor_router.zustand_zuruecksetzen()
    client = TestClient(app)

    with client.websocket_connect("/motor/ws") as ws:
        ws.receive_json()
        ws.send_json({"typ": "nutzer", "text": "eins"})
        ws.receive_json(); ws.receive_json()
        ws.send_json({"typ": "neustart"})
        assert ws.receive_json() == {"typ": "verlauf", "ereignisse": []}
```

- [ ] **Step 2: rot**, **Step 3: Implementierung** (`router.py`: Modulzustand `_motor`, `_verlauf: list[dict]`, `_clients: set[WebSocket]`, `_laufende_frage: asyncio.Task | None`; Hilfen `zustand_zuruecksetzen()` für Tests, `_sende_an_alle(ereignis)` mit Verlauf-Append; `motor_fabrik = ClaudeMotor`). In `main.py`: `from .motor import router as motor_router` + `app.include_router(motor_router.router)`; requirements + `claude-agent-sdk` ergänzen.

- [ ] **Step 4:** Backend-Gesamtlauf → 21 + 2 = 23 passed (plus bestehende 46+51 unverändert).

- [ ] **Step 5: Commit** — `E4: Motor-WebSocket — Verlauf, Rückfragen-Roundtrip, Neustart`

---

### Task 3: Frontend Motor-Client (`src/api/motor.ts`)

**Files:**
- Create: `src/types/motor.ts`, `src/api/motor.ts`
- Test: `src/api/motor.test.ts`

**Interfaces:**
- Produces: Typen `MotorEreignis` (Discriminated Union über `typ` gemäß Wire-Format inkl. `verlauf` und `nutzer`) und Klasse `MotorVerbindung`:
  - `new MotorVerbindung(aufEreignis: (e: MotorEreignis) => void)` — verbindet auf `ws://<API-Host>/motor/ws` (aus `API_BASE_URL` abgeleitet: `http`→`ws`), reconnect mit 2-s-Backoff bei Abbruch.
  - `senden(text)`, `rueckfrageAntworten(id, erlaubt, antwort?)`, `abbrechen()`, `neustart()`, `schliessen()`.
- Test mit gemocktem `WebSocket` (globales Stub-Klasse mit `send`/`close` + manuell feuerbaren `onmessage`/`onopen`): prüft URL-Ableitung (`ws://127.0.0.1:8000/motor/ws`), dass `senden` das JSON `{typ:"nutzer",...}` schreibt und eingehende Nachrichten als geparste Ereignisse beim Callback landen.

- [ ] Steps: Test rot → Implementierung → `npx vitest run` grün (bisherige 8 + 2 neue) → `npm run build` grün → Commit `E4: Motor-Client (WebSocket) + Ereignis-Typen`

---

### Task 4: ChatPanel + Live-Spiegel

**Files:**
- Create: `src/components/panels/ChatPanel.tsx`
- Modify: `src/components/layout/AppShell.tsx` (dritter Tab `chat` „Chat"), `src/components/panels/BestandPanel.tsx` (Live-Spiegel-Listener)
- Test: `src/components/panels/ChatPanel.test.tsx`

**Interfaces / Verhalten (bindend):**
- Nachrichtenliste: Nutzer-Nachrichten rechtsbündig (dunkle Bubble #27272a); Claude-Text läuft inkrementell zusammen (aufeinanderfolgende `text_haeppchen` an denselben Absatz anhängen, bis ein anderes Ereignis kommt); Werkzeug-Ereignisse als kompakte Zeile `⚙ bestand: teil_suchen` (gedämpft), bei `werkzeug_fertig` mit `fehler:true` → `⚠` rot; `fertig` mit Fehler → rote Zeile, mit `kosten_usd` → dezente Zeile `— fertig (0,01 $)`.
- Rückfrage-Karte (`rueckfrage`): Rahmen #facc15; bei `art="werkzeug"`: Text + Knöpfe „Erlauben"/„Ablehnen" (Ablehnen öffnet optionales Begründungsfeld); bei `art="frage"`: Fragetext + Options-Knöpfe (Label sendet als Antworttext) + Freitextfeld. Antwort → `rueckfrageAntworten`, Karte wird zu einer gedämpften Zeile „beantwortet: …".
- Eingabezeile unten: Textfeld (Enter sendet, Shift+Enter Zeilenumbruch), Senden-Knopf, „Stopp"-Knopf (abbrechen) nur sichtbar während eine Antwort läuft (zwischen gesendeter Nutzer-Nachricht und `fertig`), „Neu starten"-Knopf (mit confirm()).
- `verlauf`-Ereignis ersetzt die komplette Liste (Reconnect).
- **Live-Spiegel:** bei `werkzeug_fertig` mit `name.startsWith("mcp__bestand")` → `window.dispatchEvent(new CustomEvent("bestand-geaendert"))`. BestandPanel: `useEffect` mit Listener auf `bestand-geaendert` → `laden()` (und Klassen neu laden).
- Tests (gemockte MotorVerbindung via vi.mock von `../../api/motor`): (1) text_haeppchen sammeln sich zu einem Absatz und Nutzer-Nachricht erscheint; (2) rueckfrage-Karte rendert Knöpfe und ruft `rueckfrageAntworten(id, true, ...)` bei „Erlauben"; (3) werkzeug_fertig mit bestand-Name dispatcht `bestand-geaendert` (Listener-Spy).

- [ ] Steps: Tests rot → Implementierung (~250 Zeilen, Bauart/Stil wie die anderen Panels) → `npx vitest run` grün (10 + 3) → `npm run build` grün → Commit `E4: Chat-Panel mit Rückfrage-Karten und Live-Spiegel auf das Bestand-Panel`

---

### Task 5: README + Doku

**Files:**
- Modify: `README.md` (Chat-Zeile im Cockpit-Absatz + Hinweis Auth: „Der Chat nutzt dieselbe Anmeldung wie Claude Code — ist ANTHROPIC_API_KEY gesetzt, wird darüber abgerechnet; für Abo-Betrieb die Variable nicht setzen"), `bestand/README.md` unberührt.
- Kein neuer Code. Commit `E4: README — Chat-Betrieb und Auth-Hinweis`

---

### Task 6: Gate-Lauf E4 + Abschluss

Ende-zu-Ende mit ECHTER Claude-Session (einmalig, kleine Anfrage — Kosten bewusst in Kauf genommen):

- [ ] **Step 1:** Backend mit Gate-DB starten (`BESTAND_DB=$CLAUDE_JOB_DIR/tmp/gate-e4.db uvicorn backend.app.main:app`), Gate-DB vorab mit 2–3 Teilen befüllen (direkt über `BestandsDienst`), `npm run build && npx vite preview --port 4173`.
- [ ] **Step 2:** Headless-Browser (playwright-core auf `~/.cache/ms-playwright/chrome-current`, wie Gate E2): Chat-Tab → Anfrage eintippen, z. B. „Welche 100-nF-Kondensatoren habe ich im Bestand, und welche Wissensschicht-Regel gilt für deren Platzierung? Buche danach 2 Stück ab." → warten bis `fertig` (Timeout großzügig, ≥ 180 s) → prüfen: Werkzeug-Zeilen für bestand+wissensschicht erschienen, Antwort enthält Regel mit Stufe, Bestand-Tab zeigt die reduzierte Menge OHNE manuelles Neuladen (Live-Spiegel). Screenshots (Chat + Bestand).
- [ ] **Step 3:** Befund in `bestand/README.md`-Stil dokumentieren (Abschnitt „Gate-Lauf E4" im Repo-Root-README oder eigener docs-Vermerk), committen: `E4: Gate-Lauf dokumentiert — echte Anfrage läuft komplett in der App`.
- Hinweis Transparenz: Der KiCad-Teil (Konnect) ist bewusst nicht Teil des Gates — auf dem Entwicklungsrechner ohne KiCad nicht prüfbar; Konnect-Anbindung des Motors = Folgeschritt (ein `mcp_servers`-Eintrag bzw. `setting_sources`), im PR als Follow-up notieren.

Danach (Controller): Whole-Branch-Review (stärkstes Modell) über `5345835..HEAD`, Fixes, push, Draft-PR (Base `cockpit/e2-panels`).

---

## Self-Review (beim Schreiben)

- Spec §3.5 abgedeckt: 5 Ereignistypen ✓ (T1), WebSocket-Dauerverbindung ✓ (T2), Werkzeug-Zeilen kompakt ✓ (T4), Rückfragen (Heikel/Rechte) im Chat ✓ (T1/T4), Motor 1 = Agent SDK mit denselben MCP-Servern ✓ (T1), „kein Claude-spezifisches Feld in der Schnittstelle" ✓ (T1-Konstante geprüft), Panels spiegeln live ✓ (T4 Live-Spiegel + Gate-Prüfung).
- Kein Test startet eine echte Session (T1 Fake-Client, T2 FakeMotor, T3/T4 gemockter WS) — nur das Gate.
- Risiken benannt: allowed_tools-Präfixform, SDK-Symbolabweichungen, ToolResult-Trägertyp → Verifikationsanweisungen in Global Constraints/T1.
