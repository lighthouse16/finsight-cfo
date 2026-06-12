import logging
from datetime import datetime
from app.core.config import settings
from app.services.market_watch.cache import cache
from app.services.market_watch.fx_client import FrankfurterClient
from app.services.market_watch.fixtures import get_fx_gba_fixture
from app.models.market_watch import (
    FxGbaResponse,
    FxPair,
    GbaFundingSignal,
    ExposureNote,
    SourceStatusItem,
    ResponseMetadata,
    SourceInfo
)

logger = logging.getLogger(__name__)

CACHE_KEY_FX = "fx_gba"

async def get_fx_gba() -> FxGbaResponse:
    is_production = settings.APP_MODE == "production" or not settings.ALLOW_DEMO_FALLBACK
    if settings.MARKET_WATCH_USE_FIXTURES:
        if is_production:
            from app.models.errors import raise_upstream_unavailable_error
            raise_upstream_unavailable_error()
        return get_fx_gba_fixture()

    cached_data = cache.get(CACHE_KEY_FX)
    if cached_data:
        return cached_data

    client = FrankfurterClient()
    try:
        rates_data = await client.fetch_fx_rates()
        
        is_v2 = rates_data.get("is_v2", False)
        
        usd_hkd = None
        usd_cny = None
        cny_hkd = None
        
        usd_date = None
        cny_date = None
        
        if is_v2:
            usd_list = rates_data.get("usd", [])
            cny_list = rates_data.get("cny", [])
            
            for item in usd_list:
                usd_date = item.get("date")
                if item.get("quote") == "HKD":
                    usd_hkd = item.get("rate")
                elif item.get("quote") == "CNY":
                    usd_cny = item.get("rate")
                    
            for item in cny_list:
                cny_date = item.get("date")
                if item.get("quote") == "HKD":
                    cny_hkd = item.get("rate")
        else:
            usd_res = rates_data.get("usd", {})
            cny_res = rates_data.get("cny", {})
            
            usd_rates = usd_res.get("rates", {})
            cny_rates = cny_res.get("rates", {})
            
            usd_hkd = usd_rates.get("HKD")
            usd_cny = usd_rates.get("CNY")
            cny_hkd = cny_rates.get("HKD")
            
            usd_date = usd_res.get("date")
            cny_date = cny_res.get("date")
            
        warnings = []
        derived_usd_hkd = False
        derived_usd_cny = False
        derived_cny_hkd = False
        
        # Cross rate derivation
        if usd_hkd is None and usd_cny is not None and cny_hkd is not None:
            usd_hkd = usd_cny * cny_hkd
            warnings.append("USD/HKD derived from CNY/HKD and USD/CNY.")
            derived_usd_hkd = True
            
        if usd_cny is None and usd_hkd is not None and cny_hkd is not None:
            if cny_hkd != 0:
                usd_cny = usd_hkd / cny_hkd
                warnings.append("USD/CNY derived from USD/HKD and CNY/HKD.")
                derived_usd_cny = True
                
        if cny_hkd is None and usd_hkd is not None and usd_cny is not None:
            if usd_cny != 0:
                cny_hkd = usd_hkd / usd_cny
                warnings.append("CNY/HKD derived from USD/HKD and USD/CNY.")
                derived_cny_hkd = True
                
        if usd_hkd is None:
            warnings.append("USD/HKD rate unavailable.")
        if usd_cny is None:
            warnings.append("USD/CNY rate unavailable.")
        if cny_hkd is None:
            warnings.append("CNY/HKD rate unavailable.")
            
        # If all failed, trigger fallback to fixture
        if usd_hkd is None and usd_cny is None and cny_hkd is None:
            raise Exception("All provider FX rates failed to load or derive.")
            
        now = datetime.utcnow().isoformat() + "Z"
        
        metadata = ResponseMetadata(
            asOf=usd_date or cny_date or "2026-06",
            fetchedAt=now,
            freshness="Daily",
            isStale=False,
            source=SourceInfo(
                provider="Frankfurter",
                name="Frankfurter FX Provider"
            ),
            warnings=warnings
        )
        
        fx_pairs = [
            FxPair(
                id="usd-hkd",
                pair="USD/HKD",
                value=usd_hkd,
                unit="price",
                displayValue=f"{usd_hkd:.4f}" if usd_hkd is not None else "N/A",
                trend="flat",
                changePips=0,
                context="Peg reference (derived)" if derived_usd_hkd else "Peg reference",
                sourceTimestamp=usd_date
            ),
            FxPair(
                id="cny-hkd",
                pair="CNY/HKD",
                value=cny_hkd,
                unit="price",
                displayValue=f"{cny_hkd:.4f}" if cny_hkd is not None else "N/A",
                trend="flat",
                changePips=0,
                context="Cross rate (derived)" if derived_cny_hkd else "Cross rate",
                sourceTimestamp=cny_date
            ),
            FxPair(
                id="usd-cny",
                pair="USD/CNY",
                value=usd_cny,
                unit="price",
                displayValue=f"{usd_cny:.4f}" if usd_cny is not None else "N/A",
                trend="flat",
                changePips=0,
                context="Base reference (derived)" if derived_usd_cny else "Base reference",
                sourceTimestamp=usd_date
            )
        ]
        
        gba_signals = [
            GbaFundingSignal(
                id="gba-signal-1",
                title="Rates connected via Frankfurter",
                description="Cross-border FX rates remain connected and within normal volatility ranges.",
                severity="Positive"
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
                status="connected",
                provider="Frankfurter",
                lastUpdatedAt=now
            )
        ]
        
        from app.services.market_watch.source_registry import build_provenance
        from app.models.market_watch import SourceProvenance
        prov = SourceProvenance(**build_provenance("fx_gba_v1", as_of=now))

        response = FxGbaResponse(
            metadata=metadata,
            fxPairs=fx_pairs,
            gbaFundingSignal=gba_signals,
            exposureNotes=exposure_notes,
            sourceStatus=source_status,
            provenance=prov
        )
        
        cache.set(CACHE_KEY_FX, response, settings.rates_ttl_seconds)
        return response
        
    except Exception as e:
        logger.error(f"Frankfurter FX fetch failed: {e}")
        stale_data: FxGbaResponse = cache.get_stale(CACHE_KEY_FX)
        if stale_data:
            stale_data.metadata.isStale = True
            stale_data.metadata.warnings = stale_data.metadata.warnings or []
            stale_data.metadata.warnings.append("Frankfurter upstream failed. Serving stale cache.")
            for status in stale_data.sourceStatus:
                status.status = "stale"
            return stale_data
            
        # Fallback to fixture
        if is_production:
            from app.models.errors import raise_upstream_unavailable_error
            raise_upstream_unavailable_error("FX provider is unavailable")
        res = get_fx_gba_fixture()
        res.metadata.warnings = [
            "FX provider is not configured or unavailable. Showing workspace seed data."
        ]
        from app.services.market_watch.source_registry import build_provenance
        from app.models.market_watch import SourceProvenance
        res.provenance = SourceProvenance(**build_provenance("fx_gba_v1"))
        return res
