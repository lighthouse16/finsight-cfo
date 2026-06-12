"""
Structured JSON logging for FinSight CFO.

Provides a custom logging.Formatter that emits JSON lines with:
- ISO-8601 timestamps (always valid on Windows Python 3.11 by avoiding strftime %f)
- Log level, logger name, message, module info
- Automatic credential masking in message strings
- Exception info and extra contextual fields included when available
"""

import datetime
import json
import logging
import re
import sys
import types


# Patterns that match credential prefixes followed by the full value.
# Group 1 must capture the prefix (including separator) so that
# r"\1****" replaces the value with "****".
SENSITIVE_PATTERNS: list[re.Pattern] = [
    # Authorization: Bearer <token>
    re.compile(r"(?i)(Authorization:\s*).*"),
    # apikey/apikey-secret in header or query forms
    re.compile(r"(?i)(apikey[=:]\s*)\S+"),
    re.compile(r"(?i)(api_key[=:]\s*)\S+"),
    # x-api-key header
    re.compile(r"(?i)(x-api-key[=:]\s*)\S+"),
]


def sanitize_message(msg: str) -> str:
    """Mask sensitive credential patterns in *msg*."""
    for pattern in SENSITIVE_PATTERNS:
        msg = pattern.sub(r"\1****", msg)
    return msg


# Standard LogRecord attributes that should NOT be promoted as extras.
_STANDARD_KEYS = {
    "name", "levelno", "levelname", "pathname", "filename", "module",
    "lineno", "funcName", "created", "asctime", "msecs", "relativeCreated",
    "thread", "threadName", "process", "message", "msg", "args", "exc_info",
    "exc_text", "stack_info",
}


class SanitizingJSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects with sanitized payloads."""

    def format(self, record: logging.LogRecord) -> str:
        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        log_obj = {
            "timestamp": dt.isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0]:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include any extra contextual fields that were passed
        # via the `extra` parameter to the logging call.
        for key, value in record.__dict__.items():
            if key not in _STANDARD_KEYS:
                log_obj[key] = value

        return json.dumps(log_obj, default=str)


def setup_json_logging(
    logger_name: str = "finsight",
    level: int = logging.INFO,
    stream: types.ModuleType = sys.stderr,
) -> logging.Logger:
    """
    Configure and return a JSON-structured logger.

    Usage:
        logger = setup_json_logging()
        logger.info("Task complete", extra={"task_id": "abc"})
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates on re-init
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    handler = logging.StreamHandler(stream)
    handler.setFormatter(SanitizingJSONFormatter())
    logger.addHandler(handler)

    return logger
