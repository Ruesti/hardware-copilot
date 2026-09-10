"""Leucht-Regal ansteuern: genau ein HTTP-Befehl, mehr kann das Regal nicht (Spec §3.3).

Die Zuordnung Teil→Fach→LED kennt nur die DB; hier wird nur gesendet.
"""
from __future__ import annotations

import json
import urllib.request


def sende(url: str, befehl: dict) -> None:
    """POST an die Regal-Firmware. Wirft OSError, wenn das Regal nicht antwortet."""
    anfrage = urllib.request.Request(
        url, data=json.dumps(befehl).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=3):
        pass
