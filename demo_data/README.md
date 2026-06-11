# Novus Retail Solutions Ltd — Sample Financial Statements

This folder contains realistic, internally consistent sample financial statements for a fictional Hong Kong retail SME called **Novus Retail Solutions Ltd**. 

These files can be uploaded manually in the **Data Room** to verify the end-to-end ingestion, snapshot, and analysis run flow of **FinSight CFO**.

## Files Included

1. **`pl.csv`** (Profit & Loss / Income Statement)
   - Key Metrics: Revenue $5,400,000, Gross Profit $3,300,000, EBITDA $1,500,000, Net Income $1,000,000.
2. **`bs.csv`** (Balance Sheet)
   - Key Assets: Cash $450,000, Accounts Receivable $650,000, Inventory $800,000.
   - Key Liabilities: Accounts Payable $400,000, Total Liabilities $2,000,000, Equity $1,500,000.
   - Satisfies the balance sheet identity: Total Assets ($3,500,000) = Total Liabilities ($2,000,000) + Equity ($1,500,000).
3. **`cf.csv`** (Cash Flow Statement)
   - Key Metrics: Cash Flow from Operations (CFO) $1,200,000, Capital Expenditures (CapEx) $300,000, Net Change in Cash $850,000.
4. **`debt.csv`** (Debt Schedule)
   - Key Metrics: Scheduled Interest $120,000, Scheduled Principal $200,000.
5. **`receivables.csv`** (Accounts Receivable Aging Ledger)
   - Key Metrics: Current (0-30 days) $400,000, 31-60 days $150,000, 61-90 days $70,000, 90+ days $30,000.
   - Total equals the Accounts Receivable asset on the Balance Sheet ($650,000).

## Upload Order & Setup Instructions

To run the workflow manually:
1. Open the platform and navigate to the **Data Room**.
2. Click **Add New** in the Workspaces dropdown to create a new workspace:
   - **Company Name**: `Novus Retail Solutions Ltd`
   - **Currency**: `HKD`
   - **Period**: `FY2025`
3. Map and upload each CSV file to its corresponding record row in the Data Room checklist:
   - Map `pl.csv` to **Profit & Loss Statement (P&L)**
   - Map `bs.csv` to **Balance Sheet**
   - Map `cf.csv` to **Cash Flow Statement**
   - Map `debt.csv` to **Debt Amortization Schedule**
   - Map `receivables.csv` to **Accounts Receivable (AR) Aging Ledger**
4. Verify that the files parse successfully (green checkmark indicators).
5. Click **Build Active Financial Snapshot** in the upper-right corner.
6. Verify the snapshot compiles successfully, displaying summary metrics and satisfying accounting integrity checks.
7. Navigate to the **Overview**, **Financial Health**, or **Reports** page to view the generated outputs.
