"""Export-Endpoint über den FastAPI-TestClient mit geseedetem Mini-Projekt."""
import pytest
from fastapi.testclient import TestClient

from .conftest import KICAD_SYMBOLS, requires_kicad


@pytest.fixture()
def seeded_client(tmp_path, monkeypatch):
    import app.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)

    from app.main import app
    with TestClient(app) as client:
        from app.models import (
            BlockConnection, ComponentCreate, ConnectionCreate,
            DesignBlockCreate, ProjectCreate,
        )
        from app.repository import (
            create_block, create_component, create_connection, create_project,
        )

        prj = create_project(ProjectCreate(name="Export-Test"))
        b_reg = create_block(prj.id, DesignBlockCreate(name="Regler", description=""))
        b_mcu = create_block(prj.id, DesignBlockCreate(name="MCU", description=""))
        create_connection(prj.id, ConnectionCreate(
            source_block_id=b_reg.id, target_block_id=b_mcu.id,
            label="3.3V", conn_type="power",
        ))
        create_connection(prj.id, ConnectionCreate(
            source_block_id=b_reg.id, target_block_id=b_mcu.id,
            label="GND", conn_type="gnd",
        ))
        create_component(prj.id, ComponentCreate(
            name="ESP32-S3-WROOM-1-N8", type="mcu", mpn="ESP32-S3-WROOM-1-N8",
            block_id=b_mcu.id,
        ))
        create_component(prj.id, ComponentCreate(
            name="100nF", type="passive_capacitor", value="100nF",
            block_id=b_mcu.id, net_role="decoupling",
        ))
        yield client, prj.id


@requires_kicad
def test_export_endpoint_returns_schematic(seeded_client):
    client, pid = seeded_client
    r = client.get(f"/projects/{pid}/export/kicad")
    assert r.status_code == 200
    assert r.text.startswith("(kicad_sch")
    assert "attachment" in r.headers["content-disposition"]


@requires_kicad
def test_export_report(seeded_client):
    client, pid = seeded_client
    r = client.get(f"/projects/{pid}/export/kicad/report")
    assert r.status_code == 200
    data = r.json()
    assert {"instances", "unmapped", "warnings", "counts"} <= set(data)
    assert data["counts"]["mapped"] == 1     # ESP32 aus Bibliothek
    assert data["counts"]["fallback"] == 1   # 100nF über Typ-Fallback


def test_export_unknown_project_404(seeded_client):
    client, _ = seeded_client
    r = client.get("/projects/prj-gibtsnicht/export/kicad")
    assert r.status_code == 404
