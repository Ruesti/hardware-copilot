"""Routing-Anleitung aus der Wissensbasis (E6 Task 4).

Eigenes tmp-Wissensrepo als Fixture: Regel-Template wörtlich aus
test_wissen_router.py übernommen (exakte Feldnamen für store.load_rules),
heikel.toml-Feldnamen aus wissensschicht/heikel.py bzw. wissensschicht/tests/
test_heikel.py übernommen. Drei Regeln: R-001 (schaltregler, belegt),
R-002 (abblock_c, vermutung, quelle typ „keine“ — wie im echten Repo, siehe
regeln/versorgung/R-020.toml), R-003 (mcu_wifi, belegt) — nicht in der BOM
der Tests, damit die Klassenfilterung geprüft werden kann.
"""
import pytest

from backend.app.kicad.anleitung import baue_anleitung, projekt_hinweise

R_001 = """\
id = "R-001"
bereich = "schaltregler"
aussage = "Testaussage Schaltregler."
begruendung = "Testbegründung Schaltregler."
staerke = "muss"
stufe = "belegt"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "datenblatt"
titel = "Testblatt"
dokument = "DOC1"
fundstelle = "PDF-S. 1"
url = "https://example.com/doc.pdf"
zitat = "Original quote."

[geltung]
klasse = "schaltregler"
"""

R_002 = """\
id = "R-002"
bereich = "abblock_c"
aussage = "Testaussage Abblock-C."
begruendung = "Testbegründung Abblock-C."
staerke = "sollte"
stufe = "vermutung"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "keine"
titel = ""
dokument = ""
fundstelle = ""
url = ""
zitat = ""

[geltung]
klasse = "abblock_c"
"""

R_003 = """\
id = "R-003"
bereich = "mcu_wifi"
aussage = "Testaussage MCU-WiFi."
begruendung = "Testbegründung MCU-WiFi."
staerke = "sollte"
stufe = "belegt"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "datenblatt"
titel = "WiFi-Blatt"
dokument = "DOC2"
fundstelle = "PDF-S. 3"
url = "https://example.com/wifi.pdf"
zitat = "WiFi quote."

[geltung]
klasse = "mcu_wifi"
"""

HEIKEL_TOML = """\
[[bereich]]
name = "schaltregler_heiss"
klassen = ["schaltregler"]
unterdrueckt_regeln = false
frage = "Kühlfläche ausreichend dimensioniert für den Spitzenstrom?"
fundstelle = ""
fundstelle_hinweis = "Keine belegte Quelle in der Regelbasis."
"""


@pytest.fixture
def wissens_repo(tmp_path):
    (tmp_path / "regeln" / "schaltregler").mkdir(parents=True)
    (tmp_path / "regeln" / "schaltregler" / "R-001.toml").write_text(R_001)
    (tmp_path / "regeln" / "abblock_c").mkdir(parents=True)
    (tmp_path / "regeln" / "abblock_c" / "R-002.toml").write_text(R_002)
    (tmp_path / "regeln" / "mcu_wifi").mkdir(parents=True)
    (tmp_path / "regeln" / "mcu_wifi" / "R-003.toml").write_text(R_003)
    (tmp_path / "heikel.toml").write_text(HEIKEL_TOML)
    return tmp_path


def test_hinweise_filtern_nach_bom_klassen(wissens_repo):
    projekt = {"name": "P", "positionen": [
        {"referenz": "U2", "klasse": "schaltregler"},
        {"referenz": "C1", "klasse": "abblock_c"},
        {"referenz": "C2", "klasse": "abblock_c"},
    ]}

    h = projekt_hinweise(projekt, wissens_repo)

    ids = {x["regel_id"] for x in h["hinweise"]}
    assert ids == {"R-001", "R-002"}          # R-003 (mcu_wifi) nicht in der BOM
    abblock = next(x for x in h["hinweise"] if x["regel_id"] == "R-002")
    assert abblock["referenzen"] == ["C1", "C2"]
    assert abblock["stufe"] == "vermutung"


def test_heikel_warnung_bei_betroffener_klasse(wissens_repo):
    projekt = {"name": "P", "positionen": [{"referenz": "U2", "klasse": "schaltregler"}]}

    h = projekt_hinweise(projekt, wissens_repo)

    assert h["heikel"] and "schaltregler" not in h["ohne_regeln"]


def test_html_traegt_marker_zitat_und_escaped(wissens_repo):
    projekt = {"name": "<böse>", "positionen": [
        {"referenz": "C1", "klasse": "abblock_c"},
        {"referenz": "U2", "klasse": "schaltregler"},
    ]}

    html_text = baue_anleitung(projekt, wissens_repo, heute="2026-09-11")

    assert "⚠ VERMUTUNG" in html_text and "BELEGT" in html_text
    assert "<blockquote>" in html_text and "Original quote." in html_text
    assert "&lt;böse&gt;" in html_text and "<böse>" not in html_text
    assert "Stand 2026-09-11" in html_text


def test_ohne_regeln_bei_klasse_ohne_treffer(wissens_repo):
    projekt = {"name": "P", "positionen": [{"referenz": "X1", "klasse": "unbekannt_xyz"}]}

    h = projekt_hinweise(projekt, wissens_repo)

    assert h["hinweise"] == []
    assert h["ohne_regeln"] == ["unbekannt_xyz"]


def test_position_ohne_klasse_wird_uebersprungen(wissens_repo):
    projekt = {"name": "P", "positionen": [
        {"referenz": "X1", "klasse": ""},
        {"referenz": "X2"},  # Feld fehlt ganz
    ]}

    h = projekt_hinweise(projekt, wissens_repo)

    assert h["hinweise"] == [] and h["heikel"] == [] and h["ohne_regeln"] == []


def test_stufe_wird_nicht_hochgestuft(wissens_repo):
    """Stufen kommen unverändert aus dem Repo — R-002 bleibt „vermutung“,
    obwohl seine Klasse eine Karte mit belegter Regel daneben hat."""
    projekt = {"name": "P", "positionen": [
        {"referenz": "U2", "klasse": "schaltregler"},
        {"referenz": "C1", "klasse": "abblock_c"},
    ]}

    h = projekt_hinweise(projekt, wissens_repo)

    stufen = {x["regel_id"]: x["stufe"] for x in h["hinweise"]}
    assert stufen == {"R-001": "belegt", "R-002": "vermutung"}


def test_fusszeile_nennt_repo_und_datenstatus(wissens_repo):
    projekt = {"name": "P", "positionen": [{"referenz": "U2", "klasse": "schaltregler"}]}

    html_text = baue_anleitung(projekt, wissens_repo, heute="2026-09-11")

    assert "Stufen sind Daten" in html_text
    assert str(wissens_repo) in html_text
