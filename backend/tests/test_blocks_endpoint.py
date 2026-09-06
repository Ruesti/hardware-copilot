"""Bugfix-Regression: GET /blocks muss den ASCII-Schaltplan mitliefern."""
import pytest


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    import app.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    db.init_db()


def test_list_blocks_includes_schematic(tmp_db):
    from app.models import DesignBlockCreate, ProjectCreate
    from app.repository import (
        create_block, create_project, list_blocks, set_block_schematic,
    )

    prj = create_project(ProjectCreate(name="t"))
    b = create_block(prj.id, DesignBlockCreate(name="X", description=""))
    set_block_schematic(prj.id, b.id, "ASCII-PLAN")
    got = list_blocks(prj.id)[0]
    assert got.schematic_ascii == "ASCII-PLAN"
    assert got.schematic_validated is False
