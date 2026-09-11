"""Routing-Anleitung aus der Wissensbasis (E6 Task 4).

Einzige Quelle ist das Wissens-Repo (Regeln aus `wissensschicht.store.load_rules`,
heikle Bereiche aus `wissensschicht.heikel`) — hier wird nichts erfunden oder
hochgestuft. Stufe, Stärke, Aussage, Begründung und Zitat kommen unverändert
aus den Regel-Dateien; dieses Modul filtert nur nach den Bauteilklassen der
Projekt-Stückliste und macht daraus eine lesbare HTML-Anleitung.
"""
from __future__ import annotations

import html
from pathlib import Path

from wissensschicht.heikel import lade_heikel, pruefe_heikel
from wissensschicht.store import load_rules

_BADGES = {
    "belegt": ("BELEGT", "badge-belegt"),
    "vermutung": ("⚠ VERMUTUNG", "badge-vermutung"),
    "verifiziert": ("VERIFIZIERT", "badge-verifiziert"),
}

_QUELLE_FELDER = ("typ", "titel", "fundstelle", "url")


def _referenzen_je_klasse(projekt: dict) -> dict[str, list[str]]:
    """Referenzen der Positionen, gruppiert nach Klasse.

    Positionen ohne Klasse (leer oder Feld fehlt) werden übersprungen — sie
    tauchen später weder als Hinweis noch als ``ohne_regeln``-Eintrag auf.
    """
    zuordnung: dict[str, list[str]] = {}
    for position in projekt.get("positionen", []):
        klasse = position.get("klasse") or ""
        if not klasse:
            continue
        zuordnung.setdefault(klasse, []).append(position["referenz"])
    return {klasse: sorted(referenzen) for klasse, referenzen in zuordnung.items()}


def _quelle_zeile(quelle: dict) -> str:
    """Quelle-Zeile als Klartext-String — Daten aus der Regel, nur zusammengefasst."""
    teile = [quelle.get(feld, "") for feld in _QUELLE_FELDER]
    teile = [teil for teil in teile if teil]
    return " — ".join(teile) if teile else "keine Quelle"


def projekt_hinweise(projekt: dict, wissens_repo: Path) -> dict:
    """Regeln + heikle Bereiche, gefiltert auf die Bauteilklassen der BOM.

    `hinweise`: eine Regel-Karte je Regel, deren `geltung.klasse` unter den
    BOM-Klassen ist; `referenzen` sind die (sortierten) Positionsreferenzen
    dieser Klasse. `heikel`: heikle Bereiche, die eine der BOM-Klassen führen.
    `ohne_regeln`: BOM-Klassen ohne jeden Regel-Treffer.
    """
    refs_je_klasse = _referenzen_je_klasse(projekt)
    klassen = set(refs_je_klasse)

    hinweise = []
    getroffene_klassen: set[str] = set()
    for regel in sorted(load_rules(wissens_repo), key=lambda r: r.id):
        klasse = regel.geltung.get("klasse")
        if klasse not in klassen:
            continue
        getroffene_klassen.add(klasse)
        hinweise.append({
            "regel_id": regel.id,
            "stufe": regel.stufe,
            "staerke": regel.staerke,
            "aussage": regel.aussage,
            "begruendung": regel.begruendung,
            "quelle": _quelle_zeile(regel.quelle),
            "zitat": regel.quelle.get("zitat", ""),
            "referenzen": refs_je_klasse[klasse],
        })

    heikel_bereiche = pruefe_heikel(lade_heikel(wissens_repo), {"klasse": sorted(klassen)})
    heikel = [{"bereich": bereich.name, "hinweis": bereich.frage} for bereich in heikel_bereiche]

    ohne_regeln = sorted(klassen - getroffene_klassen)

    return {"hinweise": hinweise, "heikel": heikel, "ohne_regeln": ohne_regeln}


def _heikel_block(heikel: list[dict]) -> str:
    if not heikel:
        return ""
    eintraege = "".join(
        f'<div class="heikel-eintrag"><strong>{html.escape(eintrag["bereich"])}:</strong> '
        f'{html.escape(eintrag["hinweis"])}</div>'
        for eintrag in heikel
    )
    return f'<div class="heikel"><h2>⚠ Heikle Bereiche</h2>{eintraege}</div>'


def _karte(hinweis: dict) -> str:
    label, badge_klasse = _BADGES.get(hinweis["stufe"], (hinweis["stufe"].upper(), "badge-vermutung"))
    referenzen = ", ".join(html.escape(ref) for ref in hinweis["referenzen"])
    zitat_html = ""
    if hinweis["zitat"]:
        zitat_html = f'<blockquote>{html.escape(hinweis["zitat"])}</blockquote>'
    return (
        '<div class="karte">'
        f'<span class="badge {badge_klasse}">{label}</span>'
        f'<span class="staerke">{html.escape(hinweis["staerke"])}</span>'
        f'<p class="aussage"><strong>{html.escape(hinweis["aussage"])}</strong></p>'
        f'<p class="betrifft">„betrifft: {referenzen}“</p>'
        f'<p class="begruendung">{html.escape(hinweis["begruendung"])}</p>'
        f'<p class="quelle">Quelle: {html.escape(hinweis["quelle"])}</p>'
        f'{zitat_html}'
        '</div>'
    )


def _ohne_regeln_block(ohne_regeln: list[str]) -> str:
    if not ohne_regeln:
        return ""
    klassen = ", ".join(html.escape(klasse) for klasse in ohne_regeln)
    return f'<p class="ohne-regeln">Ohne Regel-Treffer in der Wissensbasis: {klassen}</p>'


_SEITE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{titel_seite}</title>
<style>
  body {{ background:#0d1117; color:#c9d1d9; font-family: -apple-system, "Segoe UI", sans-serif;
         margin: 2rem; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; border-bottom: 1px solid #30363d; padding-bottom: .5rem; }}
  .heikel {{ border: 2px solid #d4a72c; background:#2b2510; border-radius: 6px;
            padding: 1rem; margin-bottom: 1.5rem; }}
  .heikel h2 {{ margin-top:0; color:#e3b341; font-size:1.05rem; }}
  .heikel-eintrag {{ margin-bottom: .75rem; }}
  .karte {{ background:#161b22; border:1px solid #30363d; border-radius: 6px;
           padding: 1rem; margin-bottom: 1rem; }}
  .badge {{ display:inline-block; padding: .15rem .6rem; border-radius: 999px;
           font-size:.8rem; font-weight:600; margin-right:.5rem; }}
  .badge-belegt {{ background:#1f6f3d; color:#d3f9d8; }}
  .badge-vermutung {{ background:#8a6d1a; color:#fff3c4; }}
  .badge-verifiziert {{ background:#1f5f9e; color:#d0e7ff; }}
  .staerke {{ color:#8b949e; font-size:.85rem; }}
  .aussage {{ margin: .6rem 0; }}
  .betrifft {{ color:#8b949e; font-size:.85rem; margin: .3rem 0; }}
  .begruendung {{ margin: .5rem 0; }}
  .quelle {{ color:#8b949e; font-size:.85rem; margin-top:.5rem; }}
  blockquote {{ border-left: 3px solid #30363d; margin: .5rem 0 0; padding: .3rem 1rem;
               color:#8b949e; font-style: italic; }}
  .ohne-regeln {{ color:#8b949e; font-size:.9rem; margin: 1.5rem 0; }}
  footer {{ border-top: 1px solid #30363d; margin-top: 2rem; padding-top: 1rem;
           color:#6e7681; font-size:.8rem; }}
</style>
</head>
<body>
<h1>{titel}</h1>
{heikel}
{karten}
{ohne_regeln}
<footer>{fusszeile}</footer>
</body>
</html>
"""


def baue_anleitung(projekt: dict, wissens_repo: Path, heute: str) -> str:
    """Baut die dunkle HTML-Routing-Anleitung. Alle Repo-/Projekt-Texte werden
    per `html.escape` behandelt — nur Struktur und Stufen-Badges kommen aus
    diesem Modul, der Inhalt bleibt wörtlich aus der Wissensbasis."""
    daten = projekt_hinweise(projekt, wissens_repo)
    name = html.escape(str(projekt.get("name", "")))
    heute_escaped = html.escape(str(heute))
    titel_seite = f"Routing-Anleitung — {name} (Stand {heute_escaped})"
    titel = f"„{titel_seite}“"
    karten = "".join(_karte(hinweis) for hinweis in daten["hinweise"])
    fusszeile = ("„Einzige Quelle: Wissensbasis "
                 f"{html.escape(str(wissens_repo))} — Stufen sind Daten, nie hochgestuft.“")

    return _SEITE.format(
        titel_seite=titel_seite,
        titel=titel,
        heikel=_heikel_block(daten["heikel"]),
        karten=karten,
        ohne_regeln=_ohne_regeln_block(daten["ohne_regeln"]),
        fusszeile=fusszeile,
    )
