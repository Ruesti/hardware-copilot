"""Die App ist nach der Entrümpelung genau das Cockpit-Backend."""
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_nur_cockpit_routen():
    # Über das OpenAPI-Schema statt app.routes: neuere FastAPI-Versionen
    # legen eingebundene Router nicht mehr flach in app.routes ab.
    pfade = set(app.openapi()["paths"])

    assert any(p.startswith("/bestand") for p in pfade)
    assert any(p.startswith("/projekte") for p in pfade)
    assert any(p.startswith("/wissen") for p in pfade)
    for alt in ("/chat", "/projects", "/draft-circuit", "/validation",
                "/datasheet", "/usage", "/refresh-design"):
        assert not any(p.startswith(alt) for p in pfade), alt
