from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

import anthropic

MODEL = "claude-sonnet-4-6"

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
            parts.append(f"- **{b['name']}** ({b['trust_level']}): {b['description']}")

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
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return json.loads(text.strip())


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


def suggest_components(context: dict[str, Any]) -> list[dict[str, Any]]:
    client = _get_client()
    ctx_text = _build_context_block(context)

    prompt = f"""{ctx_text}

For each design block listed above, suggest 1–3 specific real-world components. Return a JSON array:
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
    "trust_level": "parsed"
  }}
]

Return ONLY the JSON array, no markdown fences, no explanation."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json_response(response.content[0].text)


def draft_circuit(context: dict[str, Any]) -> dict[str, Any]:
    client = _get_client()
    ctx_text = _build_context_block(context)

    prompt = f"""{ctx_text}

Design a complete circuit block architecture based on the requirements above.
Return a JSON object:
{{
  "summary": "brief description of the overall circuit",
  "blocks": [
    {{
      "name": "block name",
      "description": "what this block does and key design parameters",
      "trust_level": "parsed"
    }}
  ]
}}

Return ONLY the JSON, no markdown fences, no explanation."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json_response(response.content[0].text)


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
    return response.content[0].text
