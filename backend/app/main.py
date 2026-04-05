from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ChatMessage,
    ComponentItem,
    ComponentsResponse,
    DesignBlock,
    ProjectState,
    Requirement,
    TrustLevel,
    ValidationIssue,
    ValidationResponse,
    ValidationSeverity,
)

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


def build_demo_components() -> list[ComponentItem]:
    return [
        ComponentItem(
            id="cmp-1",
            name="TVS Diode",
            value="SMBJ33A",
            package="SMB",
            manufacturer="Littelfuse",
            mpn="SMBJ33A",
            description="Input surge protection diode.",
            trust_level=TrustLevel.REVIEWED,
            block_id="blk-1",
        ),
        ComponentItem(
            id="cmp-2",
            name="Buck Regulator",
            value="MP1584EN",
            package="SOIC-8",
            manufacturer="MPS",
            mpn="MP1584EN",
            description="24V to 5V buck regulator.",
            trust_level=TrustLevel.PARSED,
            block_id="blk-2",
        ),
        ComponentItem(
            id="cmp-3",
            name="MCU",
            value="ESP32-C3",
            package="QFN32",
            manufacturer="Espressif",
            mpn="ESP32-C3",
            description="Wi-Fi/BLE microcontroller.",
            trust_level=TrustLevel.VALIDATED,
            block_id="blk-3",
        ),
    ]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/project", response_model=ProjectState)
def get_project() -> ProjectState:
    return ProjectState(
        name="24V Presence Sensor",
        phase="Phase 3.2 — Domain API Expansion",
        requirements=[
            Requirement(
                id="req-1",
                title="24V supply input",
                description="The system shall accept a 24V DC input.",
                status="open",
            ),
            Requirement(
                id="req-2",
                title="Presence detection",
                description="The system shall detect human presence.",
                status="open",
            ),
        ],
        blocks=[
            DesignBlock(
                id="blk-1",
                name="24V Input Protection",
                description="Input polarity and surge protection stage.",
                trust_level=TrustLevel.REVIEWED,
            ),
            DesignBlock(
                id="blk-2",
                name="Buck 24V to 5V",
                description="Primary step-down conversion.",
                trust_level=TrustLevel.PARSED,
            ),
            DesignBlock(
                id="blk-3",
                name="ESP32-C3 Core",
                description="Main control and connectivity block.",
                trust_level=TrustLevel.NEW,
            ),
        ],
        chat_messages=[
            ChatMessage(
                id="msg-1",
                role="assistant",
                content="Initial project draft created from sample backend data.",
            )
        ],
    )


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


@app.get("/components", response_model=ComponentsResponse)
def get_components() -> ComponentsResponse:
    return ComponentsResponse(items=build_demo_components())