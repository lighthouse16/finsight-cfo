"""Tests for structured JSON logging (Windows-safe)."""

import datetime
import json
import logging
import io
import re

from app.core.log_config import SanitizingJSONFormatter, sanitize_message, setup_json_logging


def test_sanitize_messages():
    """Sensitive patterns like Authorization headers are masked."""
    msg = "Authorization: Bearer my-secret-token-12345"
    clean = sanitize_message(msg)
    assert "my-secret-token" not in clean
    assert "Authorization: ****" in clean


def test_sanitize_apikey():
    """API key patterns in query strings are masked."""
    msg = "apikey=sk-abc123def456"
    clean = sanitize_message(msg)
    assert "sk-abc123def456" not in clean
    assert "apikey=****" in clean or "apikey: ****" in clean


def test_windows_safe_timestamp():
    """
    Verify that the JSON formatter produces ISO-8601 timestamps
    WITHOUT using strftime %f (which fails on Windows Python 3.11).
    """
    buf = io.StringIO()
    logger = setup_json_logging("test_logger", stream=buf)

    logger.info("hello world")
    output = buf.getvalue()
    record = json.loads(output.strip())

    ts = record["timestamp"]
    # Must be ISO-8601 with microseconds (e.g. 2026-06-12T10:30:00.123456+00:00)
    assert "T" in ts
    # Verify it doesn't contain the problematic '%f' literal
    assert "%f" not in ts
    # Verify it's parseable
    dt = datetime.datetime.fromisoformat(ts)
    assert dt.tzinfo is not None


def test_json_output_structure():
    """Log records are emitted as valid JSON with expected fields."""
    buf = io.StringIO()
    logger = setup_json_logging("test_logger2", stream=buf)

    logger.info("Test message", extra={"user_id": 42})
    output = buf.getvalue()
    record = json.loads(output.strip())

    assert record["level"] == "INFO"
    assert record["message"] == "Test message"
    assert record["logger"] == "test_logger2"
    assert record["module"] == "test_logging"
    assert "timestamp" in record
    assert "line" in record
    # Extra fields appear at the top level
    assert record["user_id"] == 42


def test_sanitizing_formatter_masks_authorization():
    """The SanitizingJSONFormatter masks Authorization values in messages."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(SanitizingJSONFormatter())

    logger = logging.getLogger("sanitize_test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Authorization: Bearer sk-abcdef123456")
    output = buf.getvalue()
    record = json.loads(output.strip())

    assert "sk-abcdef123456" not in record["message"]
    assert "****" in record["message"]
