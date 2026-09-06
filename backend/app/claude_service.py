from __future__ import annotations

import contextlib
import contextvars
import json
import os
from dataclasses import dataclass
from typing import Any, AsyncGenerator

import anthropic

MODEL = "claude-sonnet-4-6"


@dataclass
class UsageRecord:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_create_tokens: int = 0


_usage_sink: contextvars.ContextVar[list[UsageRecord] | None] = contextvars.ContextVar(
    "_usage_sink", default=None
)


def _record_usage_from_response(response: Any) -> None:
    sink = _usage_sink.get()
    if sink is None:
        return
    u = getattr(response, "usage", None)
    if u is None:
        return
    sink.append(
        UsageRecord(
            input_tokens=getattr(u, "input_tokens", 0) or 0,
            output_tokens=getattr(u, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_create_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )
    )


@contextlib.contextmanager
def capture_usage():
    """Context manager: alle Claude-Aufrufe innerhalb werden in eine Liste gesammelt."""
    sink: list[UsageRecord] = []
    token = _usage_sink.set(sink)
    try:
        yield sink
    finally:
        _usage_sink.reset(token)

SYSTEM_PROMPT = """You are an expert electronics engineer and PCB design consultant — the Hardware Copilot. You help design embedded systems, power electronics, and IoT devices.

You provide precise, technically accurate answers with:
- Specific component recommendations including MPN numbers, manufacturers, packages
- Trust levels: new → parsed (AI-suggested) → reviewed → validated → proven → trusted_template
- Power budget analysis, protection circuits, EMC considerations
- Schematic topology recommendations

Keep responses concise and technical. Use markdown for structure."""


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def _get_async_client() -> anthropic.AsyncAnthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.AsyncAnthropic(api_key=api_key)


def _build_context_block(context: dict[str, Any]) -> str:
    parts: list[str] = [
        f"## Active Project: {context.get('name', 'Unknown')}",
        f"Phase: {context.get('phase', 'Draft')}",
    ]

    requirements = context.get("requirements", [])
    if requirements:
        parts.append("\n### Requirements")
        for r in requirements:
            parts.append(f"- [{r['status']}] **{r['title']}**: {r['description']}")

    blocks = context.get("blocks", [])
    if blocks:
        parts.append("\n### Design Blocks")
        for b in blocks:
            parts.append(
                f"- id={b['id']} **{b['name']}** ({b['trust_level']}): {b['description']}"
            )

    components = context.get("components", [])
    if components:
        parts.append("\n### Components")
        for c in components:
            mpn = f" MPN:{c['mpn']}" if c.get("mpn") else ""
            mfr = f" ({c['manufacturer']})" if c.get("manufacturer") else ""
            ctype = f" [{c['type']}]" if c.get("type") else ""
            parts.append(
                f"- **{c['name']}**{ctype}{mpn}{mfr} trust:{c['trust_level']} — {c['description']}"
            )

    return "\n".join(parts)


def _parse_json_response(text: str) -> Any:
    raw = text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:])
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
    raw = raw.strip()

    # Falls der LLM Klartext vor dem JSON ausgegeben hat, das erste { oder [
    # bis zum dazu passenden Ende heraussuchen.
    if raw and raw[0] not in "{[":
        first = -1
        for ch in ("{", "["):
            idx = raw.find(ch)
            if idx != -1 and (first == -1 or idx < first):
                first = idx
        if first > 0:
            raw = raw[first:]

    if not raw:
        # Leerer LLM-Response → leeres JSON-Objekt liefern statt 502
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        repaired = _repair_truncated_json(raw)
        if repaired is not None:
            return repaired
        raise


def _repair_truncated_json(raw: str) -> Any | None:
    """Versucht, ein abgeschnittenes JSON-Array/-Objekt auf das letzte vollständige
    Element zu kürzen. Gibt None zurück, wenn keine Reparatur möglich ist."""
    raw = raw.strip()
    if raw.startswith("["):
        # Schneide am letzten "}," ab und schließe das Array
        last_close = raw.rfind("}")
        if last_close == -1:
            return None
        candidate = raw[: last_close + 1] + "]"
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    if raw.startswith("{"):
        # Versuche, fehlende Klammern am Ende zu schließen
        open_curly = raw.count("{")
        close_curly = raw.count("}")
        open_sq = raw.count("[")
        close_sq = raw.count("]")
        candidate = raw + "]" * (open_sq - close_sq) + "}" * (open_curly - close_curly)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None


async def stream_chat(
    history: list[dict[str, str]],
    user_message: str,
    context: dict[str, Any],
) -> AsyncGenerator[str, None]:
    client = _get_async_client()
    system = SYSTEM_PROMPT + "\n\n" + _build_context_block(context)

    messages = [*history, {"role": "user", "content": user_message}]

    async with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
        try:
            final = await stream.get_final_message()
            _record_usage_from_response(final)
        except Exception:
            pass


INTERVIEW_SYSTEM_PROMPT = """Du bist Hardware Copilot im Interview-Modus. Deine Aufgabe: Erfasse die Anforderungen für ein Hardwareprojekt durch gezielte Einzelfragen.

Regeln:
- Stelle GENAU EINE kurze Frage pro Antwort (max 2 Sätze)
- Frage der Reihe nach: Funktion/Zweck → Versorgungsspannung → Schnittstellen → Umgebung/Temperatur → Gehäuse/Formfaktor → Stückzahl
- Wenn du aus der Antwort des Users eine klare Anforderung ableiten kannst, füge am ENDE deiner Antwort (nach einem Zeilenumbruch) exakt diesen XML-Tag ein — ohne Markdown, ohne Kommentare:
  <req title="Kurztitel max 5 Wörter" description="Vollständige technische Beschreibung der Anforderung"/>
- Nur einen <req/> Tag pro Antwort
- Nie denselben Aspekt zweimal fragen"""


async def interview_chat(
    history: list[dict[str, str]],
    user_message: str,
    context: dict[str, Any],
) -> AsyncGenerator[str, None]:
    client = _get_async_client()
    system = INTERVIEW_SYSTEM_PROMPT + "\n\n" + _build_context_block(context)

    messages = [*history, {"role": "user", "content": user_message}]

    async with client.messages.stream(
        model=MODEL,
        max_tokens=400,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
        try:
            final = await stream.get_final_message()
            _record_usage_from_response(final)
        except Exception:
            pass


def suggest_components(context: dict[str, Any]) -> list[dict[str, Any]]:
    # Ohne Blöcke kein sinnvoller LLM-Call.
    blocks = context.get("blocks", []) or []
    if not blocks:
        return []

    client = _get_client()
    ctx_text = _build_context_block(context)

    existing_mpns = {c.get("mpn") for c in context.get("components", []) if c.get("mpn")}
    skip_hint = ""
    if existing_mpns:
        skip_hint = "\nBereits vorhandene MPNs (nicht erneut vorschlagen): " + ", ".join(sorted(existing_mpns))

    prompt = f"""{ctx_text}{skip_hint}

Schlage für jeden Block ohne Komponenten 1–6 reale Bauteile vor. Halte die Antwort kompakt; max 30 Bauteile insgesamt.
Blöcke, die bereits Komponenten haben, NICHT erneut vorschlagen.

Wichtige Regel für ICs/MCUs (mcu, power_ic, sensor, memory): Liefere NICHT NUR das Haupt-IC,
sondern auch die zwingende Grundbeschaltung als separate Bauteile im SELBEN Block:
- Decoupling-Caps (z. B. 100 nF + 10 µF an Vcc-Pins)
- Pull-up/Pull-down-Widerstände (EN, Reset, Boot-Strapping bei ESP32 GPIO0/GPIO2/GPIO15)
- Reset-Schaltung (RC oder dedizierter Supervisor)
- Externer Oszillator/Crystal, falls vom IC gefordert
- USB-/UART-Bridge inkl. Pull-ups, falls Programmierung/Debug nötig
- Strommessshunts, Schutzdioden, Ferritperlen wenn anwendungsrelevant

Vergib jedem Bauteil das richtige `block_name`, nicht alle ans Haupt-IC.

Return a JSON array:
[
  {{
    "block_name": "exact block name from above",
    "name": "component full name",
    "type": "one of: mcu, power_ic, diode, transistor, passive_resistor, passive_capacitor, passive_inductor, sensor, connector, protection, memory, crystal, other",
    "value": "e.g. 100nF or null",
    "package": "e.g. SOT-23, SOIC-8",
    "manufacturer": "manufacturer name",
    "mpn": "manufacturer part number",
    "description": "one-line description",
    "trust_level": "parsed",
    "net_role": "for passives/protection parts ONLY - structured net semantics, one of: \"decoupling\" | \"pullup:<ROLE>\" | \"pulldown:<ROLE>\" | \"series:<ROLE>\" | \"protect:<ROLE>\" | \"prog_resistor\" | null. <ROLE> is the logical net the part attaches to: SDA, SCL, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, USB_DP, USB_DN, CC1, CC2, EN, BOOT, STAT. Examples: I2C pull-up on SDA -> \"pullup:SDA\"; decoupling cap -> \"decoupling\"; series resistor in SPI clock -> \"series:SPI_CLK\"; ESD diode on USB D+ -> \"protect:USB_DP\"; MCP73831 PROG resistor -> \"prog_resistor\". For ICs and connectors: null."
  }}
]

Return ONLY the JSON array, no markdown fences, no explanation."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    raw_text = response.content[0].text
    try:
        result = _parse_json_response(raw_text)
    except json.JSONDecodeError as exc:
        snippet = raw_text[:400].replace("\n", " ")
        raise ValueError(
            f"LLM lieferte kein gültiges JSON ({exc.msg}). Anfang der Antwort: {snippet!r}"
        ) from exc
    return result if isinstance(result, list) else []


def draft_circuit(context: dict[str, Any]) -> dict[str, Any]:
    # Ohne Anforderungen kein LLM-Aufruf — spart Tokens und vermeidet "Keine Antwort möglich"-Klartext.
    requirements = context.get("requirements", []) or []
    if not requirements:
        return {
            "summary": "Keine Anforderungen vorhanden — bitte zuerst im Chat Anforderungen erfassen.",
            "blocks": [],
            "remove_block_ids": [],
        }

    client = _get_client()
    ctx_text = _build_context_block(context)

    prompt = f"""{ctx_text}

Aufgabe: Pflege die Block-Architektur dieser Schaltung minimal und präzise basierend auf den AKTUELLEN Anforderungen.

Strikte Regeln:
- Schlage NUR Blöcke vor, die für die Erfüllung mindestens einer expliziten Anforderung zwingend nötig sind.
- Keine spekulativen Erweiterungen (kein Bluetooth, kein USB, keine Debug-LEDs, kein Display, keine Sensoren — wenn nicht ausdrücklich gefordert).
- Lieber zu wenig als zu viel. Fehlende Blöcke ergänzt der User später manuell.
- Vorhandene Blöcke (oben unter "Design Blocks") sollst du NICHT umbenennen oder duplizieren. Wenn ein bestehender Block die Anforderung schon abdeckt, lasse ihn aus dem `blocks`-Output weg.
- Wenn ein bestehender Block durch geänderte Anforderungen überflüssig wird, trage seine `id` in `remove_block_ids` ein.

Antworte als JSON-Objekt:
{{
  "summary": "ein Satz Zusammenfassung",
  "blocks": [
    {{
      "name": "Blockname (kurz, deutsch oder englisch konsistent)",
      "description": "Was der Block tut + wichtigste Parameter (Spannung, Strom, Schnittstelle)",
      "trust_level": "parsed"
    }}
  ],
  "remove_block_ids": ["blk-xxxx", ...]
}}

`blocks` enthält NUR neue Blöcke (nicht die bestehenden). `remove_block_ids` darf leer sein.
Gib ausschließlich JSON zurück, keine Markdown-Fences, keine Erklärung. Wenn keine Änderung nötig ist, antworte mit `{{"summary":"keine Änderung","blocks":[],"remove_block_ids":[]}}`."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    raw_text = response.content[0].text
    try:
        return _parse_json_response(raw_text)
    except json.JSONDecodeError as exc:
        # Den Rohtext für Debugging in die Exception einbauen
        snippet = raw_text[:400].replace("\n", " ")
        raise ValueError(
            f"LLM lieferte kein gültiges JSON ({exc.msg}). Anfang der Antwort: {snippet!r}"
        ) from exc


def analyze_datasheet(pdf_text: str, filename: str) -> dict[str, Any]:
    client = _get_client()

    prompt = f"""Analyze this component datasheet: {filename}

Extract information and return as JSON:
{{
  "component_name": "string",
  "manufacturer": "string",
  "mpn": "string",
  "type": "one of: mcu, power_ic, diode, transistor, passive_resistor, passive_capacitor, passive_inductor, sensor, connector, protection, memory, crystal, other",
  "description": "one-line description",
  "package": "string or null",
  "supply_voltage": "string or null",
  "max_current": "string or null",
  "operating_temp": "string or null",
  "key_features": ["string"],
  "pinout": {{"pin_name": "function description"}},
  "absolute_max_ratings": {{"parameter": "value"}},
  "typical_application": "description of typical application circuit"
}}

Datasheet text (truncated to 8000 chars):
{pdf_text[:8000]}

Return ONLY the JSON, no markdown fences."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    try:
        return _parse_json_response(response.content[0].text)
    except Exception:
        return {"raw_analysis": response.content[0].text}


def validate_design(context: dict[str, Any]) -> list[dict[str, Any]]:
    client = _get_client()
    ctx_text = _build_context_block(context)

    prompt = f"""{ctx_text}

Review this hardware design and return a JSON array of validation issues:
[
  {{
    "severity": "info|warning|error|review_required",
    "title": "short title",
    "message": "detailed explanation and recommendation",
    "related_kind": "requirement|block|component|null",
    "related_id": "id string or null"
  }}
]

Check for:
- Blocks without any assigned components
- Requirements not covered by any block
- Components with low trust_level in critical paths (power, protection)
- Missing protection circuits (reverse polarity, overvoltage, ESD)
- Missing decoupling or bulk capacitors
- Incomplete power budget
- EMC concerns

If the design looks complete, return an empty array [].
Return ONLY the JSON array, no markdown fences."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    try:
        return _parse_json_response(response.content[0].text)
    except Exception:
        return [
            {
                "severity": "error",
                "title": "Validation parse error",
                "message": response.content[0].text[:500],
                "related_kind": None,
                "related_id": None,
            }
        ]


def suggest_connections(context: dict[str, Any]) -> list[dict[str, Any]]:
    client = _get_client()
    ctx_text = _build_context_block(context)

    prompt = f"""{ctx_text}

Based on the design blocks above, suggest the logical connections between them.
Consider: power rails, ground returns, digital buses, analog signals.

Return a JSON array:
[
  {{
    "source_block_name": "exact name of source block",
    "target_block_name": "exact name of target block",
    "label": "short signal label, e.g. '24V', 'GND', 'SDA/SCL', 'TX/RX', 'MISO/MOSI/SCK/CS'",
    "conn_type": "power|gnd|signal|i2c|spi|uart|custom"
  }}
]

Rules:
- source = the block that DRIVES or PROVIDES the signal/power
- target = the block that RECEIVES the signal/power
- Include a GND connection wherever relevant
- Only suggest connections that make technical sense
- Return ONLY the JSON array, no markdown fences."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    try:
        return _parse_json_response(response.content[0].text)
    except Exception:
        return []


def describe_block_circuit(block_name: str, block_description: str, components: list[dict[str, Any]]) -> str:
    client = _get_client()

    comp_list = "\n".join(
        f"- {c.get('name', '?')} {c.get('mpn', '')} ({c.get('type', '?')}, {c.get('package', '?')}): {c.get('description', '')}"
        for c in components
    ) or "No components assigned yet."

    prompt = f"""Design block: {block_name}
Description: {block_description}

Assigned components:
{comp_list}

Draw a compact ASCII schematic showing how these components connect inside this block.
Use standard ASCII art: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ for lines, labels for pins/nets.
Show: input pins, output pins, key internal connections, decoupling caps if relevant.
Keep it under 30 lines. Be precise and technically correct.
Return ONLY the ASCII schematic, no explanation."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage_from_response(response)
    return response.content[0].text
