"""
Demo company context service for Market Watch.

Provides workspace company profile for context-aware market intelligence.
This is fixture/demo data until real company financial upload is implemented.
"""

from app.models.market_watch import ConnectedRecord, CompanyProfile, CompanyExposure


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
