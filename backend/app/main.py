from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.startup_checks import validate_startup_config
from app.routes.market_watch import router as market_watch_router
from app.routes.financials import router as financials_router
from app.routes.advisory import router as advisory_router
from app.routes.data_room import router as data_room_router
from app.routes.workflow import router as workflow_router
from app.routes.cdi import router as cdi_router
from app.routes.gap_remediation import router as gap_remediation_router
from app.routes.workspaces import router as workspaces_router
from app.routes.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup config check
    validate_startup_config(settings)
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

    if getattr(settings, "QUEUE_BACKEND", "").strip().lower() == "redis":
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2.0)
            r.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "failed"
            failed = True
    else:
        checks["redis"] = "not_applicable"

    if failed:
        raise HTTPException(
            status_code=503,
            detail={"status": "unready", "checks": checks}
        )
    return {"status": "ready", "checks": checks}

app.include_router(market_watch_router, prefix="/api/market-watch")
app.include_router(financials_router, prefix="/api/financials")
app.include_router(advisory_router, prefix="/api/advisory")
app.include_router(data_room_router, prefix="/api/data-room")
app.include_router(workflow_router, prefix="/api/workflow")
app.include_router(cdi_router, prefix="/api/cdi")
app.include_router(gap_remediation_router, prefix="/api/gap-remediation")
app.include_router(workspaces_router, prefix="/api/workspaces")
app.include_router(jobs_router, prefix="/api/workspaces")
