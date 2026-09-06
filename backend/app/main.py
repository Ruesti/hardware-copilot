from __future__ import annotations

import json
import logging
import traceback
from typing import Any

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("hardware_copilot")

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from app.db import init_db
from app.models import (
    BlockConnection,
    BlockPositionUpdate,
    BlocksResponse,
    ComponentCreate,
    ComponentItem,
    ComponentUpdate,
    ComponentsResponse,
    ConnectionCreate,
    DiagramResponse,
    DatasheetsResponse,
    DesignBlock,
    DesignBlockCreate,
    DesignBlockUpdate,
    ChatHistoryResponse,
    ChatMessageCreate,
    Project,
    ProjectCreate,
    ProjectsListResponse,
    ProjectUpdate,
    RefreshDesignResponse,
    Requirement,
    RequirementCreate,
    RequirementUpdate,
    RequirementsResponse,
    SchematicValidateRequest,
    UsageResponse,
    ValidationResponse,
    ValidationIssue,
    ValidationSeverity,
)
from app.repository import (
    add_chat_message,
    bulk_create_blocks,
    bulk_create_components,
    clear_chat_messages,
    create_block,
    create_component,
    create_project,
    create_requirement,
    delete_block,
    delete_component,
    delete_project,
    delete_requirement,
    create_connection,
    delete_connection,
    find_block_by_name,
    get_block_components,
    get_chat_history_for_claude,
    get_diagram,
    get_project,
    get_project_context,
    get_usage_summary,
    is_block_schematic_validated,
    list_blocks,
    list_chat_messages,
    list_components,
    list_datasheets,
    list_projects,
    list_requirements,
    log_claude_usage,
    save_datasheet,
    set_block_schematic,
    set_block_schematic_validated,
    update_block,
    update_block_position,
    update_component,
    update_project,
    update_requirement,
)
from app.seed import seed_if_empty

app = FastAPI(title="Hardware Copilot Backend", version="2.0.0")

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


def _require_project(project_id: str) -> None:
    if get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")


def _persist_usage(project_id: str, endpoint: str, sink: list) -> None:
    """Schreibt alle gesammelten Claude-Usage-Records in die DB."""
    from app.claude_service import MODEL
    for r in sink:
        log_claude_usage(
            project_id,
            endpoint,
            MODEL,
            r.input_tokens,
            r.output_tokens,
            r.cache_read_tokens,
            r.cache_create_tokens,
        )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ── Projects ──────────────────────────────────────────────────────────────────

@app.get("/projects", response_model=ProjectsListResponse)
def get_projects() -> ProjectsListResponse:
    return ProjectsListResponse(items=list_projects())


@app.post("/projects", response_model=Project, status_code=201)
def post_project(body: ProjectCreate) -> Project:
    return create_project(body)


@app.get("/projects/{project_id}", response_model=Project)
def get_project_detail(project_id: str) -> Project:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/projects/{project_id}", response_model=Project)
def put_project(project_id: str, body: ProjectUpdate) -> Project:
    updated = update_project(project_id, body)
    if updated is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@app.delete("/projects/{project_id}", status_code=204)
def del_project(project_id: str) -> None:
    if not delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")


# ── Requirements ──────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/requirements", response_model=RequirementsResponse)
def get_requirements(project_id: str) -> RequirementsResponse:
    _require_project(project_id)
    return RequirementsResponse(items=list_requirements(project_id))


@app.post("/projects/{project_id}/requirements", response_model=Requirement, status_code=201)
def post_requirement(project_id: str, body: RequirementCreate) -> Requirement:
    _require_project(project_id)
    return create_requirement(project_id, body)


@app.put("/projects/{project_id}/requirements/{req_id}", response_model=Requirement)
def put_requirement(project_id: str, req_id: str, body: RequirementUpdate) -> Requirement:
    _require_project(project_id)
    updated = update_requirement(project_id, req_id, body)
    if updated is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return updated


@app.delete("/projects/{project_id}/requirements/{req_id}", status_code=204)
def del_requirement(project_id: str, req_id: str) -> None:
    _require_project(project_id)
    if not delete_requirement(project_id, req_id):
        raise HTTPException(status_code=404, detail="Requirement not found")


# ── Blocks ────────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/blocks", response_model=BlocksResponse)
def get_blocks(project_id: str) -> BlocksResponse:
    _require_project(project_id)
    return BlocksResponse(items=list_blocks(project_id))


@app.post("/projects/{project_id}/blocks", response_model=DesignBlock, status_code=201)
def post_block(project_id: str, body: DesignBlockCreate) -> DesignBlock:
    _require_project(project_id)
    return create_block(project_id, body)


@app.put("/projects/{project_id}/blocks/{blk_id}", response_model=DesignBlock)
def put_block(project_id: str, blk_id: str, body: DesignBlockUpdate) -> DesignBlock:
    _require_project(project_id)
    updated = update_block(project_id, blk_id, body)
    if updated is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return updated


@app.delete("/projects/{project_id}/blocks/{blk_id}", status_code=204)
def del_block(project_id: str, blk_id: str) -> None:
    _require_project(project_id)
    if not delete_block(project_id, blk_id):
        raise HTTPException(status_code=404, detail="Block not found")


# ── Components ────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/components", response_model=ComponentsResponse)
def get_components(project_id: str) -> ComponentsResponse:
    _require_project(project_id)
    return ComponentsResponse(items=list_components(project_id))


@app.post("/projects/{project_id}/components", response_model=ComponentItem, status_code=201)
def post_component(
    project_id: str, body: ComponentCreate, background_tasks: BackgroundTasks
) -> ComponentItem:
    _require_project(project_id)
    created = create_component(project_id, body)
    if created.block_id:
        _schedule_schematics_for_blocks(project_id, [created.block_id], background_tasks)
    return created


@app.put("/projects/{project_id}/components/{cmp_id}", response_model=ComponentItem)
def put_component(
    project_id: str, cmp_id: str, body: ComponentUpdate, background_tasks: BackgroundTasks
) -> ComponentItem:
    _require_project(project_id)
    # Vorherigen block_id merken, um beide Blöcke bei Umzug neu zu generieren
    prev = next((c for c in list_components(project_id) if c.id == cmp_id), None)
    updated = update_component(project_id, cmp_id, body)
    if updated is None:
        raise HTTPException(status_code=404, detail="Component not found")
    affected = {bid for bid in (prev.block_id if prev else None, updated.block_id) if bid}
    _schedule_schematics_for_blocks(project_id, list(affected), background_tasks)
    return updated


@app.delete("/projects/{project_id}/components/{cmp_id}", status_code=204)
def del_component(
    project_id: str, cmp_id: str, background_tasks: BackgroundTasks
) -> None:
    _require_project(project_id)
    prev = next((c for c in list_components(project_id) if c.id == cmp_id), None)
    if not delete_component(project_id, cmp_id):
        raise HTTPException(status_code=404, detail="Component not found")
    if prev and prev.block_id:
        _schedule_schematics_for_blocks(project_id, [prev.block_id], background_tasks)


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/chat", response_model=ChatHistoryResponse)
def get_chat(project_id: str) -> ChatHistoryResponse:
    _require_project(project_id)
    return ChatHistoryResponse(items=list_chat_messages(project_id))


@app.post("/projects/{project_id}/chat/stream")
async def stream_chat(project_id: str, body: ChatMessageCreate) -> StreamingResponse:
    _require_project(project_id)

    from app.claude_service import stream_chat as claude_stream

    # Save user message immediately
    add_chat_message(project_id, "user", body.content)

    context = get_project_context(project_id)
    history = get_chat_history_for_claude(project_id)
    # Remove the last user message from history since we pass it separately
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    collected: list[str] = []

    async def generate():
        from app.claude_service import capture_usage
        with capture_usage() as sink:
            try:
                async for chunk in claude_stream(history, body.content, context):
                    collected.append(chunk)
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            except Exception as exc:
                error_msg = f"[Claude error: {exc}]"
                collected.append(error_msg)
                yield f"data: {json.dumps({'text': error_msg})}\n\n"
            finally:
                full_response = "".join(collected)
                if full_response:
                    add_chat_message(project_id, "assistant", full_response)
                _persist_usage(project_id, "chat_stream", sink)
                yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/projects/{project_id}/chat/interview-stream")
async def interview_stream(project_id: str, body: ChatMessageCreate) -> StreamingResponse:
    _require_project(project_id)

    from app.claude_service import interview_chat as claude_interview

    add_chat_message(project_id, "user", body.content)

    context = get_project_context(project_id)
    history = get_chat_history_for_claude(project_id)
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    collected: list[str] = []

    async def generate():
        from app.claude_service import capture_usage
        with capture_usage() as sink:
            try:
                async for chunk in claude_interview(history, body.content, context):
                    collected.append(chunk)
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            except Exception as exc:
                error_msg = f"[Claude error: {exc}]"
                collected.append(error_msg)
                yield f"data: {json.dumps({'text': error_msg})}\n\n"
            finally:
                full_response = "".join(collected)
                if full_response:
                    add_chat_message(project_id, "assistant", full_response)
                _persist_usage(project_id, "interview_stream", sink)
                yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/projects/{project_id}/chat", status_code=204)
def delete_chat(project_id: str) -> None:
    _require_project(project_id)
    clear_chat_messages(project_id)


# ── Validation ────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/validation", response_model=ValidationResponse)
def get_validation(project_id: str) -> ValidationResponse:
    _require_project(project_id)

    from app.claude_service import validate_design

    context = get_project_context(project_id)
    try:
        issues_raw = validate_design(context)
    except Exception as exc:
        return ValidationResponse(
            items=[
                ValidationIssue(
                    id="err-0",
                    severity=ValidationSeverity.ERROR,
                    title="Validation unavailable",
                    message=str(exc),
                )
            ]
        )

    items = []
    for i, issue in enumerate(issues_raw):
        items.append(
            ValidationIssue(
                id=f"val-{i}",
                severity=ValidationSeverity(issue.get("severity", "info")),
                title=issue.get("title", "Issue"),
                message=issue.get("message", ""),
                related_kind=issue.get("related_kind"),
                related_id=issue.get("related_id"),
            )
        )
    return ValidationResponse(items=items)


# ── Datasheets ────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/datasheets", response_model=DatasheetsResponse)
def get_datasheets(project_id: str) -> DatasheetsResponse:
    _require_project(project_id)
    return DatasheetsResponse(items=list_datasheets(project_id))


@app.post("/projects/{project_id}/datasheet")
async def upload_datasheet(
    project_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    _require_project(project_id)

    from app.claude_service import analyze_datasheet

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(content))
        pdf_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}")

    try:
        extracted = analyze_datasheet(pdf_text, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude analysis failed: {exc}")

    record = save_datasheet(project_id, file.filename, extracted)
    return {"id": record.id, "filename": record.filename, "extractedData": extracted}


@app.post("/projects/{project_id}/components/{cmp_id}/fetch-datasheet")
def fetch_component_datasheet(project_id: str, cmp_id: str) -> dict[str, Any]:
    """Fetch datasheet from Nexar/Octopart by MPN, analyze with Claude, save result."""
    _require_project(project_id)

    from app.claude_service import analyze_datasheet
    from app.datasheet_fetcher import fetch_datasheet_for_mpn
    from pypdf import PdfReader
    import io

    comps = list_components(project_id)
    comp = next((c for c in comps if c.id == cmp_id), None)
    if comp is None:
        raise HTTPException(status_code=404, detail="Component not found")
    if not comp.mpn:
        raise HTTPException(status_code=400, detail="Component has no MPN — add one first")

    try:
        fetched = fetch_datasheet_for_mpn(comp.mpn)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Nexar lookup failed: {exc}")

    try:
        reader = PdfReader(io.BytesIO(fetched["pdf_bytes"]))
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}")

    try:
        extracted = analyze_datasheet(pdf_text, fetched["filename"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude analysis failed: {exc}")

    # Merge Nexar metadata as fallback for fields Claude may miss
    nexar = fetched.get("component_info", {})
    extracted.setdefault("manufacturer", nexar.get("manufacturer"))
    extracted.setdefault("mpn", nexar.get("mpn", comp.mpn))
    extracted.setdefault("description", nexar.get("description"))
    if nexar.get("specs"):
        extracted.setdefault("nexar_specs", nexar["specs"])

    record = save_datasheet(project_id, fetched["filename"], extracted, component_id=cmp_id)
    return {
        "id": record.id,
        "filename": record.filename,
        "sourceUrl": fetched["url"],
        "extractedData": extracted,
    }


# ── AI Actions ────────────────────────────────────────────────────────────────

def _regenerate_block_schematic(project_id: str, block_id: str) -> None:
    """Generiert den ASCII-Schaltplan eines Blocks und speichert ihn in der DB.
    Validierte Schaltpläne werden NIE überschrieben.
    Wird als BackgroundTask aufgerufen, Fehler werden geschluckt."""
    try:
        if is_block_schematic_validated(project_id, block_id):
            return  # Validierten Schaltplan nicht überschreiben

        from app.claude_service import describe_block_circuit as claude_describe
        from app.claude_service import capture_usage
        from app.repository import get_block

        block = get_block(project_id, block_id)
        if block is None:
            return
        comps = get_block_components(project_id, block_id)
        comp_dicts = [
            {"name": c.name, "mpn": c.mpn, "type": c.type,
             "package": c.package, "description": c.description}
            for c in comps
        ]
        with capture_usage() as sink:
            schematic = claude_describe(block.name, block.description, comp_dicts)
        set_block_schematic(project_id, block_id, schematic)
        _persist_usage(project_id, "describe_block_circuit_bg", sink)
    except Exception:
        # Background-Task: Fehler nicht propagieren, Frontend kann später re-triggern
        pass


def _schedule_schematics_for_blocks(
    project_id: str,
    block_ids: list[str],
    background_tasks: BackgroundTasks,
) -> None:
    for bid in block_ids:
        background_tasks.add_task(_regenerate_block_schematic, project_id, bid)


def _run_draft_circuit(project_id: str) -> dict[str, Any]:
    """Führt draft_circuit aus, mergt mit bestehenden Blöcken (Name-Match) und
    löscht via remove_block_ids überflüssige. Gibt erzeugte + entfernte IDs zurück."""
    from app.claude_service import draft_circuit as claude_draft

    context = get_project_context(project_id)
    result = claude_draft(context)

    new_block_ids: list[str] = []
    for b in result.get("blocks", []):
        name = b.get("name", "").strip()
        if not name:
            continue
        # Idempotenz: existiert ein Block mit gleichem Namen, nicht neu anlegen
        existing = find_block_by_name(project_id, name)
        if existing is not None:
            new_block_ids.append(existing.id)
            continue
        created = create_block(
            project_id,
            DesignBlockCreate(
                name=name,
                description=b.get("description", ""),
                trust_level=b.get("trust_level", "parsed"),
            ),
        )
        new_block_ids.append(created.id)

    removed_ids: list[str] = []
    for rid in result.get("remove_block_ids", []) or []:
        if delete_block(project_id, rid):
            removed_ids.append(rid)

    return {
        "summary": result.get("summary", ""),
        "new_block_ids": new_block_ids,
        "removed_block_ids": removed_ids,
    }


@app.post("/projects/{project_id}/suggest-components")
def suggest_components(
    project_id: str, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    _require_project(project_id)

    from app.claude_service import suggest_components as claude_suggest
    from app.claude_service import capture_usage

    context = get_project_context(project_id)
    try:
        with capture_usage() as sink:
            suggestions = claude_suggest(context)
    except Exception as exc:
        logger.error("suggest_components failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Claude suggest_components: {exc}")

    _persist_usage(project_id, "suggest_components", sink)
    created = bulk_create_components(project_id, suggestions)

    affected_block_ids = sorted({c.block_id for c in created if c.block_id})
    _schedule_schematics_for_blocks(project_id, affected_block_ids, background_tasks)

    return {
        "created": len(created),
        "components": [c.model_dump(by_alias=True) for c in created],
    }


@app.post("/projects/{project_id}/draft-circuit")
def draft_circuit(
    project_id: str, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    _require_project(project_id)

    from app.claude_service import capture_usage

    try:
        with capture_usage() as sink:
            outcome = _run_draft_circuit(project_id)
    except Exception as exc:
        logger.error("draft_circuit failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Claude draft_circuit: {exc}")
    _persist_usage(project_id, "draft_circuit", sink)

    blocks = list_blocks(project_id)
    new_ids = set(outcome["new_block_ids"])
    new_blocks = [b for b in blocks if b.id in new_ids]
    # Schaltpläne der neuen Blöcke jetzt erstmal leer halten; Schaltpläne werden
    # nach suggest_components / refresh-design generiert, sobald Komponenten zugeordnet sind.
    return {
        "summary": outcome["summary"],
        "blocksCreated": len(new_blocks),
        "blocks": [b.model_dump(by_alias=True) for b in new_blocks],
        "removedBlockIds": outcome["removed_block_ids"],
    }


@app.post("/projects/{project_id}/refresh-design", response_model=RefreshDesignResponse)
def refresh_design(
    project_id: str,
    background_tasks: BackgroundTasks,
    schematic_mode: str = "auto",
) -> RefreshDesignResponse:
    """Idempotenter Komplett-Refresh: draft_circuit + suggest_components + suggest_connections.
    schematic_mode='auto' (Default): ASCII-Schaltpläne werden für alle Blöcke mit Komponenten
        im Hintergrund (re-)generiert — validierte bleiben unberührt.
    schematic_mode='manual': keine Hintergrund-Generierung; der User triggert pro Block manuell."""
    _require_project(project_id)

    from app.claude_service import suggest_components as claude_suggest
    from app.claude_service import suggest_connections as claude_suggest_conns
    from app.claude_service import capture_usage

    try:
        with capture_usage() as sink_draft:
            outcome = _run_draft_circuit(project_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"draft_circuit failed: {exc}")
    _persist_usage(project_id, "refresh.draft_circuit", sink_draft)

    # Komponentenvorschläge auf Basis der jetzt aktualisierten Block-Liste
    context = get_project_context(project_id)
    try:
        with capture_usage() as sink_sc:
            suggestions = claude_suggest(context)
            bulk_create_components(project_id, suggestions)
        _persist_usage(project_id, "refresh.suggest_components", sink_sc)
    except Exception:
        # Komponentenvorschläge sind optional — Refresh trotzdem fortführen
        pass

    # Verbindungen automatisch nachziehen, wenn Blöcke ohne Anbindung existieren.
    # Bestehende Verbindungen werden anhand (source, target, conn_type) dedupliziert.
    blocks_now = list_blocks(project_id)
    existing_conns = get_diagram(project_id)[1]
    connected_ids = {c.source_block_id for c in existing_conns} | {
        c.target_block_id for c in existing_conns
    }
    isolated = [b for b in blocks_now if b.id not in connected_ids]
    if len(blocks_now) >= 2 and (not existing_conns or isolated):
        existing_keys = {
            (c.source_block_id, c.target_block_id, c.conn_type) for c in existing_conns
        }
        try:
            with capture_usage() as sink_conn:
                conn_suggestions = claude_suggest_conns(get_project_context(project_id))
            _persist_usage(project_id, "refresh.suggest_connections", sink_conn)
            block_name_to_id = {b.name: b.id for b in blocks_now}
            for s in conn_suggestions:
                src_id = block_name_to_id.get(s.get("source_block_name", ""))
                tgt_id = block_name_to_id.get(s.get("target_block_name", ""))
                conn_type = s.get("conn_type", "signal")
                if not src_id or not tgt_id or src_id == tgt_id:
                    continue
                key = (src_id, tgt_id, conn_type)
                if key in existing_keys:
                    continue
                create_connection(
                    project_id,
                    ConnectionCreate(
                        source_block_id=src_id,
                        target_block_id=tgt_id,
                        label=s.get("label", ""),
                        conn_type=conn_type,
                    ),
                )
                existing_keys.add(key)
        except Exception:
            pass

    # ASCII-Schaltpläne für alle Blöcke mit Komponenten neu erzeugen — nur im Auto-Modus
    blocks_final, conns_final = get_diagram(project_id)
    if schematic_mode == "auto":
        block_ids_with_components = [
            b.id for b in blocks_final
            if b.component_count > 0 and not b.schematic_validated
        ]
        _schedule_schematics_for_blocks(project_id, block_ids_with_components, background_tasks)

    return RefreshDesignResponse(
        blocks=blocks_final,
        components=list_components(project_id),
        connections=conns_final,
        removed_block_ids=outcome["removed_block_ids"],
    )


# ── KiCad-Export ──────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/export/kicad")
def export_kicad(project_id: str) -> Response:
    _require_project(project_id)
    from app.kicad.export import run_export
    try:
        result = run_export(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return Response(
        content=result.schematic_text,
        media_type="application/x-kicad-schematic",
        headers={"Content-Disposition": f'attachment; filename="{project_id}.kicad_sch"'},
    )


@app.get("/projects/{project_id}/export/kicad/report")
def export_kicad_report(project_id: str) -> dict[str, Any]:
    _require_project(project_id)
    from app.kicad.export import run_export
    try:
        return run_export(project_id).report
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Diagram ───────────────────────────────────────────────────────────────────

@app.get("/projects/{project_id}/diagram", response_model=DiagramResponse)
def get_diagram_endpoint(project_id: str) -> DiagramResponse:
    _require_project(project_id)
    blocks, connections = get_diagram(project_id)
    return DiagramResponse(blocks=blocks, connections=connections)


@app.put("/projects/{project_id}/blocks/{blk_id}/position", status_code=204)
def put_block_position(project_id: str, blk_id: str, body: BlockPositionUpdate) -> None:
    _require_project(project_id)
    update_block_position(project_id, blk_id, body.pos_x, body.pos_y)


@app.post("/projects/{project_id}/connections", response_model=BlockConnection, status_code=201)
def post_connection(project_id: str, body: ConnectionCreate) -> BlockConnection:
    _require_project(project_id)
    return create_connection(project_id, body)


@app.delete("/projects/{project_id}/connections/{conn_id}", status_code=204)
def del_connection(project_id: str, conn_id: str) -> None:
    _require_project(project_id)
    if not delete_connection(project_id, conn_id):
        raise HTTPException(status_code=404, detail="Connection not found")


@app.post("/projects/{project_id}/suggest-connections")
def suggest_connections_endpoint(project_id: str) -> dict[str, Any]:
    _require_project(project_id)
    from app.claude_service import suggest_connections as claude_suggest_conns
    from app.claude_service import capture_usage
    context = get_project_context(project_id)
    block_name_to_id = {b["name"]: b["id"] for b in context.get("blocks", [])}
    try:
        with capture_usage() as sink:
            suggestions = claude_suggest_conns(context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    _persist_usage(project_id, "suggest_connections", sink)
    created = []
    for s in suggestions:
        src_id = block_name_to_id.get(s.get("source_block_name", ""))
        tgt_id = block_name_to_id.get(s.get("target_block_name", ""))
        if src_id and tgt_id and src_id != tgt_id:
            conn = create_connection(
                project_id,
                ConnectionCreate(
                    source_block_id=src_id,
                    target_block_id=tgt_id,
                    label=s.get("label", ""),
                    conn_type=s.get("conn_type", "signal"),
                ),
            )
            created.append(conn.model_dump(by_alias=True))
    return {"created": len(created), "connections": created}


@app.put("/projects/{project_id}/blocks/{blk_id}/validate-schematic", status_code=204)
def validate_block_schematic(
    project_id: str, blk_id: str, body: SchematicValidateRequest
) -> None:
    _require_project(project_id)
    if not set_block_schematic_validated(project_id, blk_id, body.validated):
        raise HTTPException(status_code=404, detail="Block not found")


@app.post("/projects/{project_id}/blocks/{blk_id}/describe-circuit")
def describe_block_circuit(project_id: str, blk_id: str) -> dict[str, Any]:
    _require_project(project_id)
    from app.claude_service import describe_block_circuit as claude_describe
    from app.claude_service import capture_usage
    blocks = list_blocks(project_id)
    block = next((b for b in blocks if b.id == blk_id), None)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    comps = [
        c for c in list_components(project_id) if c.block_id == blk_id
    ]
    comp_dicts = [
        {"name": c.name, "mpn": c.mpn, "type": c.type,
         "package": c.package, "description": c.description}
        for c in comps
    ]
    try:
        with capture_usage() as sink:
            schematic = claude_describe(block.name, block.description, comp_dicts)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    set_block_schematic(project_id, blk_id, schematic)
    _persist_usage(project_id, "describe_block_circuit", sink)
    return {"blockId": blk_id, "schematic": schematic}


# ── Usage / Token Tracking ────────────────────────────────────────────────────

@app.get("/projects/{project_id}/usage", response_model=UsageResponse)
def get_usage(project_id: str) -> UsageResponse:
    _require_project(project_id)
    summary = get_usage_summary(project_id)
    return UsageResponse(**summary)
