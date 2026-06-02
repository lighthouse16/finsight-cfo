from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.market_watch import router as market_watch_router

app = FastAPI(title="FinSight CFO API")

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "finsight-cfo-api"}

app.include_router(market_watch_router, prefix="/api/market-watch")
