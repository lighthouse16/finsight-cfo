import logging
from datetime import datetime
from fastapi import HTTPException
from app.core.config import settings
from app.services.market_watch.hkma_client import hkma_client
from app.services.market_watch.cache import cache
from app.services.market_watch.fixtures import get_rates_liquidity_fixture
from app.models.market_watch import (
    RatesLiquidityResponse,
    ResponseMetadata,
    SourceInfo,
    RateSnapshot,
    LiquidityEvent,
    SourceStatusItem
)

logger = logging.getLogger(__name__)

CACHE_KEY = "rates_liquidity"

async def get_rates_liquidity() -> RatesLiquidityResponse:
    if settings.MARKET_WATCH_USE_FIXTURES:
        return get_rates_liquidity_fixture()

    # Try cache first
    cached_data = cache.get(CACHE_KEY)
    if cached_data:
        return cached_data

    # Upstream fetch
    try:
        hibor_records = await hkma_client.get_hibor_fixing()
        honia_records = await hkma_client.get_honia()
        liquidity_records = await hkma_client.get_interbank_liquidity()

        response = _normalize_data(hibor_records, honia_records, liquidity_records)
        
        # Cache the successful response
        cache.set(CACHE_KEY, response, settings.rates_ttl_seconds)
        
        return response
    except Exception as e:
        logger.error(f"Upstream fetch failed: {e}")
        stale_data: RatesLiquidityResponse = cache.get_stale(CACHE_KEY)
        
        if stale_data:
            stale_data.metadata.isStale = True
            stale_data.metadata.warnings = stale_data.metadata.warnings or []
            stale_data.metadata.warnings.append("HKMA upstream failed. Serving stale cache.")
            for status in stale_data.sourceStatus:
                status.status = "stale"
            return stale_data
            
        # No cache, upstream failed
        if settings.MARKET_WATCH_USE_FIXTURES:
            return get_rates_liquidity_fixture()
            
        raise HTTPException(
            status_code=503,
            detail={
                "code": "UPSTREAM_UNAVAILABLE",
                "message": "HKMA API is unavailable",
                "statusCode": 503,
                "source": "HKMA",
                "retryable": True,
                "fallbackUsed": False
            }
        )

def _normalize_data(hibor_records, honia_records, liquidity_records) -> RatesLiquidityResponse:
    now = datetime.utcnow().isoformat() + "Z"
    rates = []
    warnings = []
    
    latest_timestamp = None
    
    def update_latest_timestamp(date_str: str):
        nonlocal latest_timestamp
        if date_str:
            if not latest_timestamp or date_str > latest_timestamp:
                latest_timestamp = date_str

    def get_val(record: dict, keys: list):
        for k in keys:
            if k in record and record[k] is not None:
                return record[k]
        return None

    hibor_status = "unavailable"
    honia_status = "unavailable"
    liquidity_status = "unavailable"

    # Process HIBOR
    hibor_on_found = False
    if hibor_records:
        latest = hibor_records[0] # assuming sorted descending by date if offset=0 returns latest
        date = latest.get("end_of_day", latest.get("end_of_date"))
        if date:
            update_latest_timestamp(date)
        
        hibor_mappings = [
            (["ir_overnight", "ir_on", "hibor_overnight", "overnight"], "Overnight", "o/n"),
            (["ir_1m"], "1 Month", "1m"),
            (["ir_3m"], "3 Months", "3m"),
            (["ir_6m"], "6 Months", "6m"),
            (["ir_12m"], "12 Months", "12m"),
        ]
        
        for keys, label, tenor in hibor_mappings:
            val = get_val(latest, keys)
            if val is not None:
                try:
                    val_float = float(val)
                    display_str = str(val).strip() if isinstance(val, str) else str(val)
                    rates.append(RateSnapshot(
                        id=f"hibor-{tenor}",
                        label=f"HIBOR {label}",
                        tenor=tenor.upper(),
                        value=val_float,
                        unit="percent",
                        displayValue=f"{display_str}%",
                        changeBasisPoints=None,
                        trend="unknown",
                        context="HKMA fixing",
                        sourceTimestamp=date
                    ))
                    hibor_status = "connected"
                    if tenor == "o/n":
                        hibor_on_found = True
                except ValueError:
                    pass

    if not hibor_on_found:
        warnings.append("HIBOR overnight was not available in the HKMA response.")

    # Process HONIA
    if honia_records:
        latest = honia_records[0]
        date = latest.get("end_of_day", latest.get("end_of_date"))
        if date:
            update_latest_timestamp(date)
            
        val = get_val(latest, ["ir_honia", "honia", "ir_overnight", "overnight"])
        if val is not None:
            try:
                val_float = float(val)
                display_str = str(val).strip() if isinstance(val, str) else str(val)
                rates.append(RateSnapshot(
                    id="honia-on",
                    label="HONIA",
                    tenor="O/N",
                    value=val_float,
                    unit="percent",
                    displayValue=f"{display_str}%",
                    changeBasisPoints=None,
                    trend="unknown",
                    context="HKMA fixing",
                    sourceTimestamp=date
                ))
                honia_status = "connected"
            except ValueError:
                pass

    if honia_status == "unavailable":
        warnings.append("HONIA was not available in the HKMA response.")

    liquidity_events = []
    if liquidity_records:
        latest = liquidity_records[0]
        date = latest.get("end_of_day", latest.get("end_of_date"))
        if date:
            update_latest_timestamp(date)
        
        liq_mappings = [
            (["o_aggr_bal", "opening_aggregate_balance"], "Opening Aggregate Balance", "Contextual liquidity level"),
            (["c_aggr_bal", "closing_aggregate_balance"], "Closing Aggregate Balance", "Contextual liquidity level"),
            (["f_aggr_bal_t1", "forecast_aggregate_balance_t1"], "Forecast Aggregate Balance T+1", "Forecasted liquidity"),
            (["f_aggr_bal_t2", "forecast_aggregate_balance_t2"], "Forecast Aggregate Balance T+2", "Forecasted liquidity"),
            (["base_rate", "discount_window_base_rate"], "Discount Window Base Rate", "Policy rate context"),
        ]
        
        for keys, label, impact in liq_mappings:
            val = get_val(latest, keys)
            if val is not None:
                liquidity_status = "connected"
                event_str = f"{label}: {val}%" if "Rate" in label else f"{label}: {val}"
                liquidity_events.append(LiquidityEvent(
                    id=f"hkma-{keys[0]}",
                    date=date or now,
                    event=event_str,
                    impact=impact,
                    severity="Neutral"
                ))

    if not liquidity_events:
        warnings.append("Interbank liquidity records were unavailable or could not be normalized.")

    normalized_timestamps = [
        rate.sourceTimestamp for rate in rates if rate.sourceTimestamp
    ] + [
        event.date for event in liquidity_events if event.date
    ]
    latest_normalized_timestamp = max(normalized_timestamps) if normalized_timestamps else None

    metadata = ResponseMetadata(
        asOf=latest_normalized_timestamp,
        fetchedAt=now,
        freshness="Daily",
        isStale=False,
        source=SourceInfo(
            provider="HKMA",
            name="HKMA Public API",
            url="https://api.hkma.gov.hk"
        ),
        warnings=warnings
    )
    
    source_status = [
        SourceStatusItem(
            id="hkma-hibor",
            label="HKMA HIBOR",
            status=hibor_status,
            provider="HKMA",
            lastUpdatedAt=latest_timestamp
        ),
        SourceStatusItem(
            id="hkma-honia",
            label="HKMA HONIA",
            status=honia_status,
            provider="HKMA",
            lastUpdatedAt=latest_timestamp
        ),
        SourceStatusItem(
            id="hkma-liquidity",
            label="HKMA Liquidity",
            status=liquidity_status,
            provider="HKMA",
            lastUpdatedAt=latest_timestamp
        )
    ]

    return RatesLiquidityResponse(
        metadata=metadata,
        rates=rates,
        liquidityEvents=liquidity_events,
        sourceStatus=source_status
    )
