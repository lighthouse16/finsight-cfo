from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.market_watch import router as market_watch_router
from app.routes.financials import router as financials_router
from app.routes.advisory import router as advisory_router
from app.routes.data_room import router as data_room_router
from app.routes.workflow import router as workflow_router
from app.routes.cdi import router as cdi_router
from app.routes.gap_remediation import router as gap_remediation_router

app = FastAPI(title="FinSight CFO API")

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
