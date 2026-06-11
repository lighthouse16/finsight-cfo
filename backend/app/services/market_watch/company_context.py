"""
Demo/Workspace company context service for Market Watch.

Provides workspace company profile for context-aware market intelligence.
"""

from typing import Optional
from fastapi import HTTPException
from pydantic import ValidationError
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.models.errors import raise_missing_workspace_error, raise_insufficient_data_error
from app.models.market_watch import ConnectedRecord, CompanyProfile, CompanyExposure, CompanyContextResponse
from app.models.financials import CompanyFinancialSnapshot
from app.services.financials.ratio_engine import calculate_ratios


def get_demo_company_profile() -> CompanyProfile:
    """Return demo connected company profile for Market Watch context."""
    return CompanyProfile(
        companyName="Harbour & Finch Trading Ltd.",
        sector="Electronics Import / Trading & Distribution",
        geography="Hong Kong / GBA",
        revenueTtmHkd=42_800_000,
        cashBalanceHkd=3_200_000,
        receivablesHkd=8_900_000,
        payablesHkd=5_400_000,
        inventoryHkd=6_100_000,
        dsoDays=52,
        dpoDays=45,
        inventoryDays=61,
        grossMarginPercent=18.5,
        floatingRateDebtHkd=6_500_000,
        monthlyDebtServiceHkd=420_000,
        cnySupplierPayablesPercent=38,
        usdImportCostPercent=72,
        topCustomerConcentrationPercent=31,
        workingCapitalGapHkd=4_700_000,
        connectedRecords=[
            ConnectedRecord(
                id="bank-transactions",
                label="Bank Transactions",
                status="connected"
            ),
            ConnectedRecord(
                id="invoices",
                label="Invoices",
                status="connected"
            ),
            ConnectedRecord(
                id="receivables-aging",
                label="Receivables Aging",
                status="connected"
            ),
            ConnectedRecord(
                id="payables-schedule",
                label="Payables Schedule",
                status="connected"
            ),
            ConnectedRecord(
                id="debt-schedule",
                label="Debt Schedule",
                status="connected"
            ),
            ConnectedRecord(
                id="supplier-contracts",
                label="Supplier Contracts",
                status="partial"
            ),
        ]
    )


def get_company_exposures() -> list[CompanyExposure]:
    """Return company-specific exposure summary for Market Watch."""
    return [
        CompanyExposure(
            id="floating-rate-debt",
            category="Debt Service",
            label="Floating-Rate Facility",
            value="HKD 6.5M",
            severity="High",
            context="Rate-sensitive debt requires HIBOR monitoring. Monthly service: HKD 420K."
        ),
        CompanyExposure(
            id="cny-payables",
            category="FX Exposure",
            label="CNY Supplier Payables",
            value="38% of payables",
            severity="Caution",
            context="CNY depreciation increases HKD-equivalent payables."
        ),
        CompanyExposure(
            id="usd-import-costs",
            category="FX Exposure",
            label="USD Import Costs",
            value="72% of COGS",
            severity="Caution",
            context="USD strength raises landed-cost base."
        ),
        CompanyExposure(
            id="receivables-cycle",
            category="Working Capital",
            label="DSO Above Benchmark",
            value="52d vs 45d sector",
            severity="Caution",
            context="Collections cycle 7 days above sector standard. Working capital gap: HKD 4.7M."
        ),
        CompanyExposure(
            id="customer-concentration",
            category="Revenue Risk",
            label="Top Customer Concentration",
            value="31%",
            severity="Neutral",
            context="Single largest customer represents 31% of receivables."
        ),
        CompanyExposure(
            id="inventory-turnover",
            category="Working Capital",
            label="Inventory Days",
            value="61d vs 60d sector",
            severity="Neutral",
            context="Inventory turnover slightly above sector average."
        ),
    ]


def get_company_context(workspace_id: Optional[str]) -> CompanyContextResponse:
    is_production = settings.APP_MODE == "production" or not settings.ALLOW_DEMO_FALLBACK
    
    ws_id = workspace_id
    if not ws_id:
        workspaces = WorkspaceStore.list_workspaces()
        if workspaces:
            ws_id = workspaces[-1].id
        else:
            if is_production:
                raise_missing_workspace_error("WORKSPACE_DATA_NOT_FOUND")
            
    snapshot = None
    if ws_id:
        snapshot = WorkspaceStore.get_active_snapshot(ws_id)
        if not snapshot and is_production:
            raise_missing_workspace_error("ACTIVE_SNAPSHOT_NOT_FOUND")
            
    if not snapshot:
        # Fallback to demo context in development if allowed
        if is_production:
            raise_missing_workspace_error("ACTIVE_SNAPSHOT_NOT_FOUND")
        return CompanyContextResponse(
            profile=get_demo_company_profile(),
            exposures=get_company_exposures(),
            dataMode="demo_workspace"
        )
        
    try:
        snap_data = CompanyFinancialSnapshot(
            company_id=snapshot.workspace_id,
            company_name=snapshot.metadata.get("companyName") or "Workspace Company",
            sector_code=snapshot.metadata.get("sectorCode"),
            sector_name=snapshot.metadata.get("sectorName") or snapshot.metadata.get("sector"),
            reporting_period=snapshot.reporting_period,
            currency=snapshot.currency,
            income_statement=snapshot.income_statement,
            balance_sheet=snapshot.balance_sheet,
            cash_flow_statement=snapshot.cash_flow_statement,
            debt_schedule=snapshot.debt_schedule,
            receivables_aging=snapshot.receivables_aging,
            metadata=snapshot.metadata,
        )
    except ValidationError as exc:
        missing = []
        for err in exc.errors():
            loc_str = " -> ".join(str(l) for l in err.get("loc", []))
            missing.append(f"{loc_str}: {err.get('msg')}")
        raise_insufficient_data_error(missing)
        
    ratios = calculate_ratios(snap_data)
    
    # Calculate DSO
    dso = int(ratios.dso.value or 0)
    
    # Calculate DPO
    cogs = snap_data.income_statement.cogs
    ap = snap_data.balance_sheet.accounts_payable
    dpo = int(ap / cogs * 365) if cogs > 0 else 45
    
    # Calculate Inventory Days
    inv = snap_data.balance_sheet.inventory
    inv_days = int(inv / cogs * 365) if cogs > 0 else 60
    
    # Gross margin
    rev = snap_data.income_statement.revenue
    gp = snap_data.income_statement.gross_profit if snap_data.income_statement.gross_profit is not None else (rev - cogs)
    gross_margin = float(gp / rev * 100) if rev > 0 else 0.0
    
    # Floating rate debt
    floating_rate = int(snap_data.balance_sheet.short_term_debt + snap_data.balance_sheet.long_term_debt)
    
    # Monthly debt service
    monthly_service = int(snap_data.debt_schedule.monthly_debt_service) if snap_data.debt_schedule.monthly_debt_service is not None else int(snap_data.debt_schedule.scheduled_interest + snap_data.debt_schedule.scheduled_principal)
    
    cny_pct = int(snap_data.metadata.get("cnySupplierPayablesPercent", 38))
    usd_pct = int(snap_data.metadata.get("usdImportCostPercent", 72))
    cust_pct = int(snap_data.metadata.get("topCustomerConcentrationPercent", 31))
    wc_gap = int(ratios.working_capital_gap.value or 0)
    
    profile = CompanyProfile(
        companyName=snap_data.company_name,
        sector=snap_data.sector_name or "Electronics Import / Trading & Distribution",
        geography=snap_data.metadata.get("geography") or "Hong Kong / GBA",
        revenueTtmHkd=int(snap_data.income_statement.revenue),
        cashBalanceHkd=int(snap_data.balance_sheet.cash),
        receivablesHkd=int(snap_data.balance_sheet.accounts_receivable),
        payablesHkd=int(snap_data.balance_sheet.accounts_payable),
        inventoryHkd=int(snap_data.balance_sheet.inventory),
        dsoDays=dso,
        dpoDays=dpo,
        inventoryDays=inv_days,
        grossMarginPercent=gross_margin,
        floatingRateDebtHkd=floating_rate,
        monthlyDebtServiceHkd=monthly_service,
        cnySupplierPayablesPercent=cny_pct,
        usdImportCostPercent=usd_pct,
        topCustomerConcentrationPercent=cust_pct,
        workingCapitalGapHkd=wc_gap,
        connectedRecords=[
            ConnectedRecord(id="bank-transactions", label="Bank Transactions", status="connected" if snap_data.metadata.get("bank_connected") else "missing"),
            ConnectedRecord(id="invoices", label="Invoices", status="connected"),
            ConnectedRecord(id="receivables-aging", label="Receivables Aging", status="connected" if snap_data.receivables_aging else "missing"),
            ConnectedRecord(id="payables-schedule", label="Payables Schedule", status="connected"),
            ConnectedRecord(id="debt-schedule", label="Debt Schedule", status="connected"),
            ConnectedRecord(id="supplier-contracts", label="Supplier Contracts", status="missing"),
        ]
    )
    
    # exposures
    exposures = []
    if floating_rate > 0:
        exposures.append(CompanyExposure(
            id="floating-rate-debt",
            category="Debt Service",
            label="Floating-Rate Facility",
            value=f"{snap_data.currency} {floating_rate / 1_000_000:.1f}M",
            severity="High",
            context=f"Rate-sensitive debt requires HIBOR monitoring. Monthly service: {snap_data.currency} {monthly_service / 1_000:.0f}K."
        ))
        
    exposures.extend([
        CompanyExposure(
            id="cny-payables",
            category="FX Exposure",
            label="CNY Supplier Payables",
            value=f"{cny_pct}% of payables",
            severity="Caution" if cny_pct > 20 else "Neutral",
            context="CNY depreciation increases HKD-equivalent payables."
        ),
        CompanyExposure(
            id="usd-import-costs",
            category="FX Exposure",
            label="USD Import Costs",
            value=f"{usd_pct}% of COGS",
            severity="Caution" if usd_pct > 50 else "Neutral",
            context="USD strength raises landed-cost base."
        )
    ])
    
    if dso > 45:
        exposures.append(CompanyExposure(
            id="receivables-cycle",
            category="Working Capital",
            label="DSO Above Benchmark",
            value=f"{dso}d vs 45d sector",
            severity="Caution",
            context=f"Collections cycle {dso - 45} days above sector standard. Working capital gap: {snap_data.currency} {wc_gap / 1_000_000:.1f}M."
        ))
    else:
        exposures.append(CompanyExposure(
            id="receivables-cycle",
            category="Working Capital",
            label="DSO Within Benchmark",
            value=f"{dso}d vs 45d sector",
            severity="Neutral",
            context=f"Collections cycle within sector standard. Working capital gap: {snap_data.currency} {wc_gap / 1_000_000:.1f}M."
        ))
        
    exposures.append(CompanyExposure(
        id="customer-concentration",
        category="Revenue Risk",
        label="Top Customer Concentration",
        value=f"{cust_pct}%",
        severity="Caution" if cust_pct > 30 else "Neutral",
        context=f"Single largest customer represents {cust_pct}% of receivables."
    ))
    
    exposures.append(CompanyExposure(
        id="inventory-turnover",
        category="Working Capital",
        label="Inventory Days",
        value=f"{inv_days}d vs 60d sector",
        severity="Caution" if inv_days > 75 else "Neutral",
        context=f"Inventory turnover benchmarked against sector average."
    ))
    
    return CompanyContextResponse(
        profile=profile,
        exposures=exposures,
        dataMode="connected"
    )

