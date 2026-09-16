"""Structured, text-free diagnostics for local batch runs."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import TextIO


def emit(event: str, *, stream: TextIO | None = None, **fields: object) -> None:
    """emit writes one stable JSON event without including Bible text."""

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    target = stream or sys.stderr
    target.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    target.flush()
