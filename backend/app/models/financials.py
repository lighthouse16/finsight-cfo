from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class FinancialsBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class IncomeStatementPeriod(FinancialsBaseModel):
    revenue: float
    cogs: float
    gross_profit: Optional[float] = None
    operating_expenses: float
    ebit: float
    depreciation_amortization: float
    ebitda: float
    interest_expense: float
    ebt: float
    taxes: float
    net_income: float

class BalanceSheetPeriod(FinancialsBaseModel):
    cash: float
    accounts_receivable: float
    inventory: float
    prepaid: float
    current_assets: float
    ppe_net: float
    total_assets: float
    accounts_payable: float
    accrued: float
    short_term_debt: float
    current_portion_long_term_debt: float
    long_term_debt: float
    lease_liabilities: float
    current_liabilities: float
    total_liabilities: float
    equity: float
    retained_earnings: Optional[float] = None

class CashFlowStatementPeriod(FinancialsBaseModel):
    cfo: float
    capex: float
    debt_issued: float
    debt_repaid: float
    dividends: float
    net_change_cash: float

class ReceivablesAging(FinancialsBaseModel):
    current_0_30: float
    days_31_60: float
    days_61_90: float
    days_90_plus: float

class DebtSchedule(FinancialsBaseModel):
    scheduled_interest: float
    scheduled_principal: float
    monthly_debt_service: Optional[float] = None

class CompanyFinancialSnapshot(FinancialsBaseModel):
    company_id: str
    company_name: str
    sector_code: Optional[str] = None
    sector_name: Optional[str] = None
    reporting_period: str
    currency: str
    income_statement: IncomeStatementPeriod
    balance_sheet: BalanceSheetPeriod
    cash_flow_statement: CashFlowStatementPeriod
    debt_schedule: DebtSchedule
    receivables_aging: Optional[ReceivablesAging] = None
    metadata: Optional[dict] = Field(default_factory=dict)

class RatioMetric(FinancialsBaseModel):
    value: Optional[float] = None
    warning: Optional[str] = None
    label: str

class FinancialRatios(FinancialsBaseModel):
    current_ratio: RatioMetric
    quick_ratio: RatioMetric
    interest_coverage: RatioMetric
    dscr: RatioMetric
    debt_ratio: RatioMetric
    net_debt_to_ebitda: RatioMetric
    dso: RatioMetric
    working_capital_gap: RatioMetric
    expected_credit_loss_ar: RatioMetric

class IntegrityCheckResult(FinancialsBaseModel):
    check_name: str
    passed: bool
    message: str
    details: Optional[dict] = None

class AltmanZScoreResult(FinancialsBaseModel):
    value: Optional[float] = None
    band: Optional[str] = None  # "safe", "grey", "distress"
    components: Optional[dict] = None  # X1, X2, X3, X4
    warnings: List[str] = Field(default_factory=list)
    source: str
    methodology_label: str

class ReceivablesRiskResult(FinancialsBaseModel):
    total_ar: float
    expected_credit_loss: Optional[float] = None
    ecl_ratio: Optional[float] = None
    ar_90_plus_concentration: Optional[float] = None
    zone: Optional[str] = None  # "low", "moderate", "elevated"
    warnings: List[str] = Field(default_factory=list)
    source: str
    methodology_label: str

class FinancialRiskDiagnostics(FinancialsBaseModel):
    altman_z_score: AltmanZScoreResult = Field(..., alias="altmanZScore")
    receivables_risk: ReceivablesRiskResult = Field(..., alias="receivablesRisk")

class ProjectionAssumptions(FinancialsBaseModel):
    forecast_years: int = Field(5, alias="forecastYears")
    revenue_growth_start: float = Field(..., alias="revenueGrowthStart")
    revenue_growth_terminal: float = Field(..., alias="revenueGrowthTerminal")
    ebit_margin: float = Field(..., alias="ebitMargin")
    da_percent_revenue: float = Field(..., alias="daPercentRevenue")
    capex_percent_revenue: float = Field(..., alias="capexPercentRevenue")
    nwc_percent_incremental_revenue: float = Field(..., alias="nwcPercentIncrementalRevenue")
    tax_rate: float = Field(..., alias="taxRate")
    terminal_growth_reference: Optional[float] = Field(None, alias="terminalGrowthReference")
    currency: str

class ProjectedFinancialYear(FinancialsBaseModel):
    year: int
    revenue: float
    revenue_growth: float = Field(..., alias="revenueGrowth")
    ebit: float
    depreciation_amortization: float = Field(..., alias="depreciationAmortization")
    ebitda: float
    taxes: float
    capex: float
    delta_nwc: float = Field(..., alias="deltaNwc")
    cfo_estimate: float = Field(..., alias="cfoEstimate")
    interest_tax_adjustment: float = Field(..., alias="interestTaxAdjustment")
    fcff_primary: float = Field(..., alias="fcffPrimary")
    fcff_cross_check: float = Field(..., alias="fcffCrossCheck")
    fcff_variance: float = Field(..., alias="fcffVariance")
    warnings: List[str] = Field(default_factory=list)

class ProjectionAnalysis(FinancialsBaseModel):
    assumptions: ProjectionAssumptions
    projected_years: List[ProjectedFinancialYear] = Field(..., alias="projectedYears")
    warnings: List[str] = Field(default_factory=list)
    methodology_label: str = Field("Assumptions-Based Driver Forecast and FCFF Analysis", alias="methodologyLabel")

class ComparableBetaInput(FinancialsBaseModel):
    comparable_name: str = Field(..., alias="comparableName")
    observed_levered_beta: float = Field(..., alias="observedLeveredBeta")
    debt_to_equity: float = Field(..., alias="debtToEquity")
    tax_rate: float = Field(..., alias="taxRate")
    unlevered_beta: Optional[float] = Field(None, alias="unleveredBeta")

class WaccAssumptions(FinancialsBaseModel):
    risk_free_rate: float = Field(..., alias="riskFreeRate")
    observed_beta: float = Field(..., alias="observedBeta")
    target_debt_weight: float = Field(..., alias="targetDebtWeight")
    target_equity_weight: float = Field(..., alias="targetEquityWeight")
    equity_risk_premium: float = Field(..., alias="equityRiskPremium")
    size_premium: float = Field(..., alias="sizePremium")
    industry_risk_premium: float = Field(..., alias="industryRiskPremium")
    company_specific_premium: float = Field(..., alias="companySpecificPremium")
    pre_tax_cost_of_debt: float = Field(..., alias="preTaxCostOfDebt")
    tax_rate: float = Field(..., alias="taxRate")
    terminal_growth_rate: float = Field(..., alias="terminalGrowthRate")
    exit_multiple: Optional[float] = Field(None, alias="exitMultiple")
    currency: str
    use_book_weights_as_proxy: bool = Field(True, alias="useBookWeightsAsProxy")
    comparable_betas: Optional[List[ComparableBetaInput]] = Field(None, alias="comparableBetas")

class WaccResult(FinancialsBaseModel):
    observed_beta: float = Field(..., alias="observedBeta")
    unlevered_beta: float = Field(..., alias="unleveredBeta")
    relevered_beta: float = Field(..., alias="releveredBeta")
    cost_of_equity: float = Field(..., alias="costOfEquity")
    pre_tax_cost_of_debt: float = Field(..., alias="preTaxCostOfDebt")
    after_tax_cost_of_debt: float = Field(..., alias="afterTaxCostOfDebt")
    debt_weight: float = Field(..., alias="debtWeight")
    equity_weight: float = Field(..., alias="equityWeight")
    wacc: float
    warnings: List[str] = Field(default_factory=list)

class DcfValuationYear(FinancialsBaseModel):
    year: int
    fcff: float
    discount_factor: float = Field(..., alias="discountFactor")
    pv_fcff: float = Field(..., alias="pvFcff")

class DcfValuationResult(FinancialsBaseModel):
    valuation_years: List[DcfValuationYear] = Field(..., alias="valuationYears")
    pv_explicit_fcff: float = Field(..., alias="pvExplicitFcff")
    terminal_value_gordon_growth: Optional[float] = Field(None, alias="terminalValueGordonGrowth")
    pv_terminal_value: Optional[float] = Field(None, alias="pvTerminalValue")
    enterprise_value: Optional[float] = Field(None, alias="enterpriseValue")
    total_debt: float = Field(..., alias="totalDebt")
    cash: float
    net_debt: float = Field(..., alias="netDebt")
    equity_value: Optional[float] = Field(None, alias="equityValue")
    implied_ev_ebitda: Optional[float] = Field(None, alias="impliedEvEbitda")
    terminal_growth_rate: float = Field(..., alias="terminalGrowthRate")
    wacc: float
    terminal_value_share_of_enterprise_value: Optional[float] = Field(None, alias="terminalValueShareOfEnterpriseValue")
    exit_multiple_terminal_value: Optional[float] = Field(None, alias="exitMultipleTerminalValue")
    implied_exit_multiple: Optional[float] = Field(None, alias="impliedExitMultiple")
    warnings: List[str] = Field(default_factory=list)

class ValuationSensitivityPoint(FinancialsBaseModel):
    wacc: float
    terminal_growth_rate: float = Field(..., alias="terminalGrowthRate")
    enterprise_value: Optional[float] = Field(None, alias="enterpriseValue")
    equity_value: Optional[float] = Field(None, alias="equityValue")
    is_valid: bool = Field(True, alias="isValid")
    warning: Optional[str] = None

class ValuationSanityCheck(FinancialsBaseModel):
    name: str
    status: str  # "pass" | "warning" | "fail"
    message: str
    value: Optional[float] = None

class ValuationAnalysis(FinancialsBaseModel):
    assumptions: WaccAssumptions
    wacc: WaccResult
    dcf: DcfValuationResult
    sensitivity: List[ValuationSensitivityPoint] = Field(default_factory=list)
    sanity_checks: List[ValuationSanityCheck] = Field(default_factory=list, alias="sanityChecks")
    warnings: List[str] = Field(default_factory=list)

class FinancialSignal(FinancialsBaseModel):
    key: str
    label: str
    value: Optional[float] = None
    unit: Optional[str] = None
    band: str  # "strong" | "adequate" | "watch" | "constrained" | "unavailable"
    message: str
    evidence: str
    source: str
    warnings: List[str] = Field(default_factory=list)

class FinancialAnalysisSummary(FinancialsBaseModel):
    overall_band: str = Field(..., alias="overallBand")
    liquidity_band: str = Field(..., alias="liquidityBand")
    debt_service_band: str = Field(..., alias="debtServiceBand")
    leverage_band: str = Field(..., alias="leverageBand")
    receivables_band: str = Field(..., alias="receivablesBand")
    valuation_band: str = Field(..., alias="valuationBand")
    key_signals: List[FinancialSignal] = Field(default_factory=list, alias="keySignals")
    watch_items: List[str] = Field(default_factory=list, alias="watchItems")
    strengths: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    next_data_needed: List[str] = Field(default_factory=list, alias="nextDataNeeded")
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        "This is a demo financial analysis summary. "
        "All outputs are assumptions-based and context-only. "
        "Company records required for production advisory or credit analysis.",
        alias="disclaimer"
    )

class FinancialAnalysisResponse(FinancialsBaseModel):
    snapshot: CompanyFinancialSnapshot
    integrity_checks: List[IntegrityCheckResult] = Field(..., alias="integrityChecks")
    ratios: FinancialRatios
    risk_diagnostics: FinancialRiskDiagnostics = Field(..., alias="riskDiagnostics")
    projections: Optional[ProjectionAnalysis] = None
    valuation: Optional[ValuationAnalysis] = None
    summary: Optional[FinancialAnalysisSummary] = None
    warnings: List[str] = Field(default_factory=list)




