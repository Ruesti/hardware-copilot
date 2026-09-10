"""Cockpit-Backend (Spec §3.4): Bestand + Wissen für die App-Panels.

Die alte „App generiert KiCad selbst"-Strecke (Chat/Draft/Validate/Datasheet,
Projekt-Welt, Claude-API) ist entfernt — KiCad läuft über Konnect, KI über
Claude Code (Motor-Schnittstelle folgt in E4). Start vom Repo-Root:
uvicorn backend.app.main:app
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import bestand, wissen

app = FastAPI(title="Hardware-Copilot Cockpit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420",
                   "http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bestand.router)
app.include_router(wissen.router)


@app.get("/health")
def health():
    return {"status": "ok"}
