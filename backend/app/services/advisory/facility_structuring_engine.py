from typing import List, Optional
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    StressTestingResponse,
    FacilityStructuringResponse,
    FacilityCandidate,
    FacilityFitAssessment,
    FacilityType
)

def build_facility_structuring(
    analysis: FinancialAnalysisResponse,
    precheck: HardGatePrecheckResult,
    risk_score: UnifiedRiskScoreResult,
    stress_tests: StressTestingResponse
) -> FacilityStructuringResponse:
    """
    Generates candidate financing packages and performs fit assessments for the company.
    
    This is an assumptions-based advisory tool only. It does not perform bank underwriting
    or determine credit outcomes. Limit and pricing estimations are candidates only,
    subject to lender review.
    """
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    summary = analysis.summary
    
    disclaimer = (
        "All candidates, estimated limits, and pricing structures are assumptions-based "
        "and provided for advisory context only. They do not constitute a credit decision "
        "or loan commitment. Limit and pricing metrics are subject to lender review. "
        "Company records are required for production."
    )
    
    if not snapshot or not ratios or not summary:
        return FacilityStructuringResponse(
            company_id=snapshot.company_id if snapshot else "demo_company",
            company_name=snapshot.company_name if snapshot else "Demo Company",
            base_risk_score=risk_score.score if risk_score else 0,
            base_risk_band=risk_score.band if risk_score else "unavailable",
            hard_gate_status=precheck.overall_status if precheck else "unavailable",
            candidates=[],
            preferred_candidate_keys=[],
            disclaimer=disclaimer,
            warnings=["Insufficient financial analysis outputs to build facility candidates."]
        )

    candidates: List[FacilityCandidate] = []
    preferred_candidate_keys: List[str] = []
    
    # Base rate proxy (HIBOR reference proxy at 4.5% / 450 bps)
    base_rate_bps = 450
    
    # Pricing spread based on risk band
    risk_spread_map = {
        "low": 250,
        "moderate": 350,
        "elevated": 500,
        "high": 700,
        "unavailable": 500
    }
    risk_spread = risk_spread_map.get(risk_score.band, 500)
    pricing_bps = base_rate_bps + risk_spread

    # 1. Revolving Working Capital Line
    rev_limit = 0.0
    revenue = snapshot.income_statement.revenue
    wc_gap = ratios.working_capital_gap.value or 0.0
    
    if wc_gap > 0 and revenue > 0:
        rev_limit = min(wc_gap * 1.25, revenue * 0.20)
        
    # Cap limit if precheck fails or risk score is high/elevated
    has_cap_trigger = (precheck.overall_status == "fail") or (risk_score.band in ("high", "elevated"))
    if has_cap_trigger:
        rev_limit = min(rev_limit, 1500000.0)  # Capped at HKD 1.5M
        
    rev_limit = max(0.0, rev_limit)
    rev_annual_cost = (rev_limit * pricing_bps) / 10000.0
    
    # Fit assessment revolving working capital
    is_dscr_constrained = (summary.debt_service_band in ("watch", "constrained")) or (ratios.dscr.value is not None and ratios.dscr.value < 1.1)
    
    rev_fit_band = "adequate"
    rev_rationales = []
    rev_constraints = []
    rev_watch_items = []
    
    if is_dscr_constrained:
        rev_fit_band = "watch" if summary.debt_service_band == "watch" else "constrained"
        rev_rationales.append("Debt service coverage capacity is constrained or narrow.")
        rev_constraints.append("Baseline DSCR indicates limited space for additional debt service.")
    else:
        if risk_score.band == "low":
            rev_fit_band = "strong"
            rev_rationales.append("Strong balance sheet metrics support solid facility fit.")
        elif risk_score.band == "moderate":
            rev_fit_band = "adequate"
            rev_rationales.append("Adequate credit profile supports working capital facility.")
        else:
            rev_fit_band = "watch"
            rev_rationales.append("Elevated risk profile suggests a structured watch approach.")
            
    rev_rationales.append("Revolving credit provides flexible liquidity to bridge working capital gap.")
    
    candidates.append(FacilityCandidate(
        facility_key="revolving_working_capital",
        facility_type=FacilityType.revolving_working_capital,
        label="Revolving Working Capital Line",
        estimated_limit=rev_limit,
        currency="HKD",
        estimated_pricing_bps=pricing_bps,
        estimated_annual_cost=rev_annual_cost,
        tenor_months=12,
        repayment_profile="Interest-only monthly, principal bullet at maturity",
        purpose="Bridge short-term cash flow gaps and manage working capital cycles.",
        fit_assessment=FacilityFitAssessment(
            fit_band=rev_fit_band,
            rationale=" ".join(rev_rationales),
            constraints=rev_constraints,
            watch_items=rev_watch_items,
            required_data=["Receivables aging ledger", "Bank statement summaries"]
        ),
        supporting_signals=[
            f"Working capital gap: HKD {wc_gap:,.0f}",
            f"Base risk score: {risk_score.score}"
        ],
        sensitivity_notes="Subject to interest rate shifts (HIBOR link). Limit is capped to manage cash flow headroom.",
        disclaimer=disclaimer
    ))

    # 2. Receivables Finance
    total_ar = snapshot.balance_sheet.accounts_receivable
    eligible_ar = total_ar
    if snapshot.receivables_aging:
        # Exclude 90+ days aging bucket
        eligible_ar = total_ar - snapshot.receivables_aging.days_90_plus
        
    eligible_ar = max(0.0, eligible_ar)
    
    # Advance rate mapping
    advance_rate_map = {
        "low": 0.75,
        "moderate": 0.75,
        "elevated": 0.65,
        "high": 0.50,
        "unavailable": 0.60
    }
    advance_rate = advance_rate_map.get(risk_score.band, 0.60)
    ar_limit = eligible_ar * advance_rate
    ar_annual_cost = (ar_limit * pricing_bps) / 10000.0
    
    # Fit assessment receivables finance
    is_ar_constrained = summary.receivables_band == "constrained"
    ar_90_concentration = 0.0
    if snapshot.receivables_aging and total_ar > 0:
        ar_90_concentration = snapshot.receivables_aging.days_90_plus / total_ar
        
    ar_fit_band = "adequate"
    ar_rationales = []
    ar_constraints = []
    ar_watch_items = []
    
    if is_ar_constrained or ar_90_concentration > 0.20:
        ar_fit_band = "constrained"
        ar_rationales.append("Receivables quality is weak with significant concentration of late invoices.")
        ar_constraints.append("High 90+ day receivables concentration narrows advance eligibility.")
    elif summary.receivables_band in ("watch", "elevated"):
        ar_fit_band = "watch"
        ar_rationales.append("Receivables lag is present, but collection cycle remains functional.")
        ar_watch_items.append("Monitor collection lag and average invoice aging.")
    else:
        if risk_score.band in ("low", "moderate"):
            ar_fit_band = "strong"
            ar_rationales.append("Clean receivables aging allows maximum advance rate.")
        else:
            ar_fit_band = "adequate"
            ar_rationales.append("Baseline receivables profile supports invoicing-based financing.")
            
    ar_rationales.append("Accelerates collection cycles and converts outstanding invoicing to cash.")
    
    candidates.append(FacilityCandidate(
        facility_key="receivables_finance",
        facility_type=FacilityType.receivables_finance,
        label="Receivables Financing Facility",
        estimated_limit=ar_limit,
        currency="HKD",
        estimated_pricing_bps=pricing_bps,
        estimated_annual_cost=ar_annual_cost,
        tenor_months=12,
        repayment_profile="Repaid directly from invoice collections",
        purpose="Convert customer accounts receivable to immediate liquidity.",
        fit_assessment=FacilityFitAssessment(
            fit_band=ar_fit_band,
            rationale=" ".join(ar_rationales),
            constraints=ar_constraints,
            watch_items=ar_watch_items,
            required_data=["Detailed invoice registry", "Customer credit histories"]
        ),
        supporting_signals=[
            f"Accounts receivable: HKD {total_ar:,.0f}",
            f"Eligible AR: HKD {eligible_ar:,.0f}"
        ],
        sensitivity_notes="Limits are sensitive to invoice quality and customer credit risk profiles.",
        disclaimer=disclaimer
    ))

    # 3. Trade Finance / Import Facility
    cogs_base = snapshot.income_statement.cogs
    trade_limit = 0.0
    if cogs_base > 0:
        trade_limit = (cogs_base / 12.0) * 2.0  # 2 months proxy
        
    trade_annual_cost = (trade_limit * pricing_bps) / 10000.0
    
    # Fit assessment trade finance
    input_cost_scenario = next((s for s in stress_tests.scenarios if s.scenario_key == "input_cost_squeeze"), None)
    input_cost_severity = input_cost_scenario.severity if input_cost_scenario else "low"
    fx_scenario = next((s for s in stress_tests.scenarios if s.scenario_key == "fx_stress"), None)
    fx_severity = fx_scenario.severity if fx_scenario else "low"
    
    trade_fit_band = "adequate"
    trade_rationales = []
    trade_constraints = []
    trade_watch_items = []
    
    if input_cost_severity == "high" or fx_severity == "high":
        trade_fit_band = "watch"
        trade_rationales.append("High commodity cost or FX import sensitivity increases pricing risk on procurement.")
        trade_watch_items.append("Monitor FX volatility and procurement cost trends.")
    elif input_cost_severity == "elevated" or fx_severity == "elevated":
        trade_fit_band = "watch"
        trade_rationales.append("Elevated input-cost squeeze or FX stress calls for close procurement review.")
    else:
        if risk_score.band in ("low", "moderate"):
            trade_fit_band = "strong"
            trade_rationales.append("Stable import margin sensitivities support trade finance facility.")
        else:
            trade_fit_band = "adequate"
            trade_rationales.append("Standard trade financing fit matching current supplier terms.")
            
    trade_rationales.append("Provides funding for imports and inventory raw materials.")
    
    candidates.append(FacilityCandidate(
        facility_key="trade_finance",
        facility_type=FacilityType.trade_finance,
        label="Trade Finance & LC Facility",
        estimated_limit=trade_limit,
        currency="HKD",
        estimated_pricing_bps=pricing_bps,
        estimated_annual_cost=trade_annual_cost,
        tenor_months=6,
        repayment_profile="L/C drawings or import loans repaid post-sale",
        purpose="Support procurement, trade payments, and inventory imports.",
        fit_assessment=FacilityFitAssessment(
            fit_band=trade_fit_band,
            rationale=" ".join(trade_rationales),
            constraints=trade_constraints,
            watch_items=trade_watch_items,
            required_data=["Supplier contracts", "Import bills / bills of lading"]
        ),
        supporting_signals=[
            f"Annual COGS: HKD {cogs_base:,.0f}",
            f"Import cost sensitivity: {fx_severity}"
        ],
        sensitivity_notes="Limits depend on supplier terms and shipping timelines.",
        disclaimer=disclaimer
    ))

    # 4. Term Loan Refinance Context
    ebitda_base = snapshot.income_statement.ebitda
    term_limit = max(0.0, ebitda_base * 1.0)
    term_annual_cost = (term_limit * pricing_bps) / 10000.0
    
    # Fit assessment term loan
    is_dscr_under_1 = ratios.dscr.value is not None and ratios.dscr.value < 1.0
    term_fit_band = "adequate"
    term_rationales = []
    term_constraints = []
    term_watch_items = []
    
    if is_dscr_under_1:
        term_fit_band = "constrained"
        term_rationales.append("DSCR is below 1.0x, indicating current operating cash flow cannot comfortably service term obligations.")
        term_constraints.append("Baseline debt service coverage fails to meet safe credit criteria.")
    elif is_dscr_constrained:
        term_fit_band = "watch"
        term_rationales.append("Narrow debt service coverage margins require structured monitoring.")
        term_watch_items.append("Track monthly debt service constraints closely.")
    else:
        term_rationales.append("Term refinancing can extend maturities and improve cash flow structure.")
        
    candidates.append(FacilityCandidate(
        facility_key="term_loan",
        facility_type=FacilityType.term_loan,
        label="Term Loan Facility",
        estimated_limit=term_limit,
        currency="HKD",
        estimated_pricing_bps=pricing_bps,
        estimated_annual_cost=term_annual_cost,
        tenor_months=36,
        repayment_profile="Monthly principal and interest amortization",
        purpose="Refinance existing short-term debt to smooth maturity profile.",
        fit_assessment=FacilityFitAssessment(
            fit_band=term_fit_band,
            rationale=" ".join(term_rationales),
            constraints=term_constraints,
            watch_items=term_watch_items,
            required_data=["Existing credit agreements", "Three-year business plan"]
        ),
        supporting_signals=[
            f"EBITDA: HKD {ebitda_base:,.0f}",
            f"Debt service coverage: {ratios.dscr.value or 0.0:.2f}x"
        ],
        sensitivity_notes="Highly sensitive to baseline cash flow stability. Subject to strict debt service check covenants.",
        disclaimer=disclaimer
    ))

    # 5. FX Hedging Context
    fx_fit_band = "watch"
    fx_rationales = []
    
    if fx_severity == "high":
        fx_fit_band = "adequate"
        fx_rationales.append("High FX import-cost sensitivity detected. Advise review of FX forward contracts.")
    elif fx_severity == "elevated":
        fx_fit_band = "adequate"
        fx_rationales.append("Elevated USD import cost exposure indicates value in checking FX hedging tools.")
    elif fx_severity == "unavailable":
        fx_fit_band = "unavailable"
        fx_rationales.append("FX exposure parameters not available for this company.")
    else:
        fx_fit_band = "watch"
        fx_rationales.append("Low FX import-cost stress indicates hedging is not an immediate priority.")
        
    fx_rationales.append("Advisory context only; review FX hedging policies with an FX specialist.")
    
    candidates.append(FacilityCandidate(
        facility_key="fx_hedging",
        facility_type=FacilityType.fx_hedging_context,
        label="FX Hedging Advisory Context",
        estimated_limit=None,
        currency="HKD",
        estimated_pricing_bps=None,
        estimated_annual_cost=None,
        tenor_months=None,
        repayment_profile="N/A - Non-credit advisory context",
        purpose="Manage currency risk exposure on imports and supplier payments.",
        fit_assessment=FacilityFitAssessment(
            fit_band=fx_fit_band,
            rationale=" ".join(fx_rationales),
            constraints=[],
            watch_items=[],
            required_data=["Procurement invoices denominated in foreign currencies"]
        ),
        supporting_signals=[
            f"USD import cost sensitivity: {fx_severity}"
        ],
        sensitivity_notes="This is an advisory review context only, not a credit facility.",
        disclaimer=disclaimer
    ))

    # Choose preferred credit candidates
    if rev_fit_band in ("strong", "adequate", "watch"):
        preferred_candidate_keys.append("revolving_working_capital")
    if ar_fit_band in ("strong", "adequate", "watch"):
        preferred_candidate_keys.append("receivables_finance")
    if trade_fit_band in ("strong", "adequate", "watch"):
        preferred_candidate_keys.append("trade_finance")

    # Global response constraints
    global_constraints = []
    if precheck.overall_status == "fail":
        global_constraints.append("Company fails to meet basic hard-gate workflow criteria.")
    if is_dscr_constrained:
        global_constraints.append("Baseline debt service coverage capacity is constrained.")
    if risk_score.band in ("elevated", "high"):
        global_constraints.append("Credit score risk band requires conservative sizing limits.")

    # Warnings consolidation
    global_warnings = []
    if summary.warnings:
        global_warnings.extend(summary.warnings)
    if risk_score.warnings:
        global_warnings.extend(risk_score.warnings)
        
    def _dedup(l: List[str]) -> List[str]:
        seen = set()
        return [x for x in l if not (x in seen or seen.add(x))]
    global_warnings = _dedup(global_warnings)

    limitations = [
        "Lender review required.",
        "Terms are indicative and depend on bank policy, documentation, collateral, and borrower profile.",
        "Estimated limits and rates are not a formal credit offer or loan commitment."
    ]
    
    assumptions = [
        "Working capital lines assume typical HKD operating cash cycle patterns.",
        "Receivables financing assumes receivables ledger dilution and collection lag stay within acceptable bounds.",
        "Trade finance assumes direct linkage to cost of goods sold (COGS).",
        "Pricing uses a baseline HIBOR rate of 4.5% (450 bps) plus a risk spread based on the workspace-derived planning tier."
    ]

    data_quality = {
        "financial_analysis_available": snapshot is not None and ratios is not None,
        "precheck_status": precheck.overall_status if precheck else "unavailable",
        "risk_score_available": risk_score is not None
    }

    # Sum of non-advisory limits
    total_max_size = sum(c.estimated_limit for c in candidates if c.estimated_limit is not None)

    return FacilityStructuringResponse(
        company_id=snapshot.company_id,
        company_name=snapshot.company_name,
        base_risk_score=risk_score.score,
        base_risk_band=risk_score.band,
        hard_gate_status=precheck.overall_status,
        candidates=candidates,
        preferred_candidate_keys=preferred_candidate_keys,
        constraints=global_constraints,
        next_data_needed=precheck.next_data_needed,
        disclaimer=disclaimer,
        warnings=global_warnings,
        dscr_floor=1.10,
        ltv_cap=0.70,
        max_facility_size=total_max_size,
        indicative_pricing_assumption=f"HIBOR (4.5%) + spread of {risk_spread} bps based on planning tier",
        provenance="Deterministic workspace rules engine",
        model_version="1.0.0",
        model_type="candidate_facility_structuring",
        calibration_status="rules_based",
        assumptions=assumptions,
        limitations=limitations,
        data_quality=data_quality,
        confidence_band="medium"
    )
