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

class FinancialAnalysisResponse(FinancialsBaseModel):
    snapshot: CompanyFinancialSnapshot
    integrity_checks: List[IntegrityCheckResult] = Field(..., alias="integrityChecks")
    ratios: FinancialRatios
    warnings: List[str] = Field(default_factory=list)
