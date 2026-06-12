from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, get_settings
from app.core.startup_checks import validate_startup_config
from app.core.log_config import setup_json_logging
from app.middleware.request_id import request_id_middleware
from app.middleware.rate_limit import rate_limit_middleware
from app.routes.market_watch import router as market_watch_router
from app.routes.market_funding import router as market_funding_router
from app.routes.financials import router as financials_router
from app.routes.advisory import router as advisory_router
from app.routes.data_room import router as data_room_router
from app.routes.workflow import router as workflow_router
from app.routes.cdi import router as cdi_router
from app.routes.gap_remediation import router as gap_remediation_router
from app.routes.workspaces import router as workspaces_router
from app.routes.jobs import router as jobs_router
from app.routes.metrics import router as metrics_router

logger = setup_json_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup config check
    validate_startup_config(settings)
    logger.info("FinSight CFO API started", extra={"mode": settings.APP_MODE})
    yield

app = FastAPI(title="FinSight CFO API", lifespan=lifespan)

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Internal middlewares (request_id first, then rate_limit)
app.middleware("http")(request_id_middleware)
app.middleware("http")(rate_limit_middleware)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "finsight-cfo-api"}

@app.get("/ready")
def readiness_check():
    from fastapi import HTTPException
    checks = {}
    failed = False

    if settings.normalized_persistence_backend == "database":
        try:
            from sqlalchemy import text
            from app.db.session import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "failed"
            failed = True
    else:
        checks["database"] = "not_applicable"

    # Normalize queue backend comparison
    q_backend = getattr(settings, "QUEUE_BACKEND", "").strip().lower()
    if q_backend in ("redis", "local"):
        try:
            import redis
            r = redis.Redis.from_url(settings.QUEUE_REDIS_URL, socket_connect_timeout=2.0)
            r.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "failed"
            # If queue backend is 'local', redis is optional; but if it is 'redis' we fail
            if q_backend == "redis":
                failed = True
    else:
        checks["redis"] = "not_applicable"

    if failed:
        raise HTTPException(
            status_code=503,
            detail={"status": "unready", "checks": checks}
        )
    return {"status": "ready", "checks": checks}

@app.get("/api/runtime/status")
def runtime_status():
    """
    Returns the current runtime configuration status without exposing secrets.
    """
    st = get_settings()
    warnings = []

    if st.APP_MODE == "production":
        if st.normalized_auth_mode == "local":
            warnings.append("Auth mode is 'local' in production. This is highly unsafe for real data. Replace with real OIDC/SAML.")
        if st.normalized_persistence_backend == "local":
            warnings.append("Persistence backend is 'local' in production. Database persistence should be enabled.")
        if getattr(st, "STORAGE_BACKEND", "local") == "local":
            warnings.append("Storage backend is 'local' in production. Object storage should be configured.")
        if not getattr(st, "REPORT_WORKER_ENABLED", False):
            warnings.append("Report worker is disabled. Async report generation will not function.")
        if not st.is_llm_configured:
            warnings.append("AI LLM provider is not configured. AI CFO will operate in deterministic fallback mode.")

    # Queue backend warning
    qb = st.normalized_queue_backend
    if qb == "in_process" and st.APP_MODE == "production":
        warnings.append(f"Queue backend is '{qb}' in production. Consider configuring Redis/Celery for async jobs.")

    disclaimers = [
        "This platform is intended for demonstration and planning purposes.",
        "Ensure all secrets and API keys are stored securely outside the source tree."
    ]

    return {
        "app_version": getattr(st, "APP_VERSION", "unknown"),
        "app_mode": st.APP_MODE,
        "persistence_backend": st.normalized_persistence_backend,
        "auth_mode": st.normalized_auth_mode,
        "report_worker_enabled": getattr(st, "REPORT_WORKER_ENABLED", False),
        "scheduler_mode": getattr(st, "SCHEDULER_MODE", "manual"),
        "storage_mode": getattr(st, "STORAGE_BACKEND", "local"),
        "ai_mode": st.normalized_ai_mode,
        "ai_provider_configured": st.is_llm_configured,
        "queue_backend": qb,
        "warnings": warnings,
        "disclaimers": disclaimers
    }

app.include_router(market_watch_router, prefix="/api/market-watch")
app.include_router(market_funding_router, prefix="/api/market-funding")
app.include_router(financials_router, prefix="/api/financials")
app.include_router(advisory_router, prefix="/api/advisory")
app.include_router(data_room_router, prefix="/api/data-room")
app.include_router(workflow_router, prefix="/api/workflow")
app.include_router(cdi_router, prefix="/api/cdi")
app.include_router(gap_remediation_router, prefix="/api/gap-remediation")
app.include_router(workspaces_router, prefix="/api/workspaces")
app.include_router(jobs_router, prefix="/api/workspaces")
app.include_router(metrics_router)
