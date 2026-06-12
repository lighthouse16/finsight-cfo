import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.advisory.pd_engine import calculate_pd
from app.services.advisory.credit_scoring_engine import build_credit_scoring_result
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.financials.valuation_engine import calculate_dcf, calculate_wacc, build_default_wacc_assumptions
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score

client = TestClient(app)

def test_pd_engine_hardened_metadata():
    resp = calculate_pd("test_comp", dscr=1.5, debt_ratio=0.4, margin=0.15)
    assert resp.model_type == "indicative_pd_proxy"
    assert resp.calibration_status == "uncalibrated_proxy"
    assert "Not calibrated to historical default data." in resp.limitations
    assert "Not a formal credit decision." in resp.limitations
    assert resp.model_version == "1.0.0"
    assert "dscr_available" in resp.data_quality
    assert resp.confidence_band in ["low", "medium", "high"]

def test_credit_score_hardened_metadata_and_subscores():
    analysis = get_demo_analysis()
    resp = build_credit_scoring_result(analysis)
    
    # Assert all required sub-scores are visible
    factor_keys = [f.key for f in resp.factors]
    required_keys = [
        "coverage",
        "leverage",
        "liquidity",
        "profitability",
        "cash_flow",
        "receivables_quality",
        "stress_resilience"
    ]
    for key in required_keys:
        assert key in factor_keys, f"Missing required sub-score factor key: {key}"
        
    # Check profitability details
    profit_factor = next(f for f in resp.factors if f.key == "profitability")
    assert profit_factor.label == "Operating profitability margins"
    assert profit_factor.weight == 0.10
    assert profit_factor.raw_score >= 0
    
    # Check terminology
    assert "credit rating" not in resp.methodology_label.lower()
    assert "planning" in resp.methodology_label.lower() or "readiness" in resp.methodology_label.lower()
    
    assert resp.model_type == "deterministic_scorecard"
    assert resp.calibration_status == "rules_based"
    assert len(resp.assumptions) > 0
    assert len(resp.limitations) > 0
    assert "profitability_available" in resp.data_quality

def test_stress_tests_parameterized_endpoint_success():
    payload = {
        "company_id": "demo_company",
        "hibor_shock_bps": 200,
        "dso_days_shock": 20,
        "input_cost_shock_pct": 5.0,
        "fx_shock_pct": 3.0
    }
    response = client.post("/api/advisory/stress-tests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["modelType"] == "scenario_stress_test"
    assert data["calibrationStatus"] == "rules_based"
    
    # Check if custom parameters are reflected in scenario labels
    scenarios = data["scenarios"]
    rate_scenario = next(s for s in scenarios if s["scenarioKey"] == "rate_shock")
    assert "200 bps" in rate_scenario["label"]
    
    ar_scenario = next(s for s in scenarios if s["scenarioKey"] == "receivables_delay")
    assert "20 Days" in ar_scenario["label"]
    
    cogs_scenario = next(s for s in scenarios if s["scenarioKey"] == "input_cost_squeeze")
    assert "5.0%" in cogs_scenario["label"]

def test_stress_tests_parameterized_endpoint_out_of_bounds():
    # Invalid HIBOR shock > 1000 bps
    payload = {
        "hibor_shock_bps": 1200,
        "dso_days_shock": 15,
        "input_cost_shock_pct": 3.0,
        "fx_shock_pct": 2.0
    }
    response = client.post("/api/advisory/stress-tests", json=payload)
    assert response.status_code == 422
    
    # Invalid DSO shock > 180 days
    payload["hibor_shock_bps"] = 150
    payload["dso_days_shock"] = 200
    response = client.post("/api/advisory/stress-tests", json=payload)
    assert response.status_code == 422

    # Invalid input cost shock < -50%
    payload["dso_days_shock"] = 15
    payload["input_cost_shock_pct"] = -60.0
    response = client.post("/api/advisory/stress-tests", json=payload)
    assert response.status_code == 422

    # Invalid FX shock > 50%
    payload["input_cost_shock_pct"] = 3.0
    payload["fx_shock_pct"] = 55.0
    response = client.post("/api/advisory/stress-tests", json=payload)
    assert response.status_code == 422

def test_valuation_warnings_and_metadata():
    analysis = get_demo_analysis()
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    projections = analysis.projections
    
    # Case 1: Terminal Growth >= WACC
    assumptions = build_default_wacc_assumptions(snapshot, ratios, projections)
    wacc_res = calculate_wacc(snapshot, ratios, assumptions)
    
    # Force terminal growth rate >= WACC
    assumptions.terminal_growth_rate = wacc_res.wacc + 0.01
    
    res = calculate_dcf(snapshot, ratios, projections, wacc_res, assumptions)
    assert any("WACC" in w and "terminal growth" in w for w in res.warnings)
    assert res.enterprise_value is None
    
    # Case 2: TV dominates EV (> 85%)
    # Let's force a very small WACC or high growth rate close to WACC to trigger TV dominance
    assumptions_dom = build_default_wacc_assumptions(snapshot, ratios, projections)
    wacc_res_dom = calculate_wacc(snapshot, ratios, assumptions_dom)
    
    # High but valid growth rate to make TV very high
    assumptions_dom.terminal_growth_rate = wacc_res_dom.wacc - 0.005
    res_dom = calculate_dcf(snapshot, ratios, projections, wacc_res_dom, assumptions_dom)
    
    if res_dom.enterprise_value is not None:
        tv_share = res_dom.terminal_value_share_of_enterprise_value
        if tv_share and tv_share > 0.85:
            assert any("Terminal value represents more than 85%" in w for w in res_dom.warnings)
            
    # Metadata check
    assert res_dom.model_type == "deterministic_valuation"
    assert len(res_dom.limitations) > 0

def test_facility_structuring_metadata_and_constraints():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    
    resp = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    assert resp.model_type == "candidate_facility_structuring"
    assert resp.dscr_floor == 1.10
    assert resp.ltv_cap == 0.70
    assert resp.max_facility_size > 0
    assert "HIBOR" in resp.indicative_pricing_assumption
    assert resp.provenance == "Deterministic workspace rules engine"
    assert any("Lender review required" in lim for lim in resp.limitations)
    assert any("Terms are indicative" in lim for lim in resp.limitations)

def test_forbidden_wording_absent():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    credit_score = build_credit_scoring_result(analysis)
    pd_estimate = calculate_pd("test", dscr=1.5, debt_ratio=0.4, margin=0.1)
    
    forbidden_terms = [
        "guaranteed approval", "approved loan", "guaranteed funding", 
        "formal underwriting", "bank-grade approval", "certified credit rating"
    ]
    
    structures = [facility_structuring, credit_score, pd_estimate, stress_tests]
    for struct in structures:
        json_str = str(struct.model_dump()).lower()
        for term in forbidden_terms:
            assert term not in json_str, f"Forbidden term '{term}' found in output: {json_str}"
