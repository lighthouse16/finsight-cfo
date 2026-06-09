from typing import Optional

from app.models.market_watch import (
    BenchmarkSignal,
    DemandSignal,
    IndustryHealthBand,
    IndustryHealthComponent,
    IndustryHealthProvenance,
    IndustryHealthResponse,
    MarginSignal,
    SectorBenchmark,
    SectorBenchmarksResponse,
    SignalSeverity,
    WorkingCapitalSignal,
)
from app.services.market_watch.sector_benchmarks_service import get_sector_benchmarks
from app.services.market_watch.source_registry import build_provenance

DISCLAIMER = (
    "Industry health context is for planning support only. It uses fixture/workspace-derived "
    "sector benchmarks and is not a financing instruction."
)


def _severity_score(severity: SignalSeverity) -> int:
    return {"Positive": 1, "Neutral": 0, "Caution": -1, "High": -2}.get(severity, 0)


def _format_value(value: Optional[float], display_value: str) -> str:
    return display_value if display_value else ("N/A" if value is None else str(value))


def _demand_signal(data: SectorBenchmarksResponse) -> tuple[DemandSignal, IndustryHealthComponent]:
    components = data.sectorHealth.components
    pmi = components.pmi.value if components.pmi else None
    export_growth = components.exportGrowth.value if components.exportGrowth else None
    industrial_production = components.industrialProduction.value if components.industrialProduction else None

    values = [v for v in (pmi, export_growth, industrial_production) if v is not None]
    if not values:
        signal: DemandSignal = "unavailable"
        explanation = "Demand proxy is unavailable because sector PMI/export/production fixture inputs are missing."
        value = None
    else:
        expansion_points = 0
        if pmi is not None and pmi >= 52:
            expansion_points += 1
        if export_growth is not None and export_growth >= 3:
            expansion_points += 1
        if industrial_production is not None and industrial_production >= 3:
            expansion_points += 1

        softening_points = 0
        if pmi is not None and pmi < 50:
            softening_points += 1
        if export_growth is not None and export_growth < 0:
            softening_points += 1
        if industrial_production is not None and industrial_production < 0:
            softening_points += 1

        if expansion_points >= 2:
            signal = "expanding"
        elif softening_points >= 1:
            signal = "softening"
        else:
            signal = "stable"
        value = ", ".join(
            part for part in (
                f"PMI {pmi:.1f}" if pmi is not None else "",
                f"exports {export_growth:+.1f}%" if export_growth is not None else "",
                f"production {industrial_production:+.1f}%" if industrial_production is not None else "",
            ) if part
        )
        explanation = "Demand proxy blends fixture PMI, export growth, and production context."

    return signal, IndustryHealthComponent(
        signal="demandSignal",
        label="Demand proxy",
        band=signal,
        value=value,
        explanation=explanation,
    )


def _margin_signal(data: SectorBenchmarksResponse) -> tuple[MarginSignal, IndustryHealthComponent]:
    gross_margin = next((item for item in data.benchmarks if item.id == "gross-margin"), None)
    margin_context = data.sectorHealth.components.marginContext
    if gross_margin is None and margin_context is None:
        signal: MarginSignal = "unavailable"
        return signal, IndustryHealthComponent(
            signal="marginSignal",
            label="Margin proxy",
            band=signal,
            value=None,
            explanation="Margin proxy is unavailable because margin benchmark inputs are missing.",
        )

    severity = gross_margin.severity if gross_margin else data.sectorHealth.severity
    if severity == "Positive":
        signal = "expanding"
    elif severity in ("Caution", "High"):
        signal = "compressing"
    else:
        signal = "stable"

    value = _format_value(gross_margin.value, gross_margin.displayValue) if gross_margin else margin_context.displayValue
    explanation = (gross_margin.context if gross_margin else margin_context.context)
    return signal, IndustryHealthComponent(
        signal="marginSignal",
        label="Margin proxy",
        band=signal,
        value=value,
        explanation=explanation,
    )


def _working_capital_signal(benchmarks: list[SectorBenchmark]) -> tuple[WorkingCapitalSignal, IndustryHealthComponent]:
    wc_items = [item for item in benchmarks if item.id in {"dso", "dio", "dpo"}]
    if not wc_items:
        signal: WorkingCapitalSignal = "unavailable"
        return signal, IndustryHealthComponent(
            signal="workingCapitalSignal",
            label="Working capital proxy",
            band=signal,
            value=None,
            explanation="Working capital proxy is unavailable because DSO/DIO/DPO inputs are missing.",
        )

    high_count = sum(1 for item in wc_items if item.severity == "High")
    caution_count = sum(1 for item in wc_items if item.severity == "Caution")
    positive_count = sum(1 for item in wc_items if item.severity == "Positive")

    if high_count or caution_count >= 2:
        signal = "stressed"
    elif caution_count == 1:
        signal = "watch"
    elif positive_count >= 1 and caution_count == 0:
        signal = "healthy"
    else:
        signal = "watch"

    value = " / ".join(f"{item.label}: {item.displayValue}" for item in wc_items)
    explanation = "Working capital proxy reviews DSO, inventory days, and payable days fixture benchmarks."
    return signal, IndustryHealthComponent(
        signal="workingCapitalSignal",
        label="Working capital proxy",
        band=signal,
        value=value,
        explanation=explanation,
    )


def _benchmark_signal(data: SectorBenchmarksResponse) -> tuple[BenchmarkSignal, IndustryHealthComponent]:
    items = data.benchmarks
    if data.sectorHealth.score is None or not items:
        signal: BenchmarkSignal = "unavailable"
    else:
        score = data.sectorHealth.score
        caution_count = sum(1 for item in items if item.severity == "Caution")
        high_count = sum(1 for item in items if item.severity == "High")
        positive_count = sum(1 for item in items if item.severity == "Positive")
        if score >= 70 and positive_count >= 2 and high_count == 0:
            signal = "favorable"
        elif score < 55 or high_count > 0 or caution_count >= 3:
            signal = "cautious"
        else:
            signal = "neutral"

    return signal, IndustryHealthComponent(
        signal="benchmarkSignal",
        label="Benchmark proxy",
        band=signal,
        value=f"{data.sectorHealth.score:.0f}/100" if data.sectorHealth.score is not None else None,
        explanation=f"Overall fixture benchmark context: {data.sectorHealth.label}.",
    )


def _overall_band(
    demand: DemandSignal,
    margin: MarginSignal,
    working_capital: WorkingCapitalSignal,
    benchmark: BenchmarkSignal,
) -> IndustryHealthBand:
    if "unavailable" in {demand, margin, working_capital, benchmark}:
        return "unavailable"

    stress_points = 0
    stress_points += 1 if demand == "softening" else 0
    stress_points += 1 if margin == "compressing" else 0
    stress_points += 2 if working_capital == "stressed" else 1 if working_capital == "watch" else 0
    stress_points += 1 if benchmark == "cautious" else 0

    positive_points = 0
    positive_points += 1 if demand == "expanding" else 0
    positive_points += 1 if margin == "expanding" else 0
    positive_points += 1 if working_capital == "healthy" else 0
    positive_points += 1 if benchmark == "favorable" else 0

    if stress_points >= 3:
        return "stressed"
    if stress_points >= 1:
        return "watch"
    if positive_points >= 3:
        return "resilient"
    return "stable"


async def get_industry_health(
    sector: Optional[str] = None,
    geography: Optional[str] = None,
) -> IndustryHealthResponse:
    data = await get_sector_benchmarks(sector=sector, geography=geography)

    demand, demand_component = _demand_signal(data)
    margin, margin_component = _margin_signal(data)
    working_capital, wc_component = _working_capital_signal(data.benchmarks)
    benchmark, benchmark_component = _benchmark_signal(data)
    band = _overall_band(demand, margin, working_capital, benchmark)

    provenance = IndustryHealthProvenance(
        **build_provenance(
            "industry_health_v1",
            as_of=data.metadata.asOf,
            provider_override=data.metadata.source.name,
            freshness_override=data.metadata.freshness,
        ),
    )
    warnings = [
        "Industry Health Context v1 is fixture/workspace-derived. Production sector provider integration is pending.",
        *data.metadata.warnings,
    ]
    if band == "unavailable":
        warnings.append("One or more sector proxy inputs are unavailable; overall band is unavailable.")

    explanation = (
        f"{data.selectedSector.name} is {band} based on demand, margin, "
        "working-capital, and benchmark proxy signals from sector benchmark seed data."
    )

    return IndustryHealthResponse(
        sectorName=data.selectedSector.name,
        industryHealthBand=band,
        demandSignal=demand,
        marginSignal=margin,
        workingCapitalSignal=working_capital,
        benchmarkSignal=benchmark,
        explanation=explanation,
        components=[demand_component, margin_component, wc_component, benchmark_component],
        provenance=provenance,
        source=provenance,
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )
