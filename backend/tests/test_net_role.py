"""net_role: Migration, Persistenz und Durchreichung durch bulk_create."""
import pytest


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    import app.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    db.init_db()
    return db


def test_component_net_role_roundtrip(tmp_db):
    from app.models import ComponentCreate, ProjectCreate
    from app.repository import create_project, create_component, list_components

    prj = create_project(ProjectCreate(name="t"))
    create_component(prj.id, ComponentCreate(
        name="10k", type="passive_resistor", description="Pull-up SDA",
        net_role="pullup:SDA",
    ))
    items = list_components(prj.id)
    assert items[0].net_role == "pullup:SDA"


def test_bulk_create_passes_net_role(tmp_db):
    from app.models import ProjectCreate
    from app.repository import create_project, bulk_create_components, list_components

    prj = create_project(ProjectCreate(name="t"))
    bulk_create_components(prj.id, [
        {"name": "100nF", "type": "passive_capacitor", "net_role": "decoupling"},
        {"name": "MCU", "type": "mcu"},  # ohne net_role
    ])
    by_name = {c.name: c for c in list_components(prj.id)}
    assert by_name["100nF"].net_role == "decoupling"
    assert by_name["MCU"].net_role is None


def test_migration_is_idempotent(tmp_db):
    tmp_db.init_db()  # zweiter Lauf darf nicht knallen
