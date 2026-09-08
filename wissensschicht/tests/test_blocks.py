"""Phase 4: Verified Blocks — erfassen, laden, suchen, ausgeben (§0 D1-D4, C5)."""
import pytest

from wissensschicht.blocks import (BlockFehler, block_volltext, erfasse_block,
                                   lade_bloecke, suche_bloecke)


DATEN = dict(
    titel="3,3-V-Versorgung ESP32-Logger",
    kernbauteil="XC6220B331",
    topologie="LiPo/USB auf XC6220, CIN 10 µF, CL 4,7 µF, dahinter ESP32-S3",
    gebaut="XC6220B331MR mit CIN 10 µF X7R, CL 4,7 µF X7R",
    gemessen="3,29 V bei 480 mA WLAN-Burst, Einbruch 40 mV",
    gescheitert="",
    fallback="",
    projekt="esp32-logger",
    messbedingungen="Oszilloskop 100 MHz, Tastkopf 1:10, Raumtemperatur",
    grenzen="bis 500 mA Burst getestet, nicht dauerhaft; nur bei 25 Grad",
    revision="breadboard-aufbau-1",
    ausschnitt="U1 XC6220B331MR: VIN=VBAT, VOUT=3V3, C1 10u VIN-GND, C2 4u7 VOUT-GND",
    regeln=["R-037", "R-038"],
)


def test_erfasse_block_schreibt_toml_und_ausschnitt(tmp_path):
    meldung = erfasse_block(tmp_path, **DATEN)

    assert "B-001" in meldung
    assert (tmp_path / "bloecke" / "B-001.toml").exists()
    assert (tmp_path / "bloecke" / "B-001-ausschnitt.txt").read_text().startswith("U1 XC6220B331MR")
    bloecke = lade_bloecke(tmp_path)
    assert bloecke[0].id == "B-001"
    assert bloecke[0].grenzen.startswith("bis 500 mA")
    assert bloecke[0].regeln == ["R-037", "R-038"]


def test_ids_laufen_fort(tmp_path):
    erfasse_block(tmp_path, **DATEN)
    meldung = erfasse_block(tmp_path, **{**DATEN, "titel": "Zweiter Block"})

    assert "B-002" in meldung
    assert len(lade_bloecke(tmp_path)) == 2


def test_pflichtfelder_werden_erzwungen(tmp_path):
    with pytest.raises(BlockFehler, match="gemessen"):
        erfasse_block(tmp_path, **{**DATEN, "gemessen": ""})
    with pytest.raises(BlockFehler, match="ausschnitt"):
        erfasse_block(tmp_path, **{**DATEN, "ausschnitt": ""})


def test_erfassen_meldet_c5_hochstufung_wenn_regeln_verknuepft(tmp_path):
    meldung = erfasse_block(tmp_path, **DATEN)

    assert "R-037" in meldung
    assert "verifiziert" in meldung


def test_suche_findet_ueber_kernbauteil_und_titel(tmp_path):
    erfasse_block(tmp_path, **DATEN)

    treffer = suche_bloecke(lade_bloecke(tmp_path), "xc6220")
    assert [b.id for b in treffer] == ["B-001"]
    assert suche_bloecke(lade_bloecke(tmp_path), "drv8825") == []
    assert [b.id for b in suche_bloecke(lade_bloecke(tmp_path), "logger")] == ["B-001"]


def test_volltext_traegt_d4_banner(tmp_path):
    erfasse_block(tmp_path, **DATEN)
    block = lade_bloecke(tmp_path)[0]

    text = block_volltext(block)

    assert "verifiziert" in text.lower()
    assert "Vermutung" in text
    assert "Differenz" in text
    assert "bis 500 mA" in text
    assert "Oszilloskop" in text
