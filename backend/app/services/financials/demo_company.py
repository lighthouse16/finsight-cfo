from app.models.financials import (
    CompanyFinancialSnapshot,
    IncomeStatementPeriod,
    BalanceSheetPeriod,
    CashFlowStatementPeriod,
    DebtSchedule,
    ReceivablesAging
)

def get_demo_financial_snapshot() -> CompanyFinancialSnapshot:
    """
    Generates a realistic, accounting-consistent CompanyFinancialSnapshot
    for Harbour & Finch Trading Ltd.
    """
    # 1. Income Statement for FY2025
    income_statement = IncomeStatementPeriod(
        revenue=62_500_000.0,
        cogs=50_937_500.0,
        gross_profit=11_562_500.0,
        operating_expenses=7_562_500.0,
        ebit=4_000_000.0,
        depreciation_amortization=800_000.0,
        ebitda=4_800_000.0,
        interest_expense=450_000.0,
        ebt=3_550_000.0,
        taxes=585_000.0,
        net_income=2_965_000.0
    )

    # 2. Balance Sheet as of FY2025
    balance_sheet = BalanceSheetPeriod(
        cash=3_200_000.0,
        accounts_receivable=8_900_000.0,
        inventory=6_100_000.0,
        prepaid=200_000.0,
        current_assets=18_400_000.0,
        ppe_net=4_500_000.0,
        total_assets=22_900_000.0,
        accounts_payable=5_400_000.0,
        accrued=5_100_000.0,
        short_term_debt=1_500_000.0,
        current_portion_long_term_debt=1_000_000.0,
        long_term_debt=3_500_000.0,
        lease_liabilities=500_000.0,
        current_liabilities=13_500_000.0,
        total_liabilities=17_000_000.0,
        equity=5_900_000.0,
        retained_earnings=4_200_000.0
    )

    # 3. Cash Flow Statement for FY2025
    cash_flow_statement = CashFlowStatementPeriod(
        cfo=3_100_000.0,
        capex=600_000.0,
        debt_issued=1_000_000.0,
        debt_repaid=800_000.0,
        dividends=500_000.0,
        net_change_cash=2_200_000.0
    )

    # 4. Debt Schedule (reconciles with interest and total debt)
    debt_schedule = DebtSchedule(
        scheduled_interest=450_000.0,
        scheduled_principal=4_590_000.0,
        monthly_debt_service=420_000.0
    )

    # 5. Receivables Aging (sums up to accounts_receivable = 8.9M)
    receivables_aging = ReceivablesAging(
        current_0_30=5_000_000.0,
        days_31_60=2_500_000.0,
        days_61_90=1_000_000.0,
        days_90_plus=400_000.0
    )

    return CompanyFinancialSnapshot(
        company_id="harbour-finch-trading",
        company_name="Harbour & Finch Trading Ltd.",
        sector_code="4754-2017",
        sector_name="Electronics Import / Trading & Distribution",
        reporting_period="FY2025",
        currency="HKD",
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        cash_flow_statement=cash_flow_statement,
        debt_schedule=debt_schedule,
        receivables_aging=receivables_aging,
        metadata={
            "freshness": "workspace-derived",
            "last_audit_date": "2025-12-31",
            "usd_import_cost_percent": 0.72,
            "cny_supplier_payables_percent": 0.38
        }
    )
