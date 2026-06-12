# Queue, Rate Limit & Metrics Foundation

## Overview

This module provides three cross-cutting infrastructure capabilities for the
Finsight CFO backend:

1. **Task Queue** — an abstract `BaseQueue` interface with two backends:
   - `InProcessQueue` (in-memory `asyncio.Queue`, always available)
   - `RedisBackedQueue` (async Redis, auto-falls back to in-process if Redis is unreachable)
2. **Rate Limiting** — dual token-bucket middleware that limits HTTP requests
   per client IP and per `X-Workspace-ID` header. Enforced **only** in
   production mode (`APP_MODE=production`).
3. **Prometheus Metrics** — a `/metrics` endpoint exporting standard
   HTTP/application-level Prometheus counters, gauges, and histograms.

---

## Architecture

### Queue (`app/queue/`)

```
BaseQueue          (abstract, app/queue/base.py)
├── InProcessQueue (app/queue/in_process.py)
└── RedisBackedQueue (app/queue/redis_backend.py)
Factory            (app/queue/factory.py)
```

- Queue backend is selected via `settings.QUEUE_BACKEND`.
- `RedisBackedQueue` catches connection errors on init and falls back
  gracefully to `InProcessQueue`.

### Rate Limiting (`app/middleware/rate_limit.py`)

- Dual token-bucket algorithm.
- **Per-IP bucket** — keyed on `request.client.host`.
- **Per-Workspace bucket** — keyed on `X-Workspace-ID` header.
- Bucket state maintained in-memory via module-level dictionaries
  (`_ip_buckets`, `_ws_buckets`).
- Only enforced when `settings.APP_MODE == "production"`.
- Returns `429 Too Many Requests` with JSON error body when exhausted.

### Metrics (`app/routes/metrics.py`)

- Exposes `/metrics` GET endpoint in Prometheus text format.
- Tracks: `http_requests_total` (counter), `active_tasks` (gauge),
  `queue_depth` (gauge), `request_duration_seconds` (histogram).

---

## Configuration

All settings in `app/core/config.py`:

| Setting | Default | Description |
|---|---|---|
| `QUEUE_BACKEND` | `in_process` | `in_process` or `redis` |
| `QUEUE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `QUEUE_IN_PROCESS_MAXSIZE` | `0` (unlimited) | Max in-process queue size |
| `RATE_LIMIT_IP_RATE` | `10.0` | Per-IP refill rate (tokens/sec) |
| `RATE_LIMIT_IP_BURST` | `20.0` | Per-IP burst capacity |
| `RATE_LIMIT_WS_RATE` | `50.0` | Per-Workspace refill rate |
| `RATE_LIMIT_WS_BURST` | `100.0` | Per-Workspace burst capacity |

---

## Testing

Four test files cover the module:

| File | Tests |
|---|---|
| `tests/test_queue_backend.py` | 7 tests — enqueue/dequeue, timeout, ack/nack, length, flush, Redis fallback |
| `tests/test_rate_limit.py` | 3 tests — normal pass-through, IP exhaustion, WS exhaustion |
| `tests/test_logging.py` | 5 tests — sanitize messages/API keys, timestamps, JSON output, Authorization header masking |
| `tests/test_metrics.py` | 3 tests — endpoint 200, default metrics, finsight prefix |

---

## Known Limitations

- **Rate limit state is in-memory only** — restarting the server clears all
  buckets. No distributed rate limiting without an external store.
- **Queue doesn't persist to disk** — the in-process backend loses messages on
  restart. The Redis backend persists only as far as Redis does.
- **Metrics are single-instance** — no aggregation across multiple server
  replicas. Each pod/process exposes its own `/metrics`.
- **No automatic queue recovery** — if Redis reconnects after an initial
  failure, the backend stays on the in-process fallback.
