from app.models.data_room import (
    DataRoomDependency,
    DataRoomReadinessSummary,
    DataRoomRecord,
    DataRoomResponse,
)


DEMO_RECORDS = [
    DataRoomRecord(
        id="pl-statement",
        name="Profit & Loss Statement (P&L)",
        category="Core Financials",
        purpose="Drives revenue growth trend, gross margin analysis, and baseline EBITDA calculation.",
        status="demo_available",
        requiredFor=["valuation", "risk diagnostics", "stress testing"],
        lastUpdated="Connected (Demo Analysis)",
        actionLabel="Review",
    ),
    DataRoomRecord(
        id="balance-sheet",
        name="Balance Sheet",
        category="Core Financials",
        purpose="Provides cash, current assets, accounts receivable, and total liability metrics for liquidity checks.",
        status="demo_available",
        requiredFor=["valuation", "risk diagnostics", "stress testing"],
        lastUpdated="Connected (Demo Analysis)",
        actionLabel="Review",
    ),
    DataRoomRecord(
        id="cash-flow",
        name="Cash Flow Statement",
        category="Core Financials",
        purpose="Supplies operating cash flow (CFO) and capital expenditures (CapEx) to calculate free cash flows (FCFF).",
        status="demo_available",
        requiredFor=["valuation", "stress testing"],
        lastUpdated="Connected (Demo Analysis)",
        actionLabel="Review",
    ),
    DataRoomRecord(
        id="debt-schedule",
        name="Debt Amortization Schedule",
        category="Debt & Credit",
        purpose="Feeds scheduled interest/principal payments for Debt Service Coverage Ratio (DSCR) checks.",
        status="missing",
        requiredFor=["stress testing", "facility structuring"],
        lastUpdated="Pending Record Connection",
        actionLabel="Upload",
    ),
    DataRoomRecord(
        id="receivables-aging",
        name="Accounts Receivable (AR) Aging Ledger",
        category="Commercial & Trade",
        purpose="Determines Days Sales Outstanding (DSO) and expected credit loss deltas for working capital gap sizing.",
        status="missing",
        requiredFor=["risk diagnostics", "facility structuring"],
        lastUpdated="Pending Record Connection",
        actionLabel="Upload",
    ),
    DataRoomRecord(
        id="payables-schedule",
        name="Accounts Payable Schedule",
        category="Commercial & Trade",
        purpose="Identifies Days Payable Outstanding (DPO) and helps estimate supply chain financing needs.",
        status="optional",
        requiredFor=["risk diagnostics"],
        lastUpdated="Not Connected",
        actionLabel="Connect",
    ),
    DataRoomRecord(
        id="supplier-contracts",
        name="Material Supplier Contracts",
        category="Commercial & Trade",
        purpose="Exposes input-cost shocks and pricing dependencies for commodity margin stress scenarios.",
        status="optional",
        requiredFor=["stress testing"],
        lastUpdated="Not Connected",
        actionLabel="Connect",
    ),
    DataRoomRecord(
        id="facility-terms",
        name="Existing Credit Facility Terms",
        category="Debt & Credit",
        purpose="Enables matching candidate structures to outstanding debt limits, tenors, and covenant constraints.",
        status="missing",
        requiredFor=["facility structuring"],
        lastUpdated="Pending Record Connection",
        actionLabel="Upload",
    ),
    DataRoomRecord(
        id="fx-hedging-contracts",
        name="FX & Derivative Hedging Contracts",
        category="Risk & Treasury",
        purpose="Maps current hedge ratios against RMB/USD exposures to simulate net GBA cross-border risk.",
        status="optional",
        requiredFor=["stress testing"],
        lastUpdated="Not Connected",
        actionLabel="Connect",
    ),
]

DEMO_DEPENDENCIES = [
    DataRoomDependency(
        recordGroup="Financial Statements (P&L, BS, CF)",
        outputs=["Liquidity Ratios (Current/Quick)", "FCFF Projections", "Indicative DCF Valuation"],
    ),
    DataRoomDependency(
        recordGroup="Debt Amortization Schedule",
        outputs=["Debt Service Coverage Ratio (DSCR)", "Rate Shock Sensitivity (+150bps)", "Facility Fit Capacity"],
    ),
    DataRoomDependency(
        recordGroup="AR Aging Ledger",
        outputs=["Days Sales Outstanding (DSO)", "Working Capital Gap", "Receivables Financing Sizing"],
    ),
    DataRoomDependency(
        recordGroup="Supplier Contracts",
        outputs=["USD/CNY FX Exposure", "Input-Cost Squeeze Margin Impact", "Supply Chain Readiness"],
    ),
    DataRoomDependency(
        recordGroup="Existing Facility Terms",
        outputs=["Refinancing Strategy", "Credit Fit Constraints", "Covenant Headroom"],
    ),
]


def get_demo_data_room_readiness() -> DataRoomResponse:
    total_required = len([record for record in DEMO_RECORDS if record.status != "optional"])
    connected_required = len(
        [record for record in DEMO_RECORDS if record.status in ("demo_available", "connected")]
    )
    missing_required = len([record for record in DEMO_RECORDS if record.status == "missing"])
    readiness_percentage = round((connected_required / total_required) * 100) if total_required else 0

    return DataRoomResponse(
        records=DEMO_RECORDS,
        dependencies=DEMO_DEPENDENCIES,
        summary=DataRoomReadinessSummary(
            totalRequired=total_required,
            connectedRequired=connected_required,
            missingRequired=missing_required,
            readinessPercentage=readiness_percentage,
            dataMode="demo_workspace",
        ),
    )
