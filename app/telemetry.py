"""
telemetry.py — Centralized Source Telemetry & Pagination Tracking.
Tracks per-source pages fetched, pagination mode, completeness, and errors.
"""
from typing import Dict, Optional
from app.models import SourceTelemetry

_REGISTRY: Dict[str, SourceTelemetry] = {}

def reset_telemetry() -> None:
    """Clears telemetry before a new pipeline run."""
    _REGISTRY.clear()

def record_telemetry(
    source: str,
    pages: int = 1,
    raw: int = 0,
    mode: str = "SINGLE_PAGE",
    completeness: str = "COMPLETE",
    coverage: str = "VERIFIED",
    error: Optional[str] = None,
) -> None:
    """Records or updates source-level pagination and health telemetry."""
    if source in _REGISTRY:
        existing = _REGISTRY[source]
        _REGISTRY[source] = SourceTelemetry(
            source=source,
            pages=existing.pages + pages,
            raw=existing.raw + raw,
            mode=mode if mode != "SINGLE_PAGE" else existing.mode,
            completeness="FAILED" if (existing.completeness == "FAILED" or completeness == "FAILED") else completeness,
            coverage=coverage if coverage != "VERIFIED" else existing.coverage,
            error=error or existing.error,
        )
    else:
        _REGISTRY[source] = SourceTelemetry(
            source=source,
            pages=pages,
            raw=raw,
            mode=mode,
            completeness=completeness,
            coverage=coverage,
            error=error,
        )

def get_telemetry() -> Dict[str, SourceTelemetry]:
    """Returns a snapshot of the current run telemetry."""
    return dict(_REGISTRY)
