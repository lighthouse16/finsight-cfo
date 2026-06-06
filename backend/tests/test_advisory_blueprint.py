from fastapi.testclient import TestClient
from app.main import app
from app.services.advisory.blueprint_engine import build_advisory_blueprint
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.routes.financials import get_demo_analysis

client = TestClient(app)


def test_demo_blueprint_endpoint_200():
    response = client.get("/api/advisory/demo-blueprint")
    assert response.status_code == 200
    data = response.json()

    assert "companyId" in data
    assert "companyName" in data
    assert data["blueprintStatus"] in (
        "ready_context",
        "watch_context",
        "constrained_context",
        "unavailable_context",
    )
    assert "executiveBrief" in data
    assert "keySections" in data
    assert "recommendedActions" in data
    assert "sourceOutputs" in data
    assert "disclaimer" in data
    assert "warnings" in data


def test_blueprint_consolidates_existing_outputs():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)

    result = build_advisory_blueprint(
        analysis,
        precheck,
        risk_score,
        stress_tests,
        facility_structuring,
    )

    assert result.company_id == analysis.snapshot.company_id
    assert result.company_name == analysis.snapshot.company_name
    assert result.blueprint_status == "constrained_context"
    assert analysis.summary.overall_band in result.executive_brief
    assert risk_score.band in result.executive_brief
    assert precheck.overall_status in result.executive_brief
    assert "financial_analysis.summary" in result.source_outputs
    assert "unified_risk_score" in result.source_outputs
    assert "stress_testing" in result.source_outputs
    assert "facility_structuring" in result.source_outputs


def test_blueprint_sections_include_context_and_actions():
    data = client.get("/api/advisory/demo-blueprint").json()
    key_sec = data["keySections"]

    assert key_sec["financialPosture"]["sectionKey"] == "financial_posture"
    assert len(key_sec["financialPosture"]["signals"]) > 0
    assert key_sec["advisoryReadiness"]["sectionKey"] == "advisory_readiness"
    assert len(key_sec["advisoryReadiness"]["constraints"]) > 0
    assert key_sec["stressContext"]["sectionKey"] == "stress_context"
    assert len(key_sec["stressContext"]["signals"]) > 0
    assert key_sec["candidateStructures"]["sectionKey"] == "candidate_structures"
    assert "receivables_finance" in key_sec["candidateStructures"]["summary"]
    assert key_sec["dataReadiness"]["sectionKey"] == "data_readiness"
    assert len(key_sec["dataReadiness"]["nextDataNeeded"]) > 0

    action_keys = {action["actionKey"] for action in data["recommendedActions"]}
    assert "collect_required_records" in action_keys
    assert "review_debt_service_headroom" in action_keys
    assert "compare_working_capital_options" in action_keys


def test_blueprint_safety_language():
    response = client.get("/api/advisory/demo-blueprint")
    assert response.status_code == 200
    data = response.json()

    unsafe_words = [
        "approved", "rejected", "lender approved", "final offer",
        "guaranteed rate", "guaranteed limit", "approval probability",
        "predicted default", "formal underwriting", "automated credit decision"
    ]

    json_str = str(data).lower()
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in response: {data}"


def test_blueprint_missing_summary_fallback():
    analysis = get_demo_analysis()
    analysis.summary = None
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)

    result = build_advisory_blueprint(
        analysis,
        precheck,
        risk_score,
        stress_tests,
        facility_structuring,
    )

    assert result.blueprint_status == "unavailable_context"
    assert result.key_sections.financial_posture.summary == "Financial analysis summary is unavailable."
    result_dict = result.model_dump()
    assert result_dict is not None
