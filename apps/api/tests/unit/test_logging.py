"""Unit: structlog CRUD helper emits required JSON fields."""

from __future__ import annotations

import json
from io import StringIO

import structlog

from app.logging_setup import log_crud


def test_log_crud_emits_json_fields(monkeypatch) -> None:
    buf = StringIO()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=buf),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=False,
    )
    # Re-bind module logger after reconfigure
    import app.logging_setup as logging_setup

    logging_setup.logger = structlog.get_logger("retail-taxonomy-api")
    log_crud(
        event="zone_create",
        resource="zone",
        resource_id="abc",
        outcome="success",
        user="admin",
    )
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "zone_create"
    assert payload["service"] == "retail-taxonomy-api"
    assert payload["resource"] == "zone"
    assert payload["resource_id"] == "abc"
    assert payload["outcome"] == "success"
    assert payload["user"] == "admin"
    assert "password" not in payload
    assert "Authorization" not in payload
