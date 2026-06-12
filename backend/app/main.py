from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.startup_checks import validate_startup_config
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
    # In a full deployment, this would verify DB and Redis connectivity.
    # For now, if the app reaches this point, we assume it's ready to handle traffic.
    return {"status": "ready"}

@app.get("/api/runtime/status")
def runtime_status():
    """
    Returns the current runtime configuration status without exposing secrets.
    """
    warnings = []
    
    if settings.APP_MODE == "production":
        if settings.normalized_auth_mode == "local":
            warnings.append("Auth mode is 'local' in production. This is highly unsafe for real data. Replace with real OIDC/SAML.")
        if settings.normalized_persistence_backend == "local":
            warnings.append("Persistence backend is 'local' in production. Database persistence should be enabled.")
        if getattr(settings, "STORAGE_BACKEND", "local") == "local":
            warnings.append("Storage backend is 'local' in production. Object storage should be configured.")
        if not getattr(settings, "REPORT_WORKER_ENABLED", False):
            warnings.append("Report worker is disabled. Async report generation will not function.")
            
    disclaimers = [
        "This platform is intended for demonstration and planning purposes.",
        "Ensure all secrets and API keys are stored securely outside the source tree."
    ]

    return {
        "app_version": getattr(settings, "APP_VERSION", "unknown"),
        "app_mode": settings.APP_MODE,
        "persistence_backend": settings.normalized_persistence_backend,
        "auth_mode": settings.normalized_auth_mode,
        "report_worker_enabled": getattr(settings, "REPORT_WORKER_ENABLED", False),
        "scheduler_mode": getattr(settings, "SCHEDULER_MODE", "manual"),
        "storage_mode": getattr(settings, "STORAGE_BACKEND", "local"),
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
