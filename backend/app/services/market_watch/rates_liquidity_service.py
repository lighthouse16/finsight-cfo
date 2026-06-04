import logging
from datetime import datetime
from fastapi import HTTPException
from app.core.config import settings
from app.services.market_watch.hkma_client import hkma_client
from app.services.market_watch.cache import cache
from app.services.market_watch.fixtures import get_rates_liquidity_fixture
from app.services.market_watch.hkab_web_client import hkab_web_client
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
    hkab_data = None
    hibor_records = []
    honia_records = []
    liquidity_records = []

    try:
        hkab_data = await hkab_web_client.fetch_latest_hibor()
    except Exception as e:
        logger.error(f"Failed to fetch primary HKAB HIBOR: {e}")

    if not hkab_data:
        try:
            hibor_records = await hkma_client.get_hibor_fixing()
        except Exception as e:
            logger.error(f"Failed to fetch fallback HKMA HIBOR: {e}")

    try:
        honia_records = await hkma_client.get_honia()
    except Exception as e:
        logger.error(f"Failed to fetch HKMA HONIA: {e}")

    try:
        liquidity_records = await hkma_client.get_interbank_liquidity()
    except Exception as e:
        logger.error(f"Failed to fetch HKMA interbank liquidity: {e}")

    # If absolutely all upstream sources failed, trigger fallback flow
    if not hkab_data and not hibor_records and not honia_records and not liquidity_records:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "UPSTREAM_UNAVAILABLE",
                "message": "All HKMA/HKAB upstream sources are unavailable",
                "statusCode": 503,
                "source": "HKMA/HKAB",
                "retryable": True,
                "fallbackUsed": False
            }
        )

    try:
        response = _normalize_data(hibor_records, honia_records, liquidity_records, hkab_data)
        
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

def _normalize_data(hibor_records, honia_records, liquidity_records, hkab_data=None) -> RatesLiquidityResponse:
    now = datetime.utcnow().isoformat() + "Z"
    rates = []
    warnings = []
    
    # Sort helper to ensure we process the latest record first regardless of upstream ordering
    def sort_records(records):
        if not records:
            return []
        def get_rec_date(r):
            return r.get("end_of_day") or r.get("end_of_date") or ""
        return sorted(records, key=get_rec_date, reverse=True)

    hibor_records = sort_records(hibor_records)
    honia_records = sort_records(honia_records)
    liquidity_records = sort_records(liquidity_records)

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

    hkab_status = "unavailable"
    hkab_date = None
    hibor_status = "unavailable"
    honia_status = "unavailable"
    liquidity_status = "unavailable"
    
    hkma_hibor_date = None
    hkma_honia_date = None
    hkma_liquidity_date = None

    # Process HIBOR
    hibor_on_found = False
    
    if hkab_data:
        hkab_date = hkab_data.get("source_date")
        if hkab_date:
            update_latest_timestamp(hkab_date)
        
        hkab_mappings = [
            ("Overnight", "Overnight", "o/n"),
            ("1 Month", "1 Month", "1m"),
            ("3 Months", "3 Months", "3m"),
            ("6 Months", "6 Months", "6m"),
            ("12 Months", "12 Months", "12m"),
        ]
        
        hkab_rates = hkab_data.get("rates", {})
        for hkab_key, label, tenor in hkab_mappings:
            if hkab_key in hkab_rates:
                val = hkab_rates[hkab_key]
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
                        context="HKAB HIBOR fixing",
                        sourceTimestamp=hkab_date
                    ))
                    hkab_status = "connected"
                    if tenor == "o/n":
                        hibor_on_found = True
                except ValueError:
                    pass
        
        # HKMA HIBOR is secondary/fallback
        hibor_status = "stale"
    else:
        # Fallback to HKMA Open API HIBOR
        warnings.append("HKAB HIBOR page unavailable. Using HKMA Open API fallback.")
        if hibor_records:
            latest = hibor_records[0]
            date = latest.get("end_of_day", latest.get("end_of_date"))
            hkma_hibor_date = date
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
        if hkab_data:
            warnings.append("HIBOR overnight was not available in the HKAB response.")
        else:
            warnings.append("HIBOR overnight was not available in the HKMA response.")

    # Process HONIA
    if honia_records:
        latest = honia_records[0]
        date = latest.get("end_of_day", latest.get("end_of_date"))
        hkma_honia_date = date
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
                    context="HKMA HONIA fixing",
                    sourceTimestamp=date
                ))
                honia_status = "connected"
            except ValueError:
                pass

    if honia_status == "unavailable":
        warnings.append("HKMA HONIA data was unavailable from the source response.")

    # Process Liquidity events
    expected_fields_mappings = [
        ["opening_balance", "o_aggr_bal", "opening_aggregate_balance"],
        ["closing_balance", "c_aggr_bal", "closing_aggregate_balance"],
        ["forecast_aggregate_bal_t1", "f_aggr_bal_t1", "forecast_aggregate_balance_t1"],
        ["disc_win_base_rate", "base_rate", "discount_window_base_rate"]
    ]
    has_all_expected = False
    if liquidity_records:
        latest = liquidity_records[0]
        has_all_expected = all(
            get_val(latest, keys) is not None for keys in expected_fields_mappings
        )

    liquidity_events = []
    if liquidity_records and has_all_expected:
        latest = liquidity_records[0]
        date = latest.get("end_of_day", latest.get("end_of_date"))
        hkma_liquidity_date = date
        if date:
            update_latest_timestamp(date)
        
        liq_mappings = [
            (["opening_balance", "o_aggr_bal", "opening_aggregate_balance"], "Opening Aggregate Balance", "Contextual liquidity level"),
            (["closing_balance", "c_aggr_bal", "closing_aggregate_balance"], "Closing Aggregate Balance", "Contextual liquidity level"),
            (["forecast_aggregate_bal_t1", "f_aggr_bal_t1", "forecast_aggregate_balance_t1"], "Forecast Aggregate Balance T+1", "Forecasted liquidity"),
            (["forecast_aggregate_bal_t2", "f_aggr_bal_t2", "forecast_aggregate_balance_t2"], "Forecast Aggregate Balance T+2", "Forecasted liquidity"),
            (["disc_win_base_rate", "base_rate", "discount_window_base_rate"], "Discount Window Base Rate", "Policy rate context"),
            (["interest_payment_issuance_efbn_t1", "efbn_t1"], "Exchange Fund Paper Net Issuance (T+1)", "Net impact of EFBN issuance and interest payments"),
            (["interest_payment_issuance_efbn_t2", "efbn_t2"], "Exchange Fund Paper Net Issuance (T+2)", "Net impact of EFBN issuance and interest payments"),
        ]
        
        for keys, label, impact in liq_mappings:
            val = get_val(latest, keys)
            if val is not None:
                liquidity_status = "connected"
                if "Rate" in label:
                    formatted_val = f"{val}%"
                elif "Balance" in label or "Exchange Fund Paper" in label:
                    try:
                        val_str = str(val).strip()
                        is_neg = val_str.startswith('-')
                        clean_str = val_str.lstrip('+-')
                        if clean_str:
                            val_int = int(clean_str)
                            formatted_val = f"HKD {'-' if is_neg else ''}{val_int:,}M"
                        else:
                            formatted_val = str(val)
                    except ValueError:
                        formatted_val = f"{val} HKD Million"
                else:
                    formatted_val = str(val)

                event_str = f"{label}: {formatted_val}"
                liquidity_events.append(LiquidityEvent(
                    id=f"hkma-{keys[0]}",
                    date=date or now,
                    event=event_str,
                    impact=impact,
                    severity="Neutral"
                ))
    else:
        if liquidity_records:
            hkma_liquidity_date = liquidity_records[0].get("end_of_day", liquidity_records[0].get("end_of_date"))

    if not liquidity_events:
        if not liquidity_records:
            warnings.append("HKMA interbank liquidity records were unavailable from the public API source.")
        else:
            warnings.append("HKMA interbank liquidity records could not be normalized due to missing expected fields (opening_balance, closing_balance, forecast_aggregate_bal_t1, disc_win_base_rate).")

    primary_hibor_date = hkab_date if hkab_data else hkma_hibor_date

    metadata = ResponseMetadata(
        asOf=primary_hibor_date,
        fetchedAt=now,
        freshness="Daily",
        isStale=False,
        source=SourceInfo(
            provider="HKAB / HKMA",
            name="HKAB and HKMA Public Data",
            url="https://www.hkab.org.hk"
        ),
        warnings=warnings
    )
    
    source_status = [
        SourceStatusItem(
            id="hkab-hibor",
            label="HKAB HIBOR",
            status=hkab_status,
            provider="HKAB",
            lastUpdatedAt=hkab_date
        ),
        SourceStatusItem(
            id="hkma-hibor",
            label="HKMA HIBOR",
            status=hibor_status,
            provider="HKMA",
            lastUpdatedAt=hkma_hibor_date
        ),
        SourceStatusItem(
            id="hkma-honia",
            label="HKMA HONIA",
            status=honia_status,
            provider="HKMA",
            lastUpdatedAt=hkma_honia_date
        ),
        SourceStatusItem(
            id="hkma-liquidity",
            label="HKMA Liquidity",
            status=liquidity_status,
            provider="HKMA",
            lastUpdatedAt=hkma_liquidity_date
        )
    ]

    return RatesLiquidityResponse(
        metadata=metadata,
        rates=rates,
        liquidityEvents=liquidity_events,
        sourceStatus=source_status
    )
