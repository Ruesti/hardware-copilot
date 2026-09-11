"""KiCad-Systemstatus und Installations-Anstoß auf dem lokalen Rechner.

Die App (Tauri) und dieses Backend laufen auf demselben Rechner — der Status
beschreibt also die Maschine, auf der auch exportiert und geöffnet wird.

Portiert aus feat/kicad-export; in E6 noch unverdrahtet.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .pcb import pcbnew_available

SYMBOLS_DIR = Path("/usr/share/kicad/symbols")

INSTALL_CMD = ["apt-get", "install", "-y", "--no-install-recommends",
               "kicad", "kicad-symbols", "kicad-footprints"]
MANUAL_HINT = ("sudo apt update && sudo apt install -y --no-install-recommends "
               "kicad kicad-symbols kicad-footprints")


def kicad_status() -> dict:
    cli = shutil.which("kicad-cli")
    version = None
    if cli:
        try:
            version = subprocess.run(
                [cli, "version"], capture_output=True, text=True, timeout=30,
            ).stdout.strip()
        except Exception:
            pass
    installed = bool(cli) and SYMBOLS_DIR.exists()
    return {
        "installed": installed,
        "version": version,
        "gui": bool(shutil.which("kicad")),
        "symbols": SYMBOLS_DIR.exists(),
        "pcbnew": pcbnew_available() if installed else False,
        "installHint": None if installed else MANUAL_HINT,
    }


def start_install() -> dict:
    """Startet die Installation über den grafischen Admin-Dialog (pkexec).

    Ohne pkexec/Display bleibt nur die Anleitung — der Aufrufer zeigt sie an.
    """
    import os

    if kicad_status()["installed"]:
        return {"started": False, "reason": "KiCad ist bereits installiert."}
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    pkexec = shutil.which("pkexec")
    if not (has_display and pkexec):
        return {
            "started": False,
            "reason": "Automatische Installation hier nicht möglich — bitte im "
                      "Terminal ausführen:",
            "command": MANUAL_HINT,
        }
    script = "apt-get update && " + " ".join(INSTALL_CMD)
    subprocess.Popen(
        [pkexec, "sh", "-c", script],
        start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return {"started": True,
            "reason": "Installation gestartet — Admin-Dialog beachten. "
                      "Der Status aktualisiert sich automatisch."}
