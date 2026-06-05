import math
from typing import List, Optional
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    RiskScoreFactor,
    RiskScoreBand
)

def build_unified_risk_score(
    analysis: FinancialAnalysisResponse,
    precheck: HardGatePrecheckResult
) -> UnifiedRiskScoreResult:
    """
    Builds a unified, context-only risk scoring foundation that consumes the
    financial analysis summary and advisory precheck.
    
    This is not a calibrated default model or formal credit decision. Higher score
    indicates stronger advisory readiness context; lower score indicates more constrained context.
    """
    factors: List[RiskScoreFactor] = []
    strengths: List[str] = []
    constraints: List[str] = []
    watch_items: List[str] = []
    
    summary = analysis.summary
    ratios = analysis.ratios
    
    # Base score
    score = 100
    
    # --- 1. Debt Service Coverage Factor ---
    ds_band = summary.debt_service_band.lower() if (summary and summary.debt_service_band) else "unavailable"
    ds_penalty = -10
    ds_msg = "Debt-service coverage assessment is unavailable."
    
    # Evidence helper
    dscr_val = ratios.dscr.value if (ratios and ratios.dscr) else None
    dscr_evidence = f"DSCR: {dscr_val:.2f}x" if dscr_val is not None else "DSCR: N/A"
    
    if ds_band == "strong":
        ds_penalty = 0
        ds_msg = "Debt-service coverage is strong, meeting top-tier safety margins."
        strengths.append("Strong debt-service coverage capacity.")
    elif ds_band == "adequate":
        ds_penalty = -8
        ds_msg = "Debt-service coverage is adequate, meeting standard advisory parameters."
        strengths.append("Adequate debt-service coverage capacity.")
    elif ds_band == "watch":
        ds_penalty = -15
        ds_msg = "Debt-service coverage is below standard thresholds, indicating narrow margins."
        watch_items.append("Debt-service coverage is in the watch range.")
    elif ds_band == "constrained":
        ds_penalty = -30
        ds_msg = "Debt-service coverage is the main constraint under current cash flow metrics."
        constraints.append("Constrained debt-service coverage under demo cash flow parameters.")
        
    score += ds_penalty
    factors.append(RiskScoreFactor(
        key="debt_service",
        label="Debt-service coverage",
        score_impact=ds_penalty,
        band=ds_band,
        message=ds_msg,
        evidence=dscr_evidence,
        source="financial_analysis_summary.debtServiceBand",
        weight=0.25
    ))

    # --- 2. Liquidity Factor ---
    liq_band = summary.liquidity_band.lower() if (summary and summary.liquidity_band) else "unavailable"
    liq_penalty = -8
    liq_msg = "Liquidity precheck is unavailable."
    
    curr_val = ratios.current_ratio.value if (ratios and ratios.current_ratio) else None
    quick_val = ratios.quick_ratio.value if (ratios and ratios.quick_ratio) else None
    liq_evidence = f"Current Ratio: {curr_val:.2f}x, Quick Ratio: {quick_val:.2f}x" if (curr_val is not None and quick_val is not None) else "Liquidity: N/A"
    
    if liq_band == "strong":
        liq_penalty = 0
        liq_msg = "Liquidity buffers are comfortable and provide stable near-term runway."
        strengths.append("Comfortable near-term liquidity runway.")
    elif liq_band == "adequate":
        liq_penalty = -5
        liq_msg = "Liquidity metrics indicate sufficient near-term buffer."
        strengths.append("Adequate liquidity buffer.")
    elif liq_band == "watch":
        liq_penalty = -12
        liq_msg = "Liquidity buffers are thin, warranting short-term monitoring."
        watch_items.append("Liquidity indicators warrant close monitoring.")
    elif liq_band == "constrained":
        liq_penalty = -22
        liq_msg = "Liquidity buffers are severely constrained under this demo analysis."
        constraints.append("Constrained short-term liquidity buffers.")
        
    score += liq_penalty
    factors.append(RiskScoreFactor(
        key="liquidity",
        label="Liquidity buffer",
        score_impact=liq_penalty,
        band=liq_band,
        message=liq_msg,
        evidence=liq_evidence,
        source="financial_analysis_summary.liquidityBand",
        weight=0.15
    ))

    # --- 3. Leverage Factor ---
    lev_band = summary.leverage_band.lower() if (summary and summary.leverage_band) else "unavailable"
    lev_penalty = -8
    lev_msg = "Leverage precheck is unavailable."
    
    lev_val = ratios.net_debt_to_ebitda.value if (ratios and ratios.net_debt_to_ebitda) else None
    lev_evidence = f"Net Debt / EBITDA: {lev_val:.2f}x" if lev_val is not None else "Leverage: N/A"
    
    if lev_band == "strong":
        lev_penalty = 0
        lev_msg = "Leverage is low relative to earnings, providing strong balance sheet headroom."
        strengths.append("Low leverage relative to operating earnings.")
    elif lev_band == "adequate":
        lev_penalty = -5
        lev_msg = "Leverage profile is moderate and within typical parameters."
        strengths.append("Moderate balance sheet leverage.")
    elif lev_band == "watch":
        lev_penalty = -12
        lev_msg = "Leverage is in the transitional watch range."
        watch_items.append("Leverage ratios are in the watch range.")
    elif lev_band == "constrained":
        lev_penalty = -20
        lev_msg = "Leverage is elevated relative to EBITDA, constraining borrowing headroom."
        constraints.append("Constrained leverage profile under current debt loads.")
        
    score += lev_penalty
    factors.append(RiskScoreFactor(
        key="leverage",
        label="Leverage profile",
        score_impact=lev_penalty,
        band=lev_band,
        message=lev_msg,
        evidence=lev_evidence,
        source="financial_analysis_summary.leverageBand",
        weight=0.15
    ))

    # --- 4. Receivables Quality Factor ---
    ar_band = summary.receivables_band.lower() if (summary and summary.receivables_band) else "unavailable"
    ar_penalty = -8
    ar_msg = "Receivables credit risk analysis is unavailable."
    
    ar_val = ratios.expected_credit_loss_ar.value if (ratios and ratios.expected_credit_loss_ar) else None
    ar_evidence = f"ECL AR: {ar_val/1000:.1f}k" if ar_val is not None else "AR Risk: N/A"
    
    if ar_band == "strong":
        ar_penalty = 0
        ar_msg = "Receivables credit risk is minimal, collection cycles are highly efficient."
        strengths.append("Highly efficient receivables collection cycles.")
    elif ar_band == "adequate":
        ar_penalty = -3
        ar_msg = "Receivables profile is within normal range."
        strengths.append("Stable receivables collection parameters.")
    elif ar_band == "watch":
        ar_penalty = -10
        ar_msg = "Receivables profile shows moderate aging or collection cycle lag."
        watch_items.append("Receivables collection lag requires monitoring.")
    elif ar_band == "constrained":
        ar_penalty = -18
        ar_msg = "Receivables risk is elevated, indicating significant collection delays."
        constraints.append("Receivables aging and concentration pose collection challenges.")
        
    score += ar_penalty
    factors.append(RiskScoreFactor(
        key="receivables",
        label="Receivables credit risk",
        score_impact=ar_penalty,
        band=ar_band,
        message=ar_msg,
        evidence=ar_evidence,
        source="financial_analysis_summary.receivablesBand",
        weight=0.10
    ))

    # --- 5. Valuation Factor ---
    val_band = summary.valuation_band.lower() if (summary and summary.valuation_band) else "unavailable"
    val_penalty = -5
    val_msg = "Valuation analysis is unavailable."
    val_evidence = "Valuation completed" if (analysis.valuation) else "Valuation: N/A"
    
    if val_band == "strong":
        val_penalty = 0
        val_msg = "Valuation assumptions and multiples are highly consistent and pass all sanity checks."
        strengths.append("Consistent valuation model parameters.")
    elif val_band == "adequate":
        val_penalty = 0  # adequate/strong: 0 penalty
        val_msg = "Valuation assumptions meet standard parameters and pass baseline checks."
        strengths.append("Valuation parameters pass sanity checks.")
    elif val_band == "watch":
        val_penalty = -8
        val_msg = "Valuation parameters show high terminal value concentration or variations."
        watch_items.append("Valuation terminal value dependency warrants monitoring.")
    elif val_band == "constrained":
        val_penalty = -15
        val_msg = "Valuation parameters show inconsistencies or implied equity value is negative."
        constraints.append("Valuation model parameters show inconsistencies.")
        
    score += val_penalty
    factors.append(RiskScoreFactor(
        key="valuation",
        label="Valuation sanity",
        score_impact=val_penalty,
        band=val_band,
        message=val_msg,
        evidence=val_evidence,
        source="financial_analysis_summary.valuationBand",
        weight=0.10
    ))

    # --- 6. Hard-Gate Precheck Factor ---
    hg_status = precheck.overall_status.lower() if precheck else "unavailable"
    hg_penalty = -8
    hg_msg = "Hard-gate precheck status is unavailable."
    hg_evidence = f"Precheck: {hg_status}"
    
    if hg_status == "pass":
        hg_penalty = 0
        hg_msg = "All hard-gate precheck parameters were passed successfully."
        strengths.append("All advisory hard-gate prechecks passed.")
    elif hg_status == "watch":
        hg_penalty = -10
        hg_msg = "Hard-gate precheck indicates items warranting advisory watch."
        watch_items.append("Hard-gate precheck flagged watch items.")
    elif hg_status == "fail":
        hg_penalty = -20
        hg_msg = "Hard-gate precheck failed due to debt service or liquidity constraints."
        constraints.append("Precheck fails to meet basic workflow criteria.")
        
    score += hg_penalty
    factors.append(RiskScoreFactor(
        key="hard_gate",
        label="Hard-gate precheck status",
        score_impact=hg_penalty,
        band=hg_status,
        message=hg_msg,
        evidence=hg_evidence,
        source="hard_gate_precheck.overall_status",
        weight=0.15
    ))

    # --- 7. Data Integrity Factor ---
    integrity_status = "unavailable"
    integrity_penalty = -10
    integrity_msg = "No data integrity checks were performed."
    integrity_evidence = "Checks missing"
    
    if analysis.integrity_checks:
        all_passed = all(c.passed for c in analysis.integrity_checks)
        integrity_evidence = f"{len(analysis.integrity_checks)} checks completed"
        if all_passed:
            integrity_status = "pass"
            integrity_penalty = 0
            integrity_msg = "All financial data integrity checks passed successfully."
            strengths.append("All accounting reconciliation checks passed.")
        else:
            integrity_status = "fail"
            integrity_penalty = -25
            integrity_msg = "Data integrity checks failed accounting balance sheet identity."
            constraints.append("Accounting balance sheet reconciliation failure.")
            
    score += integrity_penalty
    factors.append(RiskScoreFactor(
        key="data_integrity",
        label="Data integrity and reconciliation",
        score_impact=integrity_penalty,
        band=integrity_status,
        message=integrity_msg,
        evidence=integrity_evidence,
        source="financial_analysis_response.integrityChecks",
        weight=0.10
    ))

    # Clamp score
    final_score = max(0, min(100, score))
    
    # Band mapping
    # 80-100: low
    # 60-79: moderate
    # 40-59: elevated
    # 0-39: high
    # unavailable: if summary is missing or all inputs unavailable
    score_band: RiskScoreBand = "unavailable"
    if summary is not None:
        if 80 <= final_score <= 100:
            score_band = "low"
        elif 60 <= final_score < 80:
            score_band = "moderate"
        elif 40 <= final_score < 60:
            score_band = "elevated"
        else:
            score_band = "high"
            
    # Deduplicate lists
    def _dedup(l: List[str]) -> List[str]:
        seen = set()
        return [x for x in l if not (x in seen or seen.add(x))]
        
    strengths = _dedup(strengths)
    constraints = _dedup(constraints)
    watch_items = _dedup(watch_items)
    
    disclaimer = (
        "This is a context-only unified risk score for advisory readiness context based on demo financial analysis. "
        "It is not a calibrated default model. Company records are required for production."
    )
    
    # Consolidate warnings from factors
    warnings_list = []
    if summary and summary.warnings:
        warnings_list.extend(summary.warnings)
    if precheck and precheck.warnings:
        warnings_list.extend(precheck.warnings)
        
    return UnifiedRiskScoreResult(
        company_id=analysis.snapshot.company_id if analysis.snapshot else "demo_company",
        company_name=analysis.snapshot.company_name if analysis.snapshot else "Demo Company",
        score=final_score,
        band=score_band,
        score_scale="0 to 100",
        factors=factors,
        strengths=strengths,
        constraints=constraints,
        watch_items=watch_items,
        hard_gate_status=hg_status,
        disclaimer=disclaimer,
        warnings=warnings_list
    )
