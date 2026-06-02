from datetime import datetime
from app.models.market_watch import (
    RatesLiquidityResponse,
    ResponseMetadata,
    SourceInfo,
    RateSnapshot,
    LiquidityEvent,
    SourceStatusItem
)

def get_rates_liquidity_fixture() -> RatesLiquidityResponse:
    now = datetime.utcnow().isoformat() + "Z"
    
    metadata = ResponseMetadata(
        asOf=now,
        fetchedAt=now,
        freshness="Workspace",
        isStale=False,
        source=SourceInfo(
            provider="FinSight Local",
            name="Seed Data",
        ),
        warnings=["Using local seed data fixture"]
    )

    rates = [
        RateSnapshot(
            id="hibor-1m",
            label="HIBOR",
            tenor="1M",
            value=4.25,
            unit="percent",
            displayValue="4.25%",
            changeBasisPoints=0,
            trend="flat",
            context="Local fixture",
            sourceTimestamp=now
        )
    ]

    liquidity_events = [
        LiquidityEvent(
            id="fixture-event",
            date=now,
            event="Aggregate Balance Stable",
            impact="Normal liquidity conditions",
            severity="Neutral"
        )
    ]

    source_status = [
        SourceStatusItem(
            id="hkma",
            label="HKMA Rates",
            status="seed_data",
            provider="HKMA"
        )
    ]

    return RatesLiquidityResponse(
        metadata=metadata,
        rates=rates,
        liquidityEvents=liquidity_events,
        sourceStatus=source_status
    )
