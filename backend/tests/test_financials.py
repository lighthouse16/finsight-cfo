import math
from fastapi.testclient import TestClient
from app.main import app
from app.services.financials.demo_company import get_demo_financial_snapshot
from app.services.financials.ratio_engine import (
    calculate_ratios,
    calculate_total_debt,
    calculate_net_debt
)
from app.services.financials.integrity_checks import run_integrity_checks
from app.services.financials.risk_diagnostics import (
    calculate_altman_z_service,
    calculate_receivables_risk
)

client = TestClient(app)

def test_total_debt_excludes_ap_and_accrued():
    # Verify that AP and accrued do not affect total debt
    tot_debt = calculate_total_debt(
        short_term_debt=100.0,
        current_portion_long_term_debt=200.0,
        long_term_debt=500.0,
        lease_liabilities=50.0
    )
    assert tot_debt == 850.0

def test_net_debt_calculation():
    assert calculate_net_debt(850.0, 150.0) == 700.0

def test_demo_balance_sheet_identity_passes():
    snapshot = get_demo_financial_snapshot()
    checks = run_integrity_checks(snapshot)
    
    bs_check = next(c for c in checks if c.check_name == "Balance Sheet Identity")
    assert bs_check.passed is True
    
    # Also verify other checks in demo data
    for check in checks:
        assert check.passed is True, f"Check {check.check_name} failed: {check.message}"

def test_ratio_calculations():
    snapshot = get_demo_financial_snapshot()
    ratios = calculate_ratios(snapshot)
    
    # Current ratio: 18.4M / 13.5M = 1.36296
    assert ratios.current_ratio.value is not None
    assert round(ratios.current_ratio.value, 4) == round(18_400_000.0 / 13_500_000.0, 4)
    
    # Quick ratio: (18.4M - 6.1M - 0.2M) / 13.5M = 12.1M / 13.5M = 0.896296
    assert ratios.quick_ratio.value is not None
    assert round(ratios.quick_ratio.value, 4) == round(12_100_000.0 / 13_500_000.0, 4)
    
    # Interest coverage: 4M / 450K = 8.8889
    assert ratios.interest_coverage.value is not None
    assert round(ratios.interest_coverage.value, 4) == round(4_000_000.0 / 450_000.0, 4)
    
    # DSCR: CADS / 5.04M
    # CADS = 4.8M - 585K - 600K - 500K = 3.115M
    # DSCR = 3.115M / 5.04M = 0.618055
    assert ratios.dscr.value is not None
    assert round(ratios.dscr.value, 4) == round(3_115_000.0 / 5_040_000.0, 4)
    
    # Debt ratio: 6.5M / 22.9M = 0.28384
    assert ratios.debt_ratio.value is not None
    assert round(ratios.debt_ratio.value, 4) == round(6_500_000.0 / 22_900_000.0, 4)
    
    # Net debt to EBITDA: (6.5M - 3.2M) / 4.8M = 3.3M / 4.8M = 0.6875
    assert ratios.net_debt_to_ebitda.value is not None
    assert round(ratios.net_debt_to_ebitda.value, 4) == 0.6875
    
    # DSO: 8.9M / 62.5M * 365 = 51.976
    assert ratios.dso.value is not None
    assert round(ratios.dso.value, 4) == round(8_900_000.0 / 62_500_000.0 * 365, 4)
    
    # Working capital gap: 8.9M + 6.1M + 0.2M - 5.4M - 5.1M = 4.7M
    assert ratios.working_capital_gap.value == 4_700_000.0
    
    # Expected credit loss AR: 5.0M * 0.005 + 2.5M * 0.02 + 1.0M * 0.08 + 0.4M * 0.25 = 255K
    assert ratios.expected_credit_loss_ar.value == 255_000.0

def test_zero_denominator_handling():
    # Create a snapshot with zero/empty values to trigger divide-by-zero
    base_snapshot = get_demo_financial_snapshot()
    
    # Zero current liabilities
    base_snapshot.balance_sheet.current_liabilities = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.current_ratio.value is None
    assert "zero" in ratios.current_ratio.warning.lower() or "liabilities" in ratios.current_ratio.warning.lower()
    assert ratios.quick_ratio.value is None
    assert "zero" in ratios.quick_ratio.warning.lower() or "liabilities" in ratios.quick_ratio.warning.lower()

    # Zero interest expense
    base_snapshot = get_demo_financial_snapshot()
    base_snapshot.income_statement.interest_expense = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.interest_coverage.value is None
    assert "zero" in ratios.interest_coverage.warning.lower() or "interest" in ratios.interest_coverage.warning.lower()

    # Zero debt service
    base_snapshot = get_demo_financial_snapshot()
    base_snapshot.debt_schedule.scheduled_interest = 0.0
    base_snapshot.debt_schedule.scheduled_principal = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.dscr.value is None
    assert "zero" in ratios.dscr.warning.lower() or "service" in ratios.dscr.warning.lower()

    # Zero total assets
    base_snapshot = get_demo_financial_snapshot()
    base_snapshot.balance_sheet.total_assets = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.debt_ratio.value is None
    assert "zero" in ratios.debt_ratio.warning.lower() or "assets" in ratios.debt_ratio.warning.lower()

    # Zero revenue
    base_snapshot = get_demo_financial_snapshot()
    base_snapshot.income_statement.revenue = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.dso.value is None
    assert "zero" in ratios.dso.warning.lower() or "revenue" in ratios.dso.warning.lower()

def test_negative_ebitda_and_missing_aging_handling():
    base_snapshot = get_demo_financial_snapshot()
    
    # Negative EBITDA
    base_snapshot.income_statement.ebitda = -100_000.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.net_debt_to_ebitda.value is None
    assert "negative" in ratios.net_debt_to_ebitda.warning.lower()

    # Zero EBITDA
    base_snapshot.income_statement.ebitda = 0.0
    ratios = calculate_ratios(base_snapshot)
    assert ratios.net_debt_to_ebitda.value is None
    assert "zero" in ratios.net_debt_to_ebitda.warning.lower()

    # Missing Receivables Aging
    base_snapshot = get_demo_financial_snapshot()
    base_snapshot.receivables_aging = None
    ratios = calculate_ratios(base_snapshot)
    assert ratios.expected_credit_loss_ar.value is None
    assert "missing" in ratios.expected_credit_loss_ar.warning.lower() or "aging" in ratios.expected_credit_loss_ar.warning.lower()

def test_demo_endpoint_response():
    response = client.get("/api/financials/demo-analysis")
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure exists
    assert "snapshot" in data
    assert "integrityChecks" in data
    assert "ratios" in data
    assert "riskDiagnostics" in data
    assert "warnings" in data
    
    # Verify no Infinity or NaN is present in JSON
    ratios = data["ratios"]
    for ratio_name, ratio_data in ratios.items():
        val = ratio_data["value"]
        assert val is None or isinstance(val, (int, float))
        if val is not None:
            assert not math.isinf(val)
            assert not math.isnan(val)
            
    risk = data["riskDiagnostics"]
    assert "altmanZScore" in risk
    assert "receivablesRisk" in risk
    z_val = risk["altmanZScore"]["value"]
    assert z_val is None or (isinstance(z_val, (int, float)) and not math.isinf(z_val) and not math.isnan(z_val))
            
    snapshot = data["snapshot"]
    assert snapshot["companyName"] == "Harbour & Finch Trading Ltd."

def test_altman_z_service_calculation():
    snapshot = get_demo_financial_snapshot()
    res = calculate_altman_z_service(snapshot)
    assert res.value is not None
    assert round(res.value, 4) == round(3.53978, 4)
    assert res.band == "safe"
    assert "X1" in res.components
    assert res.components["X1"] == 4_900_000.0 / 22_900_000.0
    assert len(res.warnings) == 0

def test_altman_z_band_mapping():
    snapshot = get_demo_financial_snapshot()
    snapshot.income_statement.ebit = -20_000_000.0
    res = calculate_altman_z_service(snapshot)
    assert res.value is not None
    assert res.value < 1.10
    assert res.band == "distress"

    snapshot.income_statement.ebit = -3_000_000.0
    res = calculate_altman_z_service(snapshot)
    assert res.value is not None
    assert 1.10 <= res.value <= 2.60
    assert res.band == "grey"

def test_altman_z_missing_retained_earnings():
    snapshot = get_demo_financial_snapshot()
    snapshot.balance_sheet.retained_earnings = None
    res = calculate_altman_z_service(snapshot)
    assert res.value is None
    assert res.band is None
    assert len(res.warnings) > 0
    assert "missing" in res.warnings[0].lower()

def test_receivables_risk_calculation():
    snapshot = get_demo_financial_snapshot()
    res = calculate_receivables_risk(snapshot)
    assert res.total_ar == 8_900_000.0
    assert res.expected_credit_loss == 255_000.0
    assert round(res.ecl_ratio, 4) == round(255_000.0 / 8_900_000.0, 4)
    assert round(res.ar_90_plus_concentration, 4) == round(400_000.0 / 8_900_000.0, 4)
    assert res.zone == "moderate"

def test_receivables_risk_elevated_zone():
    snapshot = get_demo_financial_snapshot()
    snapshot.receivables_aging.days_90_plus = 2_000_000.0
    snapshot.balance_sheet.accounts_receivable = 10_500_000.0
    res = calculate_receivables_risk(snapshot)
    assert res.zone == "elevated"

def test_receivables_risk_zero_ar():
    snapshot = get_demo_financial_snapshot()
    snapshot.balance_sheet.accounts_receivable = 0.0
    res = calculate_receivables_risk(snapshot)
    assert res.total_ar == 0.0
    assert res.expected_credit_loss == 0.0
    assert res.ecl_ratio is None
    assert res.zone is None
    assert len(res.warnings) > 0
    assert "zero" in res.warnings[0].lower()
