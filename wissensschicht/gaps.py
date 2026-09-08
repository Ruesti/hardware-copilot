"""C6-Lückenprotokoll: Fragen ohne belegte Regel landen als Zeile in luecken.md.

Jeder Eintrag ist Kandidat für eine neue Regel mit Quelle (Phase-3-Mechanik).
"""
from __future__ import annotations

from pathlib import Path

_KOPF = (
    "# Lücken-Protokoll (C6)\n\n"
    "Fragen, zu denen nichts Belegtes vorliegt. "
    "Jeder Eintrag ist Kandidat für eine neue Regel mit Quelle.\n\n"
    "| Datum | Frage/Thema | Warum offen | Status |\n"
    "|---|---|---|---|\n"
)


def report_gap(pfad: Path, frage: str, grund: str, datum: str) -> None:
    pfad = Path(pfad)
    if not pfad.exists():
        pfad.write_text(_KOPF)
    with pfad.open("a") as f:
        f.write(f"| {datum} | {frage} | {grund} | offen |\n")


def list_gaps(pfad: Path) -> list[dict]:
    pfad = Path(pfad)
    if not pfad.exists():
        return []
    eintraege = []
    for zeile in pfad.read_text().splitlines():
        zeile = zeile.strip()
        if not zeile.startswith("|") or zeile.startswith("| Datum") or set(zeile) <= {"|", "-", " "}:
            continue
        teile = [t.strip() for t in zeile.strip("|").split("|")]
        if len(teile) == 4:
            eintraege.append({"datum": teile[0], "frage": teile[1],
                              "grund": teile[2], "status": teile[3]})
    return eintraege
