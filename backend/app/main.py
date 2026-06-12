from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.startup_checks import validate_startup_config
from app.core.log_config import setup_json_logging
from app.middleware.request_id import request_id_middleware
from app.middleware.rate_limit import rate_limit_middleware
from app.routes.market_watch import router as market_watch_router
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

app.include_router(market_watch_router, prefix="/api/market-watch")
app.include_router(financials_router, prefix="/api/financials")
app.include_router(advisory_router, prefix="/api/advisory")
app.include_router(data_room_router, prefix="/api/data-room")
app.include_router(workflow_router, prefix="/api/workflow")
app.include_router(cdi_router, prefix="/api/cdi")
app.include_router(gap_remediation_router, prefix="/api/gap-remediation")
app.include_router(workspaces_router, prefix="/api/workspaces")
app.include_router(jobs_router, prefix="/api/workspaces")
app.include_router(metrics_router)
