from __future__ import annotations

import os
import time
from typing import Any

import httpx

NEXAR_TOKEN_URL = "https://identity.nexar.com/connect/token"
NEXAR_API_URL = "https://api.nexar.com/graphql"

_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}

_SEARCH_QUERY = """
query SearchComponent($q: String!) {
  supSearch(q: $q, limit: 5) {
    results {
      part {
        mpn
        manufacturer { name }
        shortDescription
        datasheets { url }
        specs { attribute { name } displayValue }
      }
    }
  }
}
"""


def _get_token() -> str:
    client_id = os.environ.get("NEXAR_CLIENT_ID", "").strip()
    client_secret = os.environ.get("NEXAR_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise ValueError(
            "NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET not set. "
            "Register at https://nexar.com/api for a free account."
        )

    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return str(_token_cache["token"])

    resp = httpx.post(
        NEXAR_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60
    return str(_token_cache["token"])


def lookup_component(mpn: str) -> dict[str, Any]:
    """Query Nexar/Octopart for component metadata and datasheet URLs."""
    token = _get_token()
    resp = httpx.post(
        NEXAR_API_URL,
        json={"query": _SEARCH_QUERY, "variables": {"q": mpn}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()

    results = (
        resp.json()
        .get("data", {})
        .get("supSearch", {})
        .get("results", [])
    )
    if not results:
        return {}

    part = results[0]["part"]
    specs = {
        s["attribute"]["name"]: s["displayValue"]
        for s in part.get("specs", [])
        if s.get("attribute") and s.get("displayValue")
    }

    return {
        "mpn": part.get("mpn", mpn),
        "manufacturer": (part.get("manufacturer") or {}).get("name"),
        "description": part.get("shortDescription"),
        "datasheet_urls": [
            d["url"] for d in part.get("datasheets", []) if d.get("url")
        ],
        "specs": specs,
    }


def download_pdf(url: str) -> bytes:
    resp = httpx.get(
        url,
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "HardwareCopilot/1.0 (+https://github.com/hardware-copilot)"},
    )
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if "pdf" not in content_type.lower() and not url.lower().split("?")[0].endswith(".pdf"):
        raise ValueError(f"Response is not a PDF (content-type: {content_type})")
    return resp.content


def fetch_datasheet_for_mpn(mpn: str) -> dict[str, Any]:
    """
    Full pipeline: MPN → Nexar lookup → PDF download.
    Returns dict with keys: pdf_bytes, url, filename, component_info.
    """
    component_info = lookup_component(mpn)
    if not component_info:
        raise ValueError(f"No component found on Nexar for MPN: {mpn}")

    urls = component_info.get("datasheet_urls", [])
    if not urls:
        raise ValueError(f"Nexar found the component but has no datasheet URL for: {mpn}")

    last_error: Exception = RuntimeError("No URLs tried")
    for url in urls[:3]:
        try:
            pdf_bytes = download_pdf(url)
            filename = f"{mpn}.pdf"
            return {
                "pdf_bytes": pdf_bytes,
                "url": url,
                "filename": filename,
                "component_info": component_info,
            }
        except Exception as exc:
            last_error = exc
            continue

    raise ValueError(f"Could not download any datasheet PDF for {mpn}: {last_error}")
