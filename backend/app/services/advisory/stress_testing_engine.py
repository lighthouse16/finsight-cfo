import math
from typing import List, Optional
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import (
    UnifiedRiskScoreResult,
    StressTestingResponse,
    StressScenarioResult,
    StressScenarioAssumption,
    StressScenarioImpact
)

def build_demo_stress_tests(
    analysis: FinancialAnalysisResponse,
    risk_score: UnifiedRiskScoreResult,
    shock_bps: int = 150,
    dso_days_shock: int = 15,
    input_cost_shock_pct: float = 3.0,
    fx_shock_pct: float = 2.0,
) -> StressTestingResponse:
    """
    Builds a context-only financial stress testing engine that applies deterministic
    scenario shocks to the demo financial analysis and reports impact deltas.
    
    This does not constitute a formal credit decision engine.
    """
    scenarios: List[StressScenarioResult] = []
    
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    summary = analysis.summary
    
    disclaimer = (
        "This is a context-only financial stress testing scenario analysis based on demo financial analysis. "
        "It does not constitute a formal credit assessment or guarantee of distress. "
        "Company records are required for production."
    )
    
    # Check if necessary data is available
    if not snapshot or not ratios or not summary:
        return StressTestingResponse(
            company_id=snapshot.company_id if snapshot else "demo_company",
            company_name=snapshot.company_name if snapshot else "Demo Company",
            base_summary_band=summary.overall_band if summary else "unavailable",
            base_risk_score=risk_score.score if risk_score else 0,
            scenarios=[],
            disclaimer=disclaimer,
            warnings=["Insufficient baseline financial data to run stress scenario models."],
            model_version="1.0.0",
            model_type="scenario_stress_test",
            calibration_status="rules_based",
            assumptions=[],
            limitations=["Not calibrated to historical default default-frequency databases."],
            data_quality={"baseline_financials_available": False},
            confidence_band="insufficient_data"
        )
        
    ebitda_base = snapshot.income_statement.ebitda
    ebit_base = snapshot.income_statement.ebit
    taxes_base = snapshot.income_statement.taxes
    ebt_base = snapshot.income_statement.ebt
    revenue_base = snapshot.income_statement.revenue
    cogs_base = snapshot.income_statement.cogs
    interest_expense_base = snapshot.income_statement.interest_expense
    
    scheduled_interest = snapshot.debt_schedule.scheduled_interest
    scheduled_principal = snapshot.debt_schedule.scheduled_principal
    total_debt_service = scheduled_interest + scheduled_principal
    
    # Calculate tax rate proxy
    tax_rate = taxes_base / ebt_base if ebt_base > 0 else 0.165
    tax_rate = max(0.0, min(tax_rate, 0.5))
    
    # Calculate CADS
    capex = snapshot.cash_flow_statement.capex
    dividends = snapshot.cash_flow_statement.dividends
    cads_base = ebitda_base - taxes_base - capex - dividends
    
    # Get base FCFF from projection year 1
    fcff_base = 0.0
    if analysis.projections and analysis.projections.projected_years:
        fcff_base = analysis.projections.projected_years[0].fcff_primary
        
    # Total debt proxy (Short term + Current portion LTD + Long term + Lease liabilities)
    total_debt = (
        snapshot.balance_sheet.short_term_debt +
        snapshot.balance_sheet.current_portion_long_term_debt +
        snapshot.balance_sheet.long_term_debt +
        snapshot.balance_sheet.lease_liabilities
    )

    # -------------------------------------------------------------------------
    # Scenario A: Rate shock (configurable bps)
    # -------------------------------------------------------------------------
    shock_decimal = shock_bps / 10000.0
    rate_assumptions = [
        StressScenarioAssumption(
            scenario_key="rate_shock",
            label=f"Rate Shock +{shock_bps} bps",
            scenario_type="rate",
            description=f"Reference rate shift of +{shock_bps} basis points (+{shock_decimal*100:.2f}%).",
            parameters={"rate_increase": shock_decimal},
            source="Market Watch reference shock parameters"
        )
    ]
    
    rate_impacts: List[StressScenarioImpact] = []
    rate_severity = "low"
    rate_takeaway = ""
    rate_warnings = []
    
    if total_debt > 0 and total_debt_service > 0 and shock_bps > 0:
        annual_increase = total_debt * shock_decimal
        stressed_interest = interest_expense_base + annual_increase
        stressed_debt_service = total_debt_service + annual_increase
        
        # Interest coverage delta
        base_coverage = ratios.interest_coverage.value or (ebit_base / interest_expense_base if interest_expense_base > 0 else 0.0)
        stressed_coverage = ebit_base / stressed_interest if stressed_interest > 0 else 0.0
        coverage_change = stressed_coverage - base_coverage
        coverage_pct = (coverage_change / base_coverage) * 100.0 if base_coverage > 0 else 0.0
        
        # DSCR delta
        base_dscr = ratios.dscr.value or (cads_base / total_debt_service if total_debt_service > 0 else 0.0)
        stressed_dscr = cads_base / stressed_debt_service if stressed_debt_service > 0 else 0.0
        dscr_change = stressed_dscr - base_dscr
        dscr_pct = (dscr_change / base_dscr) * 100.0 if base_dscr > 0 else 0.0
        
        rate_impacts.append(StressScenarioImpact(
            metric="Additional Annual Interest Cost",
            base_value=0.0,
            stressed_value=annual_increase,
            absolute_change=annual_increase,
            unit="currency",
            interpretation=f"Stressed floating-rate proxy increases annual cash interest by HKD {annual_increase:,.0f}."
        ))
        
        rate_impacts.append(StressScenarioImpact(
            metric="Interest Coverage Ratio",
            base_value=base_coverage,
            stressed_value=stressed_coverage,
            absolute_change=coverage_change,
            percent_change=coverage_pct,
            unit="x",
            interpretation=f"Interest coverage compresses from {base_coverage:.2f}x to {stressed_coverage:.2f}x."
        ))
        
        rate_impacts.append(StressScenarioImpact(
            metric="Debt Service Coverage Ratio (DSCR)",
            base_value=base_dscr,
            stressed_value=stressed_dscr,
            absolute_change=dscr_change,
            percent_change=dscr_pct,
            unit="x",
            interpretation=f"Debt service coverage margins compress from {base_dscr:.2f}x to {stressed_dscr:.2f}x."
        ))
        
        # Severity mapping
        if stressed_dscr < 1.0:
            rate_severity = "high"
            rate_takeaway = "Stressed DSCR falls below 1.0x. Cash flow covers debt service obligations only with outside liquidity."
        elif base_dscr - stressed_dscr > 0.15:
            rate_severity = "elevated"
            rate_takeaway = "DSCR decreases significantly, reducing advisory safety margins."
        elif base_dscr - stressed_dscr > 0.05:
            rate_severity = "moderate"
            rate_takeaway = "Measurable compression in coverage capacity but basic requirements remain met."
        else:
            rate_severity = "low"
            rate_takeaway = "Minor interest expense variance with negligible impact on coverage capacity."
            
        rate_band_movement = f"debt_service_band: {summary.debt_service_band} -> {'constrained' if stressed_dscr < 1.0 else ('watch' if stressed_dscr < 1.25 else 'adequate')}"
    else:
        rate_severity = "unavailable"
        rate_takeaway = "No active floating-rate debt schedule available to simulate interest shock."
        rate_band_movement = None
        rate_warnings.append("Insufficient debt structure data.")
        
    scenarios.append(StressScenarioResult(
        scenario_key="rate_shock",
        label=f"Rate Shock +{shock_bps} bps",
        scenario_type="rate",
        severity=rate_severity,
        assumptions=rate_assumptions,
        impacts=rate_impacts,
        band_movement=rate_band_movement,
        key_takeaway=rate_takeaway,
        warnings=rate_warnings,
        disclaimer=disclaimer
    ))

    # -------------------------------------------------------------------------
    # Scenario B: Receivables delay / DSO +days
    # -------------------------------------------------------------------------
    ar_assumptions = [
        StressScenarioAssumption(
            scenario_key="receivables_delay",
            label="Invoicing lag extension",
            scenario_type="receivables",
            description=f"Simulates a {dso_days_shock}-day average collection extension across active invoice registries.",
            parameters={"dso_increase_days": dso_days_shock},
            source="Receivables aging credit guidelines"
        )
    ]
    
    ar_impacts: List[StressScenarioImpact] = []
    ar_severity = "low"
    ar_takeaway = ""
    ar_warnings = []
    
    if revenue_base > 0:
        base_ar = snapshot.balance_sheet.accounts_receivable
        base_wc_gap = ratios.working_capital_gap.value or 0.0
        
        daily_rev = revenue_base / 365.0
        ar_increase = daily_rev * float(dso_days_shock)
        stressed_ar = base_ar + ar_increase
        stressed_wc_gap = base_wc_gap + ar_increase
        
        ar_impacts.append(StressScenarioImpact(
            metric="Accounts Receivable (AR) Expansion",
            base_value=base_ar,
            stressed_value=stressed_ar,
            absolute_change=ar_increase,
            percent_change=(ar_increase / base_ar) * 100.0 if base_ar > 0 else 0.0,
            unit="currency",
            interpretation=f"Collection lag locks up an additional HKD {ar_increase:,.0f} in unpaid invoices."
        ))
        
        ar_impacts.append(StressScenarioImpact(
            metric="Working Capital Gap Expansion",
            base_value=base_wc_gap,
            stressed_value=stressed_wc_gap,
            absolute_change=ar_increase,
            percent_change=(ar_increase / base_wc_gap) * 100.0 if base_wc_gap > 0 else 0.0,
            unit="currency",
            interpretation=f"Working capital gap widens to HKD {stressed_wc_gap:,.0f}, requiring backup credit facilities."
        ))
        
        if fcff_base > 0:
            stressed_fcff = fcff_base - ar_increase
            fcff_change = stressed_fcff - fcff_base
            fcff_pct = (fcff_change / fcff_base) * 100.0
            
            ar_impacts.append(StressScenarioImpact(
                metric="Free Cash Flow to Firm (FCFF) Year 1 Impact",
                base_value=fcff_base,
                stressed_value=stressed_fcff,
                absolute_change=fcff_change,
                percent_change=fcff_pct,
                unit="currency",
                interpretation=f"Additional NWC requirement reduces Year 1 firm cash generation to HKD {stressed_fcff:,.0f}."
            ))
            
            # Severity mapping
            if stressed_fcff < 0:
                ar_severity = "high"
                ar_takeaway = "DSO extension locks up liquidity, pushing Year 1 projected cash flow into negative territory."
            elif ar_increase / base_wc_gap > 0.20:
                ar_severity = "elevated"
                ar_takeaway = "Significant working capital extension required, putting pressure on credit lines."
            else:
                ar_severity = "moderate"
                ar_takeaway = "Collections slow down temporarily but the business absorbs the working capital shift."
        else:
            ar_severity = "moderate"
            ar_takeaway = "Receivables aging slows down; working capital gap expands."
            
        ar_band_movement = f"receivables_band: {summary.receivables_band} -> {'constrained' if ar_severity == 'high' else ('watch' if ar_severity in ('elevated', 'moderate') else 'adequate')}"
    else:
        ar_severity = "unavailable"
        ar_takeaway = "No baseline revenue structure available to simulate receivables delay."
        ar_band_movement = None
        ar_warnings.append("Insufficient revenue metrics.")
        
    scenarios.append(StressScenarioResult(
        scenario_key="receivables_delay",
        label=f"Receivables Delay +{dso_days_shock} Days",
        scenario_type="receivables",
        severity=ar_severity,
        assumptions=ar_assumptions,
        impacts=ar_impacts,
        band_movement=ar_band_movement,
        key_takeaway=ar_takeaway,
        warnings=ar_warnings,
        disclaimer=disclaimer
    ))

    # -------------------------------------------------------------------------
    # Scenario C: Input cost squeeze
    # -------------------------------------------------------------------------
    input_cost_decimal = input_cost_shock_pct / 100.0
    cogs_assumptions = [
        StressScenarioAssumption(
            scenario_key="input_cost_squeeze",
            label="Raw material/input cost squeeze",
            scenario_type="commodities",
            description=f"Simulates a {input_cost_shock_pct}% increase in raw material and procurement COGS inputs.",
            parameters={"cogs_increase_percent": input_cost_decimal},
            source="Commodity index shift indicators"
        )
    ]
    
    cogs_impacts: List[StressScenarioImpact] = []
    cogs_severity = "low"
    cogs_takeaway = ""
    cogs_warnings = []
    
    if cogs_base > 0 and revenue_base > 0:
        cogs_increase = cogs_base * input_cost_decimal
        stressed_cogs = cogs_base + cogs_increase
        
        base_gross_margin = (revenue_base - cogs_base) / revenue_base * 100.0
        stressed_gross_margin = (revenue_base - stressed_cogs) / revenue_base * 100.0
        margin_change = stressed_gross_margin - base_gross_margin
        
        stressed_ebitda = ebitda_base - cogs_increase
        ebitda_change = stressed_ebitda - ebitda_base
        ebitda_pct = (ebitda_change / ebitda_base) * 100.0 if ebitda_base > 0 else 0.0
        
        cogs_impacts.append(StressScenarioImpact(
            metric="Gross Margin Compression",
            base_value=base_gross_margin,
            stressed_value=stressed_gross_margin,
            absolute_change=margin_change,
            unit="percent",
            interpretation=f"Gross margin compresses from {base_gross_margin:.2f}% to {stressed_gross_margin:.2f}%."
        ))
        
        cogs_impacts.append(StressScenarioImpact(
            metric="Operating EBITDA Compression",
            base_value=ebitda_base,
            stressed_value=stressed_ebitda,
            absolute_change=abs(ebitda_change),
            percent_change=ebitda_pct,
            unit="currency",
            interpretation=f"Annual EBITDA decreases by HKD {cogs_increase:,.0f} due to higher input costs."
        ))
        
        if fcff_base > 0:
            stressed_ebit = ebit_base - cogs_increase
            stressed_taxes = max(stressed_ebit * tax_rate, 0.0)
            tax_shield_saved = taxes_base - stressed_taxes
            
            fcff_increase_net = cogs_increase - tax_shield_saved
            stressed_fcff = fcff_base - fcff_increase_net
            fcff_change = stressed_fcff - fcff_base
            fcff_pct = (fcff_change / fcff_base) * 100.0
            
            cogs_impacts.append(StressScenarioImpact(
                metric="Free Cash Flow to Firm (FCFF) Year 1 Impact",
                base_value=fcff_base,
                stressed_value=stressed_fcff,
                absolute_change=fcff_change,
                percent_change=fcff_pct,
                unit="currency",
                interpretation=f"EBITDA contraction reduces Year 1 cash flow by HKD {fcff_increase_net:,.0f} (net of tax shield)."
            ))
            
            # Severity mapping
            ebitda_drop_pct = abs(ebitda_change / ebitda_base) if ebitda_base > 0 else 0.0
            if stressed_fcff < 0 or ebitda_drop_pct > 0.20:
                cogs_severity = "high"
                cogs_takeaway = f"Input cost squeeze compresses EBITDA margins by over 20% or drives cash flow negative."
            elif ebitda_drop_pct > 0.10:
                cogs_severity = "elevated"
                cogs_takeaway = "EBITDA and cash generation drop by over 10%. Margins are squeezed."
            else:
                cogs_severity = "moderate"
                cogs_takeaway = "Input costs squeeze gross profit slightly, but the business maintains baseline EBITDA levels."
        else:
            cogs_severity = "moderate"
            cogs_takeaway = "Procurement costs compress gross margins."
            
        cogs_band_movement = f"leverage_band: {summary.leverage_band} -> {'constrained' if cogs_severity == 'high' else ('watch' if cogs_severity in ('elevated', 'moderate') else 'adequate')}"
    else:
        cogs_severity = "unavailable"
        cogs_takeaway = "No COGS baseline metrics available to model cost sensitivity."
        cogs_band_movement = None
        cogs_warnings.append("Insufficient cost metrics.")
        
    scenarios.append(StressScenarioResult(
        scenario_key="input_cost_squeeze",
        label=f"Input Cost Squeeze +{input_cost_shock_pct}%",
        scenario_type="commodities",
        severity=cogs_severity,
        assumptions=cogs_assumptions,
        impacts=cogs_impacts,
        band_movement=cogs_band_movement,
        key_takeaway=cogs_takeaway,
        warnings=cogs_warnings,
        disclaimer=disclaimer
    ))

    # -------------------------------------------------------------------------
    # Scenario D: FX import-cost stress
    # -------------------------------------------------------------------------
    fx_metadata = snapshot.metadata if (snapshot and snapshot.metadata) else {}
    usd_import_pct = fx_metadata.get("usd_import_cost_percent")
    fx_decimal = fx_shock_pct / 100.0
    
    fx_assumptions = [
        StressScenarioAssumption(
            scenario_key="fx_stress",
            label="USD/HKD import cost stress",
            scenario_type="fx",
            description=f"Simulates a {fx_shock_pct}% appreciation in USD/HKD, increasing import cost parameters.",
            parameters={"usd_hkd_appreciation": fx_decimal},
            source="FX Frankfurter provider reference metrics"
        )
    ]
    
    fx_impacts: List[StressScenarioImpact] = []
    fx_severity = "low"
    fx_takeaway = ""
    fx_warnings = []
    
    if usd_import_pct is not None and cogs_base > 0 and revenue_base > 0:
        usd_cogs = cogs_base * usd_import_pct
        annual_increase = usd_cogs * fx_decimal
        stressed_cogs = cogs_base + annual_increase
        
        base_gross_margin = (revenue_base - cogs_base) / revenue_base * 100.0
        stressed_gross_margin = (revenue_base - stressed_cogs) / revenue_base * 100.0
        margin_change = stressed_gross_margin - base_gross_margin
        
        stressed_ebitda = ebitda_base - annual_increase
        ebitda_change = stressed_ebitda - ebitda_base
        ebitda_pct = (ebitda_change / ebitda_base) * 100.0 if ebitda_base > 0 else 0.0
        
        fx_impacts.append(StressScenarioImpact(
            metric="Gross Margin Compression",
            base_value=base_gross_margin,
            stressed_value=stressed_gross_margin,
            absolute_change=margin_change,
            unit="percent",
            interpretation=f"USD COGS appreciation compresses gross margin by {abs(margin_change):.2f}%."
        ))
        
        fx_impacts.append(StressScenarioImpact(
            metric="Procurement Cost Expansion",
            base_value=0.0,
            stressed_value=annual_increase,
            absolute_change=annual_increase,
            unit="currency",
            interpretation=f"Import cost increases by HKD {annual_increase:,.0f} due to USD/HKD {fx_shock_pct}% fluctuation."
        ))
        
        if fcff_base > 0:
            stressed_ebit = ebit_base - annual_increase
            stressed_taxes = max(stressed_ebit * tax_rate, 0.0)
            tax_shield_saved = taxes_base - stressed_taxes
            
            fcff_increase_net = annual_increase - tax_shield_saved
            stressed_fcff = fcff_base - fcff_increase_net
            fcff_change = stressed_fcff - fcff_base
            fcff_pct = (fcff_change / fcff_base) * 100.0
            
            fx_impacts.append(StressScenarioImpact(
                metric="Free Cash Flow to Firm (FCFF) Year 1 Impact",
                base_value=fcff_base,
                stressed_value=stressed_fcff,
                absolute_change=fcff_change,
                percent_change=fcff_pct,
                unit="currency",
                interpretation=f"USD purchase price appreciation reduces Year 1 cash flow by HKD {fcff_increase_net:,.0f}."
            ))
            
            # Severity mapping
            ebitda_drop_pct = abs(ebitda_change / ebitda_base) if ebitda_base > 0 else 0.0
            fcff_drop_pct = abs(fcff_change / fcff_base) if fcff_base > 0 else 0.0
            if stressed_fcff < 0 or ebitda_drop_pct > 0.15 or fcff_drop_pct > 0.15:
                fx_severity = "high"
                fx_takeaway = "USD appreciation compresses EBITDA and margins, driving significant cash flow reduction."
            elif ebitda_drop_pct > 0.05 or fcff_drop_pct > 0.05:
                fx_severity = "elevated"
                fx_takeaway = "Significant margin compression due to high USD raw material imports."
            else:
                fx_severity = "moderate"
                fx_takeaway = "Moderate FX exposure impact on procurement cost margins."
        else:
            fx_severity = "moderate"
            fx_takeaway = f"USD import cost exposure increases procurement expense by {fx_shock_pct}%."
            
        fx_band_movement = f"valuation_band: {summary.valuation_band} -> {'constrained' if fx_severity == 'high' else ('watch' if fx_severity in ('elevated', 'moderate') else 'adequate')}"
    else:
        fx_severity = "unavailable"
        fx_takeaway = "No reliable USD import cost exposure parameters detected."
        fx_band_movement = None
        fx_warnings.append("USD import cost exposure details are unavailable for this company.")
        
    scenarios.append(StressScenarioResult(
        scenario_key="fx_stress",
        label=f"FX Import-Cost Stress +{fx_shock_pct}%",
        scenario_type="fx",
        severity=fx_severity,
        assumptions=fx_assumptions,
        impacts=fx_impacts,
        band_movement=fx_band_movement,
        key_takeaway=fx_takeaway,
        warnings=fx_warnings,
        disclaimer=disclaimer
    ))
    
    # Warnings consolidation
    warnings_list = []
    if summary.warnings:
        warnings_list.extend(summary.warnings)
    if risk_score.warnings:
        warnings_list.extend(risk_score.warnings)
        
    # Deduplicate warnings list
    def _dedup(l: List[str]) -> List[str]:
        seen = set()
        return [x for x in l if not (x in seen or seen.add(x))]
    warnings_list = _dedup(warnings_list)

    stress_assumptions = [
        f"Floating-rate debt interest rate increases by the specified HIBOR shock of {shock_bps} bps.",
        f"Receivables collection delays extend the working capital cycle by the specified {dso_days_shock} DSO days.",
        f"Input cost procurement expenses increase by the specified input cost shock of {input_cost_shock_pct}%.",
        f"Import procurement cost margins compress based on the specified USD/HKD appreciation shock of {fx_shock_pct}%."
    ]

    stress_limitations = [
        "Deterministic scenario analysis only; not a statistical distribution of default outcomes.",
        "Assumes direct linear pass-through of shocks without proactive management mitigation action.",
        "Not calibrated to historical default default-frequency databases."
    ]

    stress_data_quality = {
        "baseline_financials_available": snapshot is not None and ratios is not None,
        "debt_service_details_available": total_debt > 0 and total_debt_service > 0,
        "receivables_aging_available": snapshot.receivables_aging is not None,
        "fx_metadata_available": usd_import_pct is not None
    }

    confidence_band = "high" if all(stress_data_quality.values()) else "medium"

    return StressTestingResponse(
        company_id=snapshot.company_id,
        company_name=snapshot.company_name,
        base_summary_band=summary.overall_band,
        base_risk_score=risk_score.score,
        scenarios=scenarios,
        disclaimer=disclaimer,
        warnings=warnings_list,
        model_version="1.0.0",
        model_type="scenario_stress_test",
        calibration_status="rules_based",
        assumptions=stress_assumptions,
        limitations=stress_limitations,
        data_quality=stress_data_quality,
        confidence_band=confidence_band
    )



def build_bochk_stress_test(
    analysis: FinancialAnalysisResponse,
    shock_bps: int = 150
) -> 'BochkStressTestResponse':
    from app.models.advisory import BochkStressTestResponse, BochkStressRecommendation
    
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    
    company_id = snapshot.company_id if snapshot else "demo_company"
    
    disclaimer = (
        "This is a context-only deterministic stress testing scenario analysis. "
        "It is designed for the BOCHK challenge to demonstrate rate-shock logic."
    )
    
    if not snapshot or not ratios:
        return BochkStressTestResponse(
            company_id=company_id,
            base_dscr=0.0,
            stressed_dscr=0.0,
            shock_bps=shock_bps,
            status="unavailable",
            recommendations=[],
            disclaimer=disclaimer
        )
        
    ebitda_base = snapshot.income_statement.ebitda
    taxes_base = snapshot.income_statement.taxes
    capex = snapshot.cash_flow_statement.capex
    dividends = snapshot.cash_flow_statement.dividends
    cads_base = ebitda_base - taxes_base - capex - dividends
    
    total_debt = (
        snapshot.balance_sheet.short_term_debt +
        snapshot.balance_sheet.current_portion_long_term_debt +
        snapshot.balance_sheet.long_term_debt +
        snapshot.balance_sheet.lease_liabilities
    )
    
    scheduled_interest = snapshot.debt_schedule.scheduled_interest
    scheduled_principal = snapshot.debt_schedule.scheduled_principal
    total_debt_service = scheduled_interest + scheduled_principal
    
    base_dscr = ratios.dscr.value or (cads_base / total_debt_service if total_debt_service > 0 else 0.0)
    
    annual_increase = total_debt * (shock_bps / 10000.0)
    stressed_debt_service = total_debt_service + annual_increase
    
    stressed_dscr = cads_base / stressed_debt_service if stressed_debt_service > 0 else 0.0
    
    recommendations = []
    
    if stressed_dscr < 1.10:
        status = "fail"
        recommendations.append(BochkStressRecommendation(action="Interest Rate Swap Consideration", rationale="Mitigate immediate rate risk exposure on floating-rate debt."))
        recommendations.append(BochkStressRecommendation(action="SFGS Principal Moratorium", rationale="Apply for principal moratorium under SFGS to relieve debt service burden temporarily."))
    elif stressed_dscr < 1.25:
        status = "watch"
        recommendations.append(BochkStressRecommendation(action="Reduce Working Capital Draw", rationale="Lower overall debt balances to decrease interest exposure."))
        recommendations.append(BochkStressRecommendation(action="Restructure Debt Tenor", rationale="Extend maturities to reduce near-term principal obligations and improve coverage margins."))
    else:
        status = "pass"
        recommendations.append(BochkStressRecommendation(action="Maintain Capital Buffer", rationale="DSCR remains healthy under stress. Maintain liquidity buffer."))
        
    return BochkStressTestResponse(
        company_id=company_id,
        base_dscr=base_dscr,
        stressed_dscr=stressed_dscr,
        shock_bps=shock_bps,
        status=status,
        recommendations=recommendations,
        disclaimer=disclaimer
    )
