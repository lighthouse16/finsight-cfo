from datetime import datetime
from app.models.market_watch import (
    RatesLiquidityResponse,
    ResponseMetadata,
    SourceInfo,
    RateSnapshot,
    LiquidityEvent,
    SourceStatusItem,
    FxGbaResponse,
    FxPair,
    GbaFundingSignal,
    ExposureNote
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

def get_fx_gba_fixture() -> FxGbaResponse:
    now = datetime.utcnow().isoformat() + "Z"

    metadata = ResponseMetadata(
        asOf=now,
        fetchedAt=now,
        freshness="Workspace",
        isStale=False,
        source=SourceInfo(
            provider="Fixture",
            name="Workspace seed data",
        ),
        warnings=["FX & GBA endpoint is currently fixture-backed. Production FX provider is not connected yet."]
    )

    fx_pairs = [
        FxPair(
            id="usd-hkd",
            pair="USD/HKD",
            value=7.8245,
            unit="price",
            displayValue="7.8245",
            trend="flat",
            changePips=0,
            context="Peg reference",
            sourceTimestamp=now
        ),
        FxPair(
            id="cny-hkd",
            pair="CNY/HKD",
            value=1.0820,
            unit="price",
            displayValue="1.0820",
            trend="flat",
            changePips=0,
            context="Cross rate",
            sourceTimestamp=now
        ),
        FxPair(
            id="usd-cny",
            pair="USD/CNY",
            value=7.2310,
            unit="price",
            displayValue="7.2310",
            trend="flat",
            changePips=0,
            context="Base reference",
            sourceTimestamp=now
        )
    ]

    gba_signals = [
        GbaFundingSignal(
            id="gba-signal-1",
            title="Cross-border funding context pending provider connection",
            description="FX and rate-spread context will be evaluated once FX provider and LPR source are connected.",
            severity="Neutral"
        )
    ]

    exposure_notes = [
        ExposureNote(
            id="note-1",
            category="Import",
            note="Import cost sensitivity to USD strength.",
            severity="Caution"
        ),
        ExposureNote(
            id="note-2",
            category="Repatriation",
            note="Repatriated earnings exposure from CNY operations.",
            severity="Neutral"
        ),
        ExposureNote(
            id="note-3",
            category="Funding",
            note="RMB funding context pending source connection.",
            severity="Neutral"
        ),
        ExposureNote(
            id="note-4",
            category="Volatility",
            note="FX volatility watch on cross-border payables.",
            severity="Caution"
        )
    ]

    source_status = [
        SourceStatusItem(
            id="fx-provider",
            label="FX Provider",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="gba-context",
            label="GBA Context",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="lpr-source",
            label="LPR Source",
            status="requires_backend",
            provider="Pending"
        )
    ]

    return FxGbaResponse(
        metadata=metadata,
        fxPairs=fx_pairs,
        gbaFundingSignal=gba_signals,
        exposureNotes=exposure_notes,
        sourceStatus=source_status
    )
