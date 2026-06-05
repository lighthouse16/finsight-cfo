import math
from typing import List, Optional
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import HardGatePrecheckResult, HardGateCheck, HardGateStatus, HardGateSeverity

def build_hard_gate_precheck(analysis: FinancialAnalysisResponse) -> HardGatePrecheckResult:
    """
    Consumes the financial analysis output and produces a structured,
    explainable, context-only eligibility/risk precheck for advisory workflow readiness.
    
    This is not an underwriting decision, formal credit decision, or approval/rejection engine.
    It is a context-only precheck.
    """
    checks: List[HardGateCheck] = []
    
    # --- 1. Data Integrity Check ---
    integrity_status: HardGateStatus = "unavailable"
    integrity_severity: HardGateSeverity = "low"
    integrity_msg = "No data integrity checks performed."
    integrity_evidence = "Missing integrity check results."
    integrity_warnings = []
    
    if analysis.integrity_checks:
        bs_identity_passed = True
        all_passed = True
        failed_checks = []
        
        for c in analysis.integrity_checks:
            if c.check_name == "Balance Sheet Identity":
                if not c.passed:
                    bs_identity_passed = False
            if not c.passed:
                all_passed = False
                failed_checks.append(c.check_name)
                
        if not bs_identity_passed:
            integrity_status = "fail"
            integrity_severity = "high"
            integrity_msg = "Accounting mismatch: Balance Sheet Identity check failed."
            integrity_evidence = "Total Assets do not match Total Liabilities + Equity."
            integrity_warnings.append("Balance Sheet must be in balance. Company records required for production.")
        elif not all_passed:
            integrity_status = "watch"
            integrity_severity = "medium"
            integrity_msg = f"Non-critical integrity check warning(s): {', '.join(failed_checks)} failed."
            integrity_evidence = "Certain reconciliation thresholds were exceeded."
            integrity_warnings.append("Suggest reviewing financial statement mapping before production advisory.")
        else:
            integrity_status = "pass"
            integrity_severity = "low"
            integrity_msg = "All financial data integrity checks passed successfully."
            integrity_evidence = "Balance Sheet Identity and secondary accounts reconciled within tolerance."
    
    checks.append(HardGateCheck(
        key="data_integrity",
        label="Financial Data Integrity Check",
        status=integrity_status,
        message=integrity_msg,
        evidence=integrity_evidence,
        source="Accounting Balance Sheet Check",
        severity=integrity_severity,
        required_action="Review trial balance or adjust ledger accounts" if integrity_status in ("fail", "watch") else None,
        warnings=integrity_warnings
    ))

    # --- 2. Debt Service Coverage Check ---
    dscr_status: HardGateStatus = "unavailable"
    dscr_severity: HardGateSeverity = "low"
    dscr_msg = "Debt Service Coverage Ratio (DSCR) check is unavailable."
    dscr_evidence = "No DSCR calculation available."
    dscr_warnings = []
    
    if analysis.ratios and analysis.ratios.dscr and analysis.ratios.dscr.value is not None:
        val = analysis.ratios.dscr.value
        if math.isnan(val) or math.isinf(val):
            dscr_status = "unavailable"
            dscr_severity = "low"
            dscr_msg = "Debt Service Coverage Ratio (DSCR) is invalid or unavailable."
            dscr_evidence = f"Calculated DSCR: {val}"
        else:
            dscr_evidence = f"Calculated DSCR: {val:.2f}x"
            if val < 1.0:
                dscr_status = "fail"
                dscr_severity = "high"
                dscr_msg = f"DSCR of {val:.2f}x is below 1.0x. Operating cash flow is insufficient to cover scheduled debt service obligations."
                dscr_warnings.append("Debt service capacity is limited under current metrics.")
            elif val < 1.25:
                dscr_status = "watch"
                dscr_severity = "medium"
                dscr_msg = f"DSCR of {val:.2f}x meets basic obligations but is below standard banking-grade threshold of 1.25x."
                dscr_warnings.append("Advisory watch item: margins of safety are narrow. Suggest monitoring cash flow stability.")
            else:
                dscr_status = "pass"
                dscr_severity = "low"
                dscr_msg = f"DSCR of {val:.2f}x indicates comfortable debt service capacity."
    
    checks.append(HardGateCheck(
        key="debt_service_coverage",
        label="Debt Service Coverage Check",
        status=dscr_status,
        message=dscr_msg,
        evidence=dscr_evidence,
        source="ratio_engine.dscr",
        severity=dscr_severity,
        required_action="Explore debt restructuring, refinancing, or improve cash flow generation" if dscr_status in ("fail", "watch") else None,
        warnings=dscr_warnings
    ))

    # --- 3. Liquidity Check ---
    liq_status: HardGateStatus = "unavailable"
    liq_severity: HardGateSeverity = "low"
    liq_msg = "Liquidity precheck is unavailable."
    liq_evidence = "Missing Current Ratio or Quick Ratio."
    liq_warnings = []
    
    if (analysis.ratios and 
        analysis.ratios.current_ratio and analysis.ratios.current_ratio.value is not None and
        analysis.ratios.quick_ratio and analysis.ratios.quick_ratio.value is not None):
        
        curr = analysis.ratios.current_ratio.value
        quick = analysis.ratios.quick_ratio.value
        if math.isnan(curr) or math.isinf(curr) or math.isnan(quick) or math.isinf(quick):
            liq_status = "unavailable"
            liq_severity = "low"
            liq_msg = "Liquidity metrics are invalid or unavailable."
            liq_evidence = f"Current Ratio: {curr}; Quick Ratio: {quick}"
        else:
            liq_evidence = f"Current Ratio: {curr:.2f}x; Quick Ratio: {quick:.2f}x"
            if curr < 1.0 or quick < 0.75:
                liq_status = "fail"
                liq_severity = "high"
                liq_msg = f"Liquidity buffer is weak. Current ratio ({curr:.2f}x) is below 1.0x or Quick ratio ({quick:.2f}x) is below 0.75x."
                liq_warnings.append("Current obligations exceed liquid resources.")
            elif curr < 1.5 or quick < 1.0:
                liq_status = "watch"
                liq_severity = "medium"
                liq_msg = f"Liquidity buffer is thin. Current ratio ({curr:.2f}x) is under 1.5x or Quick ratio ({quick:.2f}x) is under 1.0x."
                liq_warnings.append("Warrants monitoring: liquidity buffers are narrow for short-term working capital needs.")
            else:
                liq_status = "pass"
                liq_severity = "low"
                liq_msg = "Liquidity metrics indicate sufficient near-term buffer."
            
    checks.append(HardGateCheck(
        key="liquidity",
        label="Liquidity Buffer Precheck",
        status=liq_status,
        message=liq_msg,
        evidence=liq_evidence,
        source="ratio_engine.liquidity",
        severity=liq_severity,
        required_action="Optimize working capital cycles or secure backup liquidity" if liq_status in ("fail", "watch") else None,
        warnings=liq_warnings
    ))

    # --- 4. Leverage Check ---
    lev_status: HardGateStatus = "unavailable"
    lev_severity: HardGateSeverity = "low"
    lev_msg = "Leverage precheck is unavailable."
    lev_evidence = "Missing Net Debt to EBITDA ratio."
    lev_warnings = []
    
    if analysis.ratios and analysis.ratios.net_debt_to_ebitda and analysis.ratios.net_debt_to_ebitda.value is not None:
        val = analysis.ratios.net_debt_to_ebitda.value
        if math.isnan(val) or math.isinf(val):
            lev_status = "unavailable"
            lev_severity = "low"
            lev_msg = "Leverage metric is invalid or unavailable."
            lev_evidence = f"Net Debt / EBITDA: {val}"
        else:
            lev_evidence = f"Net Debt / EBITDA: {val:.2f}x"
            if val > 3.5:
                lev_status = "fail"
                lev_severity = "high"
                lev_msg = f"Net Debt / EBITDA of {val:.2f}x exceeds standard advisory boundary (3.5x)."
                lev_warnings.append("Elevated leverage: high debt load relative to operating earnings.")
            elif val >= 2.0:
                lev_status = "watch"
                lev_severity = "medium"
                lev_msg = f"Net Debt / EBITDA of {val:.2f}x is moderate (between 2.0x and 3.5x)."
                lev_warnings.append("Warrants monitoring: leverage is in the transitional watch range.")
            else:
                lev_status = "pass"
                lev_severity = "low"
                lev_msg = f"Net Debt / EBITDA of {val:.2f}x is low, indicating strong balance sheet headroom."
            
    checks.append(HardGateCheck(
        key="leverage",
        label="Leverage Profile Precheck",
        status=lev_status,
        message=lev_msg,
        evidence=lev_evidence,
        source="ratio_engine.net_debt_to_ebitda",
        severity=lev_severity,
        required_action="Consider equity injection or plan debt paydown" if lev_status in ("fail", "watch") else None,
        warnings=lev_warnings
    ))

    # --- 5. Receivables Quality Check ---
    ar_status: HardGateStatus = "unavailable"
    ar_severity: HardGateSeverity = "low"
    ar_msg = "Receivables precheck is unavailable."
    ar_evidence = "Missing Receivables Risk analysis."
    ar_warnings = []
    
    if analysis.risk_diagnostics and analysis.risk_diagnostics.receivables_risk:
        r = analysis.risk_diagnostics.receivables_risk
        ecl_ratio = r.ecl_ratio
        ar_90_plus = r.ar_90_plus_concentration
        
        if ecl_ratio is not None and (math.isnan(ecl_ratio) or math.isinf(ecl_ratio)):
            ar_status = "unavailable"
            ar_severity = "low"
            ar_msg = "Receivables risk metrics are invalid or unavailable."
            ar_evidence = f"ECL Ratio: {ecl_ratio}"
        else:
            ecl_ratio_str = f"{ecl_ratio:.2%}" if ecl_ratio is not None else "N/A"
            ar_90_plus_str = f"{ar_90_plus:.2%}" if ar_90_plus is not None else "N/A"
            ar_evidence = f"ECL Ratio: {ecl_ratio_str}; 90+ Day Concentration: {ar_90_plus_str}"
            
            if r.zone == "elevated":
                ar_status = "fail"
                ar_severity = "high"
                ar_msg = "Receivables quality check indicates elevated risk. High ECL ratio or significant 90+ day aging."
                ar_warnings.append("Receivables concentration: collection cycles may show lag.")
            elif r.zone == "moderate":
                ar_status = "watch"
                ar_severity = "medium"
                ar_msg = "Receivables quality check indicates moderate risk. Aging or collection cycles show mild lag."
                ar_warnings.append("Suggest checking collection protocols and customer terms.")
            elif r.zone == "low":
                ar_status = "pass"
                ar_severity = "low"
                ar_msg = "Receivables risk is low; collection and aging metrics are within normal parameters."
            
    checks.append(HardGateCheck(
        key="receivables_quality",
        label="Receivables Quality Precheck",
        status=ar_status,
        message=ar_msg,
        evidence=ar_evidence,
        source="risk_diagnostics.receivables_risk",
        severity=ar_severity,
        required_action="Review credit policies and accelerate collections" if ar_status in ("fail", "watch") else None,
        warnings=ar_warnings
    ))

    # --- 6. Distress Diagnostic Check ---
    distress_status: HardGateStatus = "unavailable"
    distress_severity: HardGateSeverity = "low"
    distress_msg = "Altman Z'' distress check is unavailable."
    distress_evidence = "Missing Altman Z'' result."
    distress_warnings = []
    
    if analysis.risk_diagnostics and analysis.risk_diagnostics.altman_z_score:
        z = analysis.risk_diagnostics.altman_z_score
        val = z.value
        if val is not None and (math.isnan(val) or math.isinf(val)):
            distress_status = "unavailable"
            distress_severity = "low"
            distress_msg = "Altman Z'' distress metrics are invalid or unavailable."
            distress_evidence = f"Altman Z'' Score: {val}"
        else:
            distress_evidence = f"Altman Z'' Score: {val:.2f}" if val is not None else "Altman Z'' Score: N/A"
            if z.band == "distress":
                distress_status = "fail"
                distress_severity = "high"
                distress_msg = f"Altman Z'' Score of {val:.2f} is in the distress zone under this demo analysis."
                distress_warnings.append("Balance sheet ratios indicate high financial distress probability.")
            elif z.band == "grey":
                distress_status = "watch"
                distress_severity = "medium"
                distress_msg = f"Altman Z'' Score of {val:.2f} is in the grey zone."
                distress_warnings.append("Ratios are transitional. Suggest balance sheet reinforcement.")
            elif z.band == "safe":
                distress_status = "pass"
                distress_severity = "low"
                distress_msg = f"Altman Z'' Score of {val:.2f} is in the safe zone."
            
    checks.append(HardGateCheck(
        key="distress_diagnostic",
        label="Altman Z'' Distress Precheck",
        status=distress_status,
        message=distress_msg,
        evidence=distress_evidence,
        source="risk_diagnostics.altman_z_score",
        severity=distress_severity,
        required_action="Optimize capital structure and working capital efficiency" if distress_status in ("fail", "watch") else None,
        warnings=distress_warnings
    ))

    # --- 7. FCFF Projection Check ---
    fcff_status: HardGateStatus = "unavailable"
    fcff_severity: HardGateSeverity = "low"
    fcff_msg = "5-year FCFF projection check is unavailable."
    fcff_evidence = "No projections computed."
    fcff_warnings = []
    
    if analysis.projections and analysis.projections.projected_years:
        neg_years = [yr.year for yr in analysis.projections.projected_years if yr.fcff_primary < 0.0]
        fcff_evidence = f"FCFF Forecast Years: {len(analysis.projections.projected_years)}"
        if neg_years:
            fcff_status = "watch"
            fcff_severity = "medium"
            fcff_msg = f"Projected Free Cash Flow to Firm (FCFF) is negative in year(s) {neg_years} under current driver assumptions."
            fcff_warnings.append("Cash flow forecast includes negative periods. Advisory review recommended.")
        else:
            fcff_status = "pass"
            fcff_severity = "low"
            fcff_msg = "Projected FCFF is positive across all forecast horizons."
            
    checks.append(HardGateCheck(
        key="fcff_projection",
        label="FCFF Projection Precheck",
        status=fcff_status,
        message=fcff_msg,
        evidence=fcff_evidence,
        source="projection_engine.projections",
        severity=fcff_severity,
        required_action="Verify growth and margin drivers or review capital expenditure plans" if fcff_status == "watch" else None,
        warnings=fcff_warnings
    ))

    # --- 8. Valuation Sanity Check ---
    val_status: HardGateStatus = "unavailable"
    val_severity: HardGateSeverity = "low"
    val_msg = "Valuation sanity check is unavailable."
    val_evidence = "No valuation computed."
    val_warnings = []
    
    if analysis.valuation:
        sanity_checks = analysis.valuation.sanity_checks
        has_fail = any(sc.status == "fail" for sc in sanity_checks)
        has_warning = any(sc.status == "warning" for sc in sanity_checks)
        val_evidence = f"Valuation sanity checks completed: {len(sanity_checks)}"
        
        if has_fail:
            val_status = "fail"
            val_severity = "high"
            val_msg = "Valuation precheck failed. Implied multiple or WACC assumptions violate model logic."
            val_warnings.append("Valuation sanity mismatch: cost of capital or terminal growth values are inconsistent.")
        elif has_warning:
            val_status = "watch"
            val_severity = "medium"
            val_msg = "Valuation precheck warrants attention due to warnings in beta or terminal value dependency."
            val_warnings.append("High terminal value share (>85%) or beta variation observed.")
        else:
            val_status = "pass"
            val_severity = "low"
            val_msg = "Valuation assumptions and implied metrics pass sanity checks."
            
    checks.append(HardGateCheck(
        key="valuation_sanity",
        label="Valuation Sanity Precheck",
        status=val_status,
        message=val_msg,
        evidence=val_evidence,
        source="valuation_engine.sanity_checks",
        severity=val_severity,
        required_action="Refine WACC parameters or terminal growth rate assumptions" if val_status in ("fail", "watch") else None,
        warnings=val_warnings
    ))

    # --- Overall Status Logic ---
    # fail: if any fail exists (regardless of severity, or if it is high severity. Let's make it fail if any fail status exists,
    # but let's check high-severity. Let's make it: if there's any status == 'fail' and severity == 'high' -> fail;
    # if no high-severity fail but there is a watch or low/med fail -> watch;
    # if all pass -> pass;
    # if all unavailable -> unavailable.)
    pass_count = sum(1 for c in checks if c.status == "pass")
    watch_count = sum(1 for c in checks if c.status == "watch")
    fail_count = sum(1 for c in checks if c.status == "fail")
    unavailable_count = sum(1 for c in checks if c.status == "unavailable")
    
    overall_status: HardGateStatus = "unavailable"
    
    # We want DSCR around 0.62 to cause debt service to fail, and overall status to be fail/watch.
    # If there are any high-severity fails: overall_status is fail.
    # Let's see: DSCR < 1.0 produces a fail check with high severity.
    # Therefore, overall_status will be fail.
    has_high_fail = any(c.status == "fail" and c.severity == "high" for c in checks)
    has_any_fail_or_watch = any(c.status in ("fail", "watch") for c in checks)
    
    if has_high_fail:
        overall_status = "fail"
    elif has_any_fail_or_watch:
        overall_status = "watch"
    elif pass_count > 0:
        overall_status = "pass"
    else:
        overall_status = "unavailable"
        
    # --- Constraints ---
    # Collect messages from failed or watched checks
    constraints = []
    for c in checks:
        if c.status == "fail":
            constraints.append(f"Coverage constraint [{c.label}]: {c.message}")
        elif c.status == "watch":
            constraints.append(f"Watch item [{c.label}]: {c.message}")
            
    # --- Next Data Needed ---
    next_data_needed = [
        "Company records required for production check.",
        "Audited financial statements for official advisory readiness.",
        "Detailed debt schedule with amortization and covenant details.",
        "Receivables aging ledger and historical customer credit losses."
    ]
    
    disclaimer = (
        "This is a context-only precheck for advisory workflow readiness based on demo financial analysis. "
        "This is not an underwriting decision, formal credit decision, or approval/rejection engine. "
        "Company records are required for production."
    )
    
    # Consolidate all warnings
    warnings_list = []
    for c in checks:
        warnings_list.extend(c.warnings)
        
    return HardGatePrecheckResult(
        company_id=analysis.snapshot.company_id if analysis.snapshot else "demo_company",
        company_name=analysis.snapshot.company_name if analysis.snapshot else "Demo Company",
        overall_status=overall_status,
        checks=checks,
        pass_count=pass_count,
        watch_count=watch_count,
        fail_count=fail_count,
        unavailable_count=unavailable_count,
        constraints=constraints,
        next_data_needed=next_data_needed,
        disclaimer=disclaimer,
        warnings=warnings_list
    )
