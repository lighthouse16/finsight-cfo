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
from app.routes.auth import router as auth_router
from app.core.rate_limit import RateLimiter
from fastapi import Depends


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup config check
    validate_startup_config(settings)
    yield

global_dependencies = []
if settings.APP_MODE == "production":
    global_dependencies.append(Depends(RateLimiter(max_tokens=100, refill_rate=10.0)))

app = FastAPI(title="FinSight CFO API", lifespan=lifespan, dependencies=global_dependencies)

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

from app.core.auth import get_request_context

app.include_router(auth_router, prefix="/api/auth")
app.include_router(market_watch_router, prefix="/api/market-watch", dependencies=[Depends(get_request_context)])
app.include_router(financials_router, prefix="/api/financials", dependencies=[Depends(get_request_context)])
app.include_router(advisory_router, prefix="/api/advisory", dependencies=[Depends(get_request_context)])
app.include_router(data_room_router, prefix="/api/data-room", dependencies=[Depends(get_request_context)])
app.include_router(workflow_router, prefix="/api/workflow", dependencies=[Depends(get_request_context)])
app.include_router(cdi_router, prefix="/api/cdi", dependencies=[Depends(get_request_context)])
app.include_router(gap_remediation_router, prefix="/api/gap-remediation", dependencies=[Depends(get_request_context)])
app.include_router(workspaces_router, prefix="/api/workspaces", dependencies=[Depends(get_request_context)])
app.include_router(jobs_router, prefix="/api/workspaces", dependencies=[Depends(get_request_context)])
