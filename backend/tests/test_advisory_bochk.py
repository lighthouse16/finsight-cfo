import pytest
from app.services.advisory.cdi_mock_gateway import get_cdi_mock_data
from app.services.advisory.pd_engine import calculate_pd
from app.services.advisory.loan_structuring_engine import optimize_loan_structure

def test_cdi_mock_gateway_consent():
    # Test consent granted
    resp = get_cdi_mock_data(consent_granted=True)
    assert resp.consent_token is not None
    assert resp.delivered_invoice_total > 0
    assert resp.alternative_collateral_hkd > 0
    assert len(resp.invoices) == 3
    
    # Test consent denied
    resp_denied = get_cdi_mock_data(consent_granted=False)
    assert resp_denied.consent_token is None
    assert resp_denied.delivered_invoice_total == 0
    assert resp_denied.alternative_collateral_hkd == 0

def test_pd_engine_logic():
    # Good metrics -> low PD
    good_resp = calculate_pd("test", dscr=2.5, debt_ratio=0.2, margin=0.3, cdi_collateral_hkd=1_000_000)
    assert good_resp.tier in ["Tier A (Excellent)", "Tier B (Good)"]
    assert good_resp.probability_default < 0.10
    
    # Bad metrics -> high PD
    bad_resp = calculate_pd("test", dscr=0.8, debt_ratio=0.8, margin=-0.1, cdi_collateral_hkd=0)
    assert bad_resp.tier in ["Tier E (High Risk)", "Tier D (Elevated)"]
    assert bad_resp.probability_default > 0.10
    
def test_loan_structuring_engine():
    # Mock some data instead of full analysis object
    # The function expects analysis.snapshot and analysis.ratios
    # Since it's a proxy test, we might skip testing the full engine if it requires deeply nested mock objects
    # Or we can create a tiny mock:
    class MockRatio:
        value = 1.5
    class MockRatios:
        dscr = MockRatio()
    class MockValuation:
        enterprise_value = 50_000_000.0
    class MockAnalysis:
        snapshot = None
        ratios = MockRatios()
        valuation = MockValuation()
        
    analysis = MockAnalysis()
    cdi_data = get_cdi_mock_data(consent_granted=True)
    
    resp = optimize_loan_structure("test", 20_000_000, analysis, cdi_data)
    
    # Expect SFGS to max out at 18M
    sfgs_alloc = next((f for f in resp.recommended_facilities if "SFGS" in f.facility), None)
    assert sfgs_alloc is not None
    assert sfgs_alloc.amount == 18_000_000.0
    
    # Trade Finance limit is 1.5x of 1.32M collateral = 1.98M
    trade_alloc = next((f for f in resp.recommended_facilities if "Trade" in f.facility), None)
    assert trade_alloc is not None
    assert trade_alloc.amount == 1_980_000.0
    
    # Remaining 20k should go to Working Capital Buffer
    wc_alloc = next((f for f in resp.recommended_facilities if "Working Capital" in f.facility), None)
    assert wc_alloc is not None
    assert wc_alloc.amount == 20_000.0
    
    assert resp.total_estimated_cost > 0
    assert resp.weighted_average_cost_bps > 0
