from typing import Optional
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
    ExposureNote,
    SectorBenchmarksResponse,
    SelectedSector,
    SectorHealth,
    SectorHealthComponents,
    SectorHealthComponent,
    SectorBenchmark,
    SectorWatchSignal,
    CommoditiesResponse,
    CommodityExposure,
    MarginPressureSignal,
    CommodityWatchSignal
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


def get_sector_benchmarks_fixture(sector: Optional[str] = None, geography: Optional[str] = None) -> SectorBenchmarksResponse:
    now = datetime.utcnow().isoformat() + "Z"
    
    # Determine which sector context to return
    target_sector = (sector or "trading-distribution").lower().strip()
    target_geo = geography or "HK"
    
    metadata = ResponseMetadata(
        asOf="2026-05", # fixture month
        fetchedAt=now,
        freshness="Workspace",
        isStale=False,
        source=SourceInfo(
            provider="Fixture",
            name="Workspace sector benchmark seed data"
        ),
        warnings=["Sector Benchmarks endpoint is currently fixture-backed. Production sector provider is not connected yet."]
    )
    
    source_status = [
        SourceStatusItem(
            id="sector-benchmark-provider",
            label="Sector Benchmark Provider",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="industry-health-provider",
            label="Industry Health Provider",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="company-sector-profile",
            label="Company Sector Profile",
            status="requires_company_data",
            provider="Pending"
        )
    ]
    
    if target_sector == "electronics-import":
        selected_sector = SelectedSector(
            id="electronics-import",
            name="Electronics Import",
            code="HK-SME-ELC",
            geography=target_geo,
            description="SMEs engaged in electronic components sourcing and regional distribution."
        )
        
        sector_health = SectorHealth(
            score=71.0,
            label="Stable expansion",
            severity="Positive",
            components=SectorHealthComponents(
                pmi=SectorHealthComponent(
                    label="PMI",
                    value=52.4,
                    unit="index",
                    displayValue="52.4",
                    context="Expansion zone watch. Indicates steady sector demand."
                ),
                exportGrowth=SectorHealthComponent(
                    label="Export Growth",
                    value=3.2,
                    unit="percent",
                    displayValue="+3.2%",
                    context="Stable external demand for electronic components."
                ),
                industrialProduction=SectorHealthComponent(
                    label="Industrial Production",
                    value=4.0,
                    unit="percent",
                    displayValue="+4.0%",
                    context="Electronics output expansion supported by components backlog."
                ),
                marginContext=SectorHealthComponent(
                    label="Margin Context",
                    value=None,
                    unit="text",
                    displayValue="Stable component pricing",
                    context="Subdued components price volatility keeps operating margins steady."
                )
            )
        )
        
        benchmarks = [
            SectorBenchmark(
                id="dso",
                label="Days Sales Outstanding",
                value=38.0,
                unit="days",
                displayValue="38 days",
                comparison="Compared to industry standard (40 days)",
                context="Strong collections discipline and credit term enforcement.",
                severity="Positive",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="dio",
                label="Inventory Days",
                value=48.0,
                unit="days",
                displayValue="48 days",
                comparison="Compared to industry standard (50 days)",
                context="Efficient warehouse throughput and high inventory turnover.",
                severity="Neutral",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="dpo",
                label="Days Payable Outstanding",
                value=42.0,
                unit="days",
                displayValue="42 days",
                comparison="Compared to industry standard (45 days)",
                context="Suppliers offering standard credit terms without surcharge.",
                severity="Neutral",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="gross-margin",
                label="Gross Margin Context",
                value=22.0,
                unit="percent",
                displayValue="22.0%",
                comparison="Compared to historical average (21.5%)",
                context="Favorable components product mix supports margins.",
                severity="Positive",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="documentation-readiness",
                label="Documentation Readiness",
                value=92.0,
                unit="percent",
                displayValue="92%",
                comparison="Compared to target (90%)",
                context="Excellent documentation completeness with automated export declarations.",
                severity="Positive",
                sourceTimestamp="2026-05"
            )
        ]
        
        watch_signals = [
            SectorWatchSignal(
                id="sig-1",
                title="Component Lead Times Stabilizing",
                description="Component lead times are stabilizing across major lanes. Monitor buffer inventory levels.",
                affectedArea="Inventory Management",
                severity="Positive"
            ),
            SectorWatchSignal(
                id="sig-2",
                title="High Compliance Facilitates Credit",
                description="High documentation compliance facilitates faster trade credit approval. Maintain records transparency.",
                affectedArea="Lender Readiness",
                severity="Positive"
            ),
            SectorWatchSignal(
                id="sig-3",
                title="Strong Cash Collection Buffer",
                description="High collections performance reduces reliance on short-term liquidity. Continue credit review policies.",
                affectedArea="Cashflow Planning",
                severity="Positive"
            )
        ]
        
    else:
        # Default to Trading & Distribution
        selected_sector = SelectedSector(
            id="trading-distribution",
            name="Trading & Distribution",
            code="HK-SME-TRD",
            geography=target_geo,
            description="Import/export and distribution SMEs with working-capital sensitivity."
        )
        
        sector_health = SectorHealth(
            score=62.0,
            label="Mixed but serviceable",
            severity="Neutral",
            components=SectorHealthComponents(
                pmi=SectorHealthComponent(
                    label="PMI",
                    value=51.2,
                    unit="index",
                    displayValue="51.2",
                    context="Mild expansion territory. Requires close buffer tracking."
                ),
                exportGrowth=SectorHealthComponent(
                    label="Export Growth",
                    value=1.8,
                    unit="percent",
                    displayValue="+1.8%",
                    context="Moderate export volume stabilization. Subject to local tariff trends."
                ),
                industrialProduction=SectorHealthComponent(
                    label="Industrial Production",
                    value=2.1,
                    unit="percent",
                    displayValue="+2.1%",
                    context="Moderate wholesale processing output expansion."
                ),
                marginContext=SectorHealthComponent(
                    label="Margin Context",
                    value=None,
                    unit="text",
                    displayValue="Margin pressure watch",
                    context="Volatility in freight rates and import costs creates mild margin compression risk."
                )
            )
        )
        
        benchmarks = [
            SectorBenchmark(
                id="dso",
                label="Days Sales Outstanding",
                value=45.0,
                unit="days",
                displayValue="45 days",
                comparison="Compared to industry standard (40 days)",
                context="Receivables cycle slightly elevated due to cross-border settlement latency. Receivables discipline remains important.",
                severity="Caution",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="dio",
                label="Inventory Days",
                value=60.0,
                unit="days",
                displayValue="60 days",
                comparison="Compared to industry standard (55 days)",
                context="Moderate inventory buildup in regional hubs. Buffer stock levels require review.",
                severity="Caution",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="dpo",
                label="Days Payable Outstanding",
                value=50.0,
                unit="days",
                displayValue="50 days",
                comparison="Compared to industry standard (45 days)",
                context="Payables matching receivables cycle extensions. Preserves working capital buffer.",
                severity="Neutral",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="gross-margin",
                label="Gross Margin Context",
                value=18.5,
                unit="percent",
                displayValue="18.5%",
                comparison="Compared to historical average (20.0%)",
                context="Input cost and freight rate volatility impact margins. Regional averages may vary.",
                severity="Caution",
                sourceTimestamp="2026-05"
            ),
            SectorBenchmark(
                id="documentation-readiness",
                label="Documentation Readiness",
                value=85.0,
                unit="percent",
                displayValue="85%",
                comparison="Compared to target (90%)",
                context="Standard invoice records complete; trade declarations pending review. Documentation consistency matters.",
                severity="Neutral",
                sourceTimestamp="2026-05"
            )
        ]
        
        watch_signals = [
            SectorWatchSignal(
                id="sig-1",
                title="Receivables Discipline Important",
                description="Receivables discipline remains important for lender review. Focus on outstanding collections.",
                affectedArea="Cashflow Planning",
                severity="Caution"
            ),
            SectorWatchSignal(
                id="sig-2",
                title="Inventory Pressure Watch",
                description="Inventory build-up can pressure working capital. Review stock rotation policies.",
                affectedArea="Warehouse Management",
                severity="Caution"
            ),
            SectorWatchSignal(
                id="sig-3",
                title="Documentation Quality Focus",
                description="Documentation consistency matters for trade finance conversations. Ensure invoice audit readiness.",
                affectedArea="Lender Readiness",
                severity="Neutral"
            )
        ]
        
    return SectorBenchmarksResponse(
        metadata=metadata,
        selectedSector=selected_sector,
        sectorHealth=sector_health,
        benchmarks=benchmarks,
        watchSignals=watch_signals,
        sourceStatus=source_status
    )


def get_commodities_fixture(sector: Optional[str] = None, geography: Optional[str] = None) -> CommoditiesResponse:
    now = datetime.utcnow().isoformat() + "Z"
    
    target_sector = (sector or "electronics-import").lower().strip()
    target_geo = geography or "HK"
    
    metadata = ResponseMetadata(
        asOf="2026-05", # fixture month
        fetchedAt=now,
        freshness="Workspace",
        isStale=False,
        source=SourceInfo(
            provider="Fixture",
            name="Workspace commodity exposure seed data"
        ),
        warnings=["Commodities endpoint is currently fixture-backed. Production commodity provider is not connected yet."]
    )
    
    if target_sector == "trading-distribution":
        selected_sector = SelectedSector(
            id="trading-distribution",
            name="Trading & Distribution",
            code="HK-SME-TRD",
            geography=target_geo,
            description="Import/export and distribution SMEs with working-capital sensitivity and commodity freight/energy exposure."
        )
    else:
        # Default to Electronics Import
        selected_sector = SelectedSector(
            id="electronics-import",
            name="Electronics Import",
            code="HK-SME-ELEC",
            geography=target_geo,
            description="Import-driven electronics SMEs with exposure to metals, freight, and FX-linked input costs."
        )
        
    commodity_exposures = [
        CommodityExposure(
            id="copper",
            commodity="Copper (LME)",
            category="Metals",
            value=14.0,
            unit="percent",
            displayValue="+14% YoY",
            trend="up",
            severity="Caution",
            exposedSectors=["Electronics Import", "Construction", "Manufacturing"],
            marginContext="Higher copper prices pressure printed circuit board and wiring raw material costs.",
            sourceTimestamp="2026-05"
        ),
        CommodityExposure(
            id="steel",
            commodity="Steel / Iron Ore",
            category="Metals",
            value=6.0,
            unit="percent",
            displayValue="+6% YoY",
            trend="up",
            severity="Neutral",
            exposedSectors=["Construction", "Heavy Industry", "Hardware Distribution"],
            marginContext="Moderate increase in structural metal components. Impact on electronic casings is limited.",
            sourceTimestamp="2026-05"
        ),
        CommodityExposure(
            id="cotton",
            commodity="Cotton",
            category="Soft Commodities",
            value=-3.0,
            unit="percent",
            displayValue="-3% YoY",
            trend="down",
            severity="Neutral",
            exposedSectors=["Apparel", "Textile Trading"],
            marginContext="Slight easing in textile input costs; minor positive pressure on apparel distribution margins.",
            sourceTimestamp="2026-05"
        ),
        CommodityExposure(
            id="energy",
            commodity="Energy / Oil (Brent)",
            category="Energy",
            value=9.0,
            unit="percent",
            displayValue="+9% YoY",
            trend="up",
            severity="Caution",
            exposedSectors=["Logistics", "Chemicals", "Manufacturing", "Electronics Import"],
            marginContext="Sustained oil price increases raise utility costs and regional transport surcharges.",
            sourceTimestamp="2026-05"
        ),
        CommodityExposure(
            id="freight",
            commodity="Freight / Logistics",
            category="Services",
            value=None,
            unit="text",
            displayValue="Index watch",
            trend="unknown",
            severity="Caution",
            exposedSectors=["Electronics Import", "Trading & Distribution", "Retail"],
            marginContext="Container index volatility watch; spot rate adjustments affect cross-border landed cost.",
            sourceTimestamp="2026-05"
        )
    ]
    
    margin_pressure_signal = [
        MarginPressureSignal(
            id="mod-input-cost-press",
            label="Moderate input-cost pressure",
            severity="Caution",
            description="Sector-level commodity exposure may pressure margins; company-specific impact requires financial records and supplier contracts.",
            affectedArea="Gross margin / working capital",
            requiresCompanyData=True
        )
    ]
    
    watch_signals = [
        CommodityWatchSignal(
            id="metals-exposure-watch",
            title="Metals exposure watch",
            description="Monitor copper and steel price trends if sourcing raw components or casings. Track whether supplier contracts include commodity-linked pricing terms.",
            affectedArea="Procurement / Casings",
            severity="Caution"
        ),
        CommodityWatchSignal(
            id="freight-energy-sensitivity",
            title="Freight and energy cost sensitivity",
            description="Utility rates and ocean/air freight spot rates remain volatile. Review how shipping terms may affect landed-cost exposure.",
            affectedArea="Landed Cost / Shipping",
            severity="Caution"
        ),
        CommodityWatchSignal(
            id="supplier-contract-context",
            title="Supplier contract review context",
            description="Review supplier contracts for price escalation clauses linked to commodity indexes.",
            affectedArea="Supplier Relations / Legal",
            severity="Neutral"
        )
    ]
    
    source_status = [
        SourceStatusItem(
            id="commodity-provider",
            label="Commodity Provider",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="sector-exposure-map",
            label="Sector Exposure Map",
            status="seed_data",
            provider="Fixture"
        ),
        SourceStatusItem(
            id="company-margin-data",
            label="Company Margin Data",
            status="requires_company_data",
            provider="Pending"
        )
    ]
    
    return CommoditiesResponse(
        metadata=metadata,
        selectedSector=selected_sector,
        commodityExposures=commodity_exposures,
        marginPressureSignal=margin_pressure_signal,
        watchSignals=watch_signals,
        sourceStatus=source_status
    )


