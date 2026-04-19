from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.models import (
    BlocksResponse,
    ComponentsResponse,
    ProjectState,
    RequirementsResponse,
    ValidationIssue,
    ValidationResponse,
    ValidationSeverity,
)
from app.repository import (
    get_blocks_response,
    get_components_response,
    get_project_state,
    get_requirements_response,
)
from app.seed import seed_if_empty

app = FastAPI(title="Hardware Copilot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    seed_if_empty()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/project", response_model=ProjectState)
def get_project() -> ProjectState:
    return get_project_state()


@app.get("/requirements", response_model=RequirementsResponse)
def get_requirements() -> RequirementsResponse:
    return get_requirements_response()


@app.get("/blocks", response_model=BlocksResponse)
def get_blocks() -> BlocksResponse:
    return get_blocks_response()


@app.get("/components", response_model=ComponentsResponse)
def get_components() -> ComponentsResponse:
    return get_components_response()


@app.get("/validation", response_model=ValidationResponse)
def get_validation() -> ValidationResponse:
    return ValidationResponse(
        items=[
            ValidationIssue(
                id="val-1",
                severity=ValidationSeverity.WARNING,
                title="Input protection incomplete",
                message="Reverse polarity protection topology is not fixed yet.",
                related_kind="block",
                related_id="blk-1",
            ),
            ValidationIssue(
                id="val-2",
                severity=ValidationSeverity.INFO,
                title="Buck regulator selected provisionally",
                message="Buck IC is a provisional choice and not yet reviewed for EMC.",
                related_kind="component",
                related_id="cmp-2",
            ),
        ]
    )