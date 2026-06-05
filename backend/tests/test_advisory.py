import math
from fastapi.testclient import TestClient
from app.main import app
from app.models.financials import FinancialAnalysisResponse, FinancialRatios, RatioMetric
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.routes.financials import get_demo_analysis

client = TestClient(app)

def test_demo_precheck_endpoint_200():
    response = client.get("/api/advisory/demo-precheck")
    assert response.status_code == 200
    data = response.json()
    assert "companyId" in data
    assert "companyName" in data
    assert "overallStatus" in data
    assert "checks" in data
    assert "passCount" in data
    assert "watchCount" in data
    assert "failCount" in data
    assert "unavailableCount" in data
    assert "constraints" in data
    assert "nextDataNeeded" in data
    assert "disclaimer" in data
    assert "warnings" in data

def test_demo_precheck_overall_status_fail_or_watch_due_to_dscr():
    # In current demo data, DSCR is ~0.62, which is < 1.0.
    # Therefore, the DSCR check must fail, and overallStatus should be "fail".
    response = client.get("/api/advisory/demo-precheck")
    assert response.status_code == 200
    data = response.json()
    assert data["overallStatus"] in ("fail", "watch")
    
    # Verify counts match
    checks = data["checks"]
    pass_count = sum(1 for c in checks if c["status"] == "pass")
    watch_count = sum(1 for c in checks if c["status"] == "watch")
    fail_count = sum(1 for c in checks if c["status"] == "fail")
    unavailable_count = sum(1 for c in checks if c["status"] == "unavailable")
    
    assert data["passCount"] == pass_count
    assert data["watchCount"] == watch_count
    assert data["failCount"] == fail_count
    assert data["unavailableCount"] == unavailable_count

def test_language_safety():
    # Make sure no unsafe language appears in checks, messages, constraints, or disclaimer
    response = client.get("/api/advisory/demo-precheck")
    assert response.status_code == 200
    data = response.json()
    
    unsafe_words = [
        "approved", "rejected", "lender approved", "approval probability",
        "predicted default", "automated credit decision", "formal underwriting",
        "bank verified", "guaranteed"
    ]
    
    # Check all fields recursively or convert entire json to lower case string to inspect
    json_str = str(data).lower()
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in response: {data}"

def test_build_hard_gate_precheck_variations():
    # Run the base demo analysis to get a realistic response
    analysis = get_demo_analysis()
    
    # 1. Test standard DSCR fail behavior
    assert analysis.ratios.dscr.value is not None
    assert analysis.ratios.dscr.value < 1.0
    result = build_hard_gate_precheck(analysis)
    
    dscr_check = next(c for c in result.checks if c.key == "debt_service_coverage")
    assert dscr_check.status == "fail"
    assert dscr_check.severity == "high"
    assert result.overall_status == "fail"
    
    # 2. Test DSCR pass behavior
    analysis_pass = get_demo_analysis()
    analysis_pass.ratios.dscr.value = 1.35
    result_pass = build_hard_gate_precheck(analysis_pass)
    dscr_check_pass = next(c for c in result_pass.checks if c.key == "debt_service_coverage")
    assert dscr_check_pass.status == "pass"
    assert dscr_check_pass.severity == "low"
    
    # 3. Test integrity pass behavior
    # By default, demo integrity checks should all pass
    integrity_check = next(c for c in result.checks if c.key == "data_integrity")
    assert integrity_check.status == "pass"
    
    # 4. Test positive FCFF projection check
    # Demo projections has positive FCFF across all years, so fcff check passes
    fcff_check = next(c for c in result.checks if c.key == "fcff_projection")
    assert fcff_check.status == "pass"
    
    # 5. Test Altman Z safe behavior
    # Demo Altman Z is safe (3.54 > 2.9)
    distress_check = next(c for c in result.checks if c.key == "distress_diagnostic")
    assert distress_check.status == "pass"

def test_missing_and_empty_fields_handling():
    # Make a minimal response structure with all optional or analysis-related fields missing/None
    analysis = get_demo_analysis()
    analysis.integrity_checks = []
    analysis.ratios = None
    analysis.risk_diagnostics = None
    analysis.projections = None
    analysis.valuation = None
    
    result = build_hard_gate_precheck(analysis)
    assert result.overall_status == "unavailable"
    assert result.pass_count == 0
    assert result.watch_count == 0
    assert result.fail_count == 0
    assert result.unavailable_count == 8  # all 8 checks should be unavailable
    
    for check in result.checks:
        assert check.status == "unavailable"
        assert check.severity == "low"

def test_nan_infinity_protection():
    # Set ratios to NaN and Inf to make sure serialization/engine handles them safely
    analysis = get_demo_analysis()
    analysis.ratios.dscr.value = float("nan")
    analysis.ratios.current_ratio.value = float("inf")
    
    result = build_hard_gate_precheck(analysis)
    
    # The build_hard_gate_precheck function should handle float("nan") / float("inf") as unavailable or watch
    dscr_check = next(c for c in result.checks if c.key == "debt_service_coverage")
    assert dscr_check.status in ("unavailable", "watch", "fail")
    
    # Ensure serialization doesn't fail. We can dump to dict / json
    result_dict = result.model_dump()
    assert result_dict is not None

def test_demo_risk_score_endpoint_200():
    response = client.get("/api/advisory/demo-risk-score")
    assert response.status_code == 200
    data = response.json()
    assert "companyId" in data
    assert "companyName" in data
    assert "score" in data
    assert 0 <= data["score"] <= 100
    assert "band" in data
    assert data["band"] in ("low", "moderate", "elevated", "high", "unavailable")
    assert "factors" in data
    assert "strengths" in data
    assert "constraints" in data
    assert "watchItems" in data
    assert "hardGateStatus" in data
    assert "disclaimer" in data
    assert "warnings" in data

def test_risk_score_calm_language():
    response = client.get("/api/advisory/demo-risk-score")
    assert response.status_code == 200
    data = response.json()
    
    unsafe_words = [
        "approval", "rejection", "lender approved", "predicted default",
        "probability of default", "underwriting decision", "automated credit decision",
        "pd", "default probability", "approval score", "credit decision"
    ]
    
    json_str = str(data).lower()
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in risk score response: {data}"

def test_build_unified_risk_score_impact():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    
    # Base score verification
    result = build_unified_risk_score(analysis, precheck)
    assert 0 <= result.score <= 100
    assert result.band == "high"  # due to fail in precheck and constrained DSCR
    
    # Verify that a passing precheck and strong DSCR raises the score
    analysis_strong = get_demo_analysis()
    analysis_strong.ratios.dscr.value = 1.6  # strong DSCR
    # Let's mock a passing precheck
    precheck_pass = build_hard_gate_precheck(analysis_strong)
    precheck_pass.overall_status = "pass"
    
    result_strong = build_unified_risk_score(analysis_strong, precheck_pass)
    # The score should be much higher than 28
    assert result_strong.score > result.score
    assert result_strong.band in ("low", "moderate", "elevated")

def test_risk_score_missing_inputs_fallback():
    # Make a minimal response structure with missing summary and precheck
    analysis = get_demo_analysis()
    analysis.summary = None
    
    precheck = build_hard_gate_precheck(analysis)
    
    result = build_unified_risk_score(analysis, precheck)
    assert result.band == "unavailable"
    for factor in result.factors:
        assert factor.score_impact < 0 or factor.score_impact == 0
        assert math.isfinite(factor.score_impact)

def test_risk_score_nan_infinity_protection():
    analysis = get_demo_analysis()
    analysis.ratios.dscr.value = float("nan")
    analysis.ratios.current_ratio.value = float("inf")
    
    precheck = build_hard_gate_precheck(analysis)
    result = build_unified_risk_score(analysis, precheck)
    
    assert math.isfinite(result.score)
    # Ensure serialization doesn't fail
    result_dict = result.model_dump()
    assert result_dict is not None
