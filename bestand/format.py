"""Ausgabeformate des Bestands: Kurzzeile (Suche) und Markdown-Detail.

Grundsatz aus der Spec (§6): Preise nie ohne Datum ausgeben — jede Preiszeile
trägt „Stand vom <datum>“.
"""
from __future__ import annotations


def kurzzeile(teil: dict) -> str:
    fach = f"Fach {teil['fach']}" if teil["fach"] else "kein Fach zugewiesen"
    klasse = f"Klasse {teil['klasse']}" if teil["klasse"] else "ohne Klasse"
    return (f"[T-{teil['id']}] {teil['bezeichnung']} — Menge {teil['menge']}, "
            f"{fach}, {klasse}")


def detail(teil: dict, alternativen: list[dict], preise: list[dict]) -> str:
    zeilen = [f"### [T-{teil['id']}] {teil['bezeichnung']}",
              kurzzeile(teil)]
    if teil["hersteller_nr"]:
        zeilen.append(f"Hersteller-Nr: {teil['hersteller_nr']}")
    if teil["eckdaten"]:
        zeilen.append(f"Eckdaten: {teil['eckdaten']}")
    if teil["datenblatt_url"]:
        zeilen.append(f"Datenblatt: {teil['datenblatt_url']}")

    if alternativen:
        zeilen.append("Alternativen:")
        zeilen += [f"- {a['bezeichnung']} ({a['hersteller_nr']}) — "
                   f"{a['hinweis']} (vermerkt {a['datum']})" for a in alternativen]
    else:
        zeilen.append("Alternativen: keine vermerkt")

    if preise:
        zeilen.append("Preise (veralten — Datum beachten):")
        for p in preise:
            zeile = (f"- {p['preis_eur']:.4g} € bei {p['quelle']} — "
                     f"Stand vom {p['datum']}")
            if p["url"]:
                zeile += f" — {p['url']}"
            zeilen.append(zeile)
    else:
        zeilen.append("Preise: keine im Cache")
    return "\n".join(zeilen)
