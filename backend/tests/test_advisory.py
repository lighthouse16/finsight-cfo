import math
from fastapi.testclient import TestClient
from app.main import app
from app.models.financials import FinancialAnalysisResponse, FinancialRatios, RatioMetric
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
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


# ---------------------------------------------------------------------------
# AI Provider (AI CFO RAG) Tests
# ---------------------------------------------------------------------------

import math
from unittest.mock import MagicMock, patch, PropertyMock, ANY

from app.services.advisory.ai_provider import (
    get_ai_mode,
    get_advisory_response,
    _get_deterministic_response,
    _build_rag_context,
    _build_sources_from_workspace,
    _call_llm,
    AdvisorySource,
    AdvisoryResponse,
)
from app.core.config import get_settings


# --- get_ai_mode() tests ---

@patch("app.services.advisory.ai_provider.get_settings")
def test_get_ai_mode_deterministic_fallback(mock_get_settings):
    """No keys → deterministic_fallback."""
    settings = MagicMock()
    settings.normalized_ai_mode = "deterministic_fallback"
    mock_get_settings.return_value = settings
    assert get_ai_mode() == "deterministic_fallback"


@patch("app.services.advisory.ai_provider.get_settings")
def test_get_ai_mode_openai(mock_get_settings):
    """OPENAI_API_KEY set → openai."""
    settings = MagicMock()
    settings.normalized_ai_mode = "openai"
    mock_get_settings.return_value = settings
    assert get_ai_mode() == "openai"


@patch("app.services.advisory.ai_provider.get_settings")
def test_get_ai_mode_azure_openai(mock_get_settings):
    """AZURE_OPENAI_API_KEY set → azure_openai."""
    settings = MagicMock()
    settings.normalized_ai_mode = "azure_openai"
    mock_get_settings.return_value = settings
    assert get_ai_mode() == "azure_openai"


# --- _build_rag_context() tests ---

def test_build_rag_context_empty():
    result = _build_rag_context(None)
    assert result == "No workspace data available."

    result2 = _build_rag_context({})
    assert result2 == "No workspace data available."


def test_build_rag_context_with_financial_summary():
    data = {
        "financial_summary": {
            "revenue": 5_000_000,
            "gross_profit": 2_000_000,
            "ebitda": 1_200_000,
            "net_income": 800_000,
            "cash_and_equivalents": 500_000,
            "total_assets": 10_000_000,
            "total_liabilities": 4_000_000,
            "period_label": "FY2024",
            "currency": "HKD",
        },
        "ratios": {
            "current_ratio": 1.8,
            "dscr": 1.25,
        },
    }
    result = _build_rag_context(data)
    assert "=== FINANCIAL SUMMARY ===" in result
    assert "5,000,000" in result
    assert "=== RATIOS ===" in result
    assert "1.25" in result
    assert "FY2024" in result


def test_build_rag_context_with_document_excerpts():
    data = {
        "financial_summary": {"revenue": 100_000},
        "document_excerpts": [
            {"title": "Annual Report 2024", "snippet": "The company achieved strong growth..."},
            {"title": "Audited Financials", "snippet": "Net profit increased by 15%..."},
        ],
    }
    result = _build_rag_context(data)
    assert "=== RELEVANT DOCUMENT EXCERPTS ===" in result
    assert "Annual Report 2024" in result
    assert "The company achieved strong growth..." in result
    assert "Audited Financials" in result


# --- _build_sources_from_workspace() tests ---

def test_build_sources_empty():
    assert _build_sources_from_workspace(None) == []
    assert _build_sources_from_workspace({}) == []


def test_build_sources_with_data():
    data = {
        "financial_summary": {"revenue": 100_000},
        "ratios": {"current_ratio": 1.5},
        "cdi_output": {"score": 75},
        "pd_estimate": {"probability": 0.02},
        "stress_test": {"loss_given_default": 0.4},
        "valuation_summary": {"value": "1M HKD"},
    }
    sources = _build_sources_from_workspace(data)
    assert len(sources) == 6
    titles = [s.title for s in sources]
    assert "Financial Summary" in titles
    assert "Financial Ratios" in titles
    assert "CDI Assessment" in titles
    assert "Probability of Default" in titles
    assert "Stress Test" in titles
    assert "Valuation Summary" in titles


def test_build_sources_with_document_excerpts():
    data = {
        "financial_summary": {"revenue": 100_000},
        "document_excerpts": [
            {"title": "Doc 1", "snippet": "Content 1", "document_id": "doc1"},
            {"title": "Doc 2", "snippet": "Content 2", "document_id": "doc2"},
        ],
    }
    sources = _build_sources_from_workspace(data)
    # 1 financial summary + 2 docs
    assert len(sources) == 3
    doc_titles = [s.title for s in sources if s.title.startswith("Doc")]
    assert len(doc_titles) == 2


# --- _get_deterministic_response() tests ---

def test_deterministic_response_default():
    resp = _get_deterministic_response("What is going on?", None)
    assert resp.ai_mode == "deterministic_fallback"
    assert "Deterministic Fallback" in resp.answer
    assert "LLM provider" not in resp.answer.lower()  # default template doesn't mention provider
    assert len(resp.sources) == 0
    assert len(resp.warnings) > 0
    assert "No LLM provider configured" in resp.warnings[0]


def test_deterministic_response_financial_health():
    ws = {
        "company_name": "TestCorp",
        "financial_summary": {
            "revenue": 1_000_000,
            "revenue_trend": "growing",
            "period_label": "FY2024",
        },
        "ratios": {
            "current_ratio": 1.5,
            "debt_to_equity": 1.2,
        },
    }
    resp = _get_deterministic_response("How is the financial health?", ws)
    assert "Financial Health Assessment" in resp.answer
    assert "TestCorp" in resp.answer
    assert "growing" in resp.answer
    assert "1.5" in resp.answer
    assert len(resp.sources) >= 2  # financial summary + ratios


def test_deterministic_response_funding_readiness():
    ws = {
        "company_name": "TestCorp",
        "financial_summary": {
            "revenue": 5_000_000,
            "ebitda": 1_200_000,
            "cash_and_equivalents": 500_000,
            "total_assets": 10_000_000,
            "total_liabilities": 4_000_000,
        },
        "cdi_output": {"score": 80},
        "pd_estimate": {"probability": 0.015},
        "stress_test": {"loss_given_default": 0.35},
    }
    resp = _get_deterministic_response("What is the funding readiness?", ws)
    assert "Funding Readiness Overview" in resp.answer
    assert "5,000,000" in resp.answer
    assert "CDI Score" in resp.answer
    assert len(resp.sources) >= 3  # financial + cdi + pd + stress


def test_deterministic_response_with_workspace_data():
    ws = {
        "company_name": "Sample Ltd",
        "financial_summary": {
            "revenue": 2_500_000,
            "net_income": 350_000,
            "period_label": "Q3 2024",
        },
    }
    resp = _get_deterministic_response("any question", ws)
    assert "Sample Ltd" in resp.answer
    assert "Q3 2024" in resp.answer


# --- _call_llm() tests ---

@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_success(mock_get_client):
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a test response from the LLM."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system prompt", "user prompt")
    assert answer == "This is a test response from the LLM."
    assert error is None


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_empty_choices(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(choices=[])
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "empty response (no choices)" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_empty_content(mock_get_client):
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "empty response (no content)" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_api_error(mock_get_client):
    from openai import APIError
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIError(
        message="Internal Server Error",
        request=MagicMock(),
        body={"error": "server_error"},
    )
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "LLM API error" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_authentication_error(mock_get_client):
    from openai import AuthenticationError
    mock_client = MagicMock()
    from unittest.mock import MagicMock as _MM
    mock_response = _MM()
    mock_response.status_code = 401
    mock_client.chat.completions.create.side_effect = AuthenticationError(
        message="Invalid API key",
        response=mock_response,
        body={"error": "auth"},
    )
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "LLM authentication error" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_rate_limit_error(mock_get_client):
    from openai import RateLimitError
    mock_client = MagicMock()
    from unittest.mock import MagicMock as _MM
    mock_response = _MM()
    mock_response.status_code = 429
    mock_client.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit exceeded",
        response=mock_response,
        body={"error": "rate_limit"},
    )
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "LLM rate limit" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_connection_error(mock_get_client):
    from openai import APIConnectionError
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIConnectionError(
        message="Connection failed",
        request=MagicMock(),
    )
    mock_get_client.return_value = (mock_client, "gpt-4o-mini")

    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "LLM connection error" in error


def test_call_llm_unknown_mode():
    answer, error = _call_llm("unknown_mode", "system", "user")
    assert answer is None
    assert "Unknown LLM mode" in error


@patch("app.services.advisory.ai_provider._get_openai_client")
def test_call_llm_client_not_available(mock_get_client):
    mock_get_client.return_value = None
    answer, error = _call_llm("openai", "system", "user")
    assert answer is None
    assert "not fully configured" in error


# --- get_advisory_response() tests ---

@patch("app.services.advisory.ai_provider.get_settings")
def test_advisory_response_deterministic_fallback(mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "deterministic_fallback"
    mock_get_settings.return_value = settings

    resp = get_advisory_response("Tell me about this company")
    assert resp.ai_mode == "deterministic_fallback"
    assert "Deterministic Fallback" in resp.answer
    assert len(resp.warnings) == 1
    assert "No LLM provider configured" in resp.warnings[0]


@patch("app.services.advisory.ai_provider.get_settings")
def test_advisory_response_provider_not_configured(mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "provider_not_configured"
    mock_get_settings.return_value = settings

    resp = get_advisory_response("Tell me about this company")
    assert resp.ai_mode == "provider_not_configured"
    assert "not available" in resp.answer.lower()
    assert resp.sources == []


@patch("app.services.advisory.ai_provider.get_settings")
@patch("app.services.advisory.ai_provider._call_llm")
def test_advisory_response_llm_success(mock_call_llm, mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "openai"
    mock_get_settings.return_value = settings
    mock_call_llm.return_value = ("The DSCR is 1.25, which indicates adequate coverage.", None)

    resp = get_advisory_response("What is the DSCR?")
    assert resp.ai_mode == "openai"
    assert "DSCR is 1.25" in resp.answer
    assert resp.warnings == []


@patch("app.services.advisory.ai_provider.get_settings")
@patch("app.services.advisory.ai_provider._call_llm")
def test_advisory_response_llm_success_with_workspace_data(mock_call_llm, mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "openai"
    mock_get_settings.return_value = settings
    mock_call_llm.return_value = ("Analysis based on provided data.", None)

    ws = {
        "company_name": "TestCorp",
        "financial_summary": {"revenue": 1_000_000, "ebitda": 250_000},
        "ratios": {"current_ratio": 1.8, "dscr": 1.25},
    }
    resp = get_advisory_response("Analyze this company", ws)
    assert resp.ai_mode == "openai"
    assert "Analysis" in resp.answer
    # Sources should be built from workspace data
    assert len(resp.sources) >= 2  # financial summary + ratios
    assert resp.warnings == []


@patch("app.services.advisory.ai_provider.get_settings")
@patch("app.services.advisory.ai_provider._call_llm")
def test_advisory_response_llm_failure_falls_back(mock_call_llm, mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "openai"
    mock_get_settings.return_value = settings
    mock_call_llm.return_value = (None, "LLM API error: 500 Internal Server Error")

    resp = get_advisory_response("What is the DSCR?")
    assert resp.ai_mode == "openai"  # mode preserved even on fallback
    assert "Deterministic Fallback" in resp.answer
    assert len(resp.warnings) >= 2  # fallback warning + error details
    assert "API call failed" in resp.warnings[0]
    assert "500 Internal Server Error" in resp.warnings[1]


@patch("app.services.advisory.ai_provider.get_settings")
@patch("app.services.advisory.ai_provider._call_llm")
def test_advisory_response_llm_failure_authentication(mock_call_llm, mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "openai"
    mock_get_settings.return_value = settings
    mock_call_llm.return_value = (None, "LLM authentication error: Invalid API key")

    resp = get_advisory_response("What is the DSCR?")
    assert resp.ai_mode == "openai"
    assert "Deterministic Fallback" in resp.answer
    assert "authentication error" in resp.warnings[1]


@patch("app.services.advisory.ai_provider.get_settings")
@patch("app.services.advisory.ai_provider._call_llm")
def test_advisory_response_azure_openai_success(mock_call_llm, mock_get_settings):
    settings = MagicMock()
    settings.normalized_ai_mode = "azure_openai"
    mock_get_settings.return_value = settings
    mock_call_llm.return_value = ("Azure OpenAI response.", None)

    resp = get_advisory_response("Analyze")
    assert resp.ai_mode == "azure_openai"
    assert "Azure OpenAI response" in resp.answer


# --- End-to-end integration test via HTTP endpoint ---

def test_chat_endpoint_deterministic_fallback():
    """Verify the chat endpoint returns deterministic fallback when no LLM key is set."""
    response = client.post(
        "/api/advisory/chat",
        json={"question": "What is the financial health of this company?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["aiMode"] == "deterministic_fallback"
    assert "Deterministic Fallback" in data["answer"]
    assert len(data["warnings"]) > 0
    # Safety language check
    json_str = str(data).lower()
    for word in ["approved", "rejected", "guaranteed", "underwriting decision"]:
        assert word not in json_str


def test_chat_endpoint_safety_language():
    """Verify the chat endpoint never returns unsafe language."""
    response = client.post(
        "/api/advisory/chat",
        json={"question": "Will my loan be approved?"},
    )
    assert response.status_code == 200
    data = response.json()
    json_str = str(data).lower()
    unsafe_words = [
        "approved", "rejected", "loan approved", "lender approved",
        "approval probability", "predicted default", "automated credit decision",
        "formal underwriting", "guaranteed"
    ]
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in response: {data}"
    analysis = get_demo_analysis()
    
    # 1. Test standard DSCR fail behavior
    assert analysis.ratios.dscr.value is not None
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

def test_demo_stress_tests_endpoint_200():
    response = client.get("/api/advisory/demo-stress-tests")
    assert response.status_code == 200
    data = response.json()
    assert "companyId" in data
    assert "companyName" in data
    assert "baseSummaryBand" in data
    assert "baseRiskScore" in data
    assert "scenarios" in data
    assert len(data["scenarios"]) > 0
    assert "disclaimer" in data
    assert "warnings" in data

def test_stress_tests_safety_language():
    response = client.get("/api/advisory/demo-stress-tests")
    assert response.status_code == 200
    data = response.json()
    
    unsafe_words = [
        "approval", "rejection", "predicted default", "probability of default",
        "underwriting decision", "automated credit decision", "guaranteed failure"
    ]
    
    json_str = str(data).lower()
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in stress testing response: {data}"

def test_stress_tests_calculations():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    
    result = build_demo_stress_tests(analysis, risk_score)
    
    # 1. Rate shock
    rate_scenario = next(s for s in result.scenarios if s.scenario_key == "rate_shock")
    assert rate_scenario.severity == "high"  # DSCR 0.62 -> 0.61 (which is < 1.0)
    interest_cost_impact = next(i for i in rate_scenario.impacts if i.metric == "Additional Annual Interest Cost")
    assert interest_cost_impact.absolute_change == 6500000.0 * 0.015  # total debt proxy 6.5M * 1.5%
    
    # 2. Receivables delay
    ar_scenario = next(s for s in result.scenarios if s.scenario_key == "receivables_delay")
    ar_impact = next(i for i in ar_scenario.impacts if i.metric == "Accounts Receivable (AR) Expansion")
    assert ar_impact.absolute_change == (analysis.snapshot.income_statement.revenue / 365.0) * 15.0
    
    # 3. Input cost squeeze
    cogs_scenario = next(s for s in result.scenarios if s.scenario_key == "input_cost_squeeze")
    ebitda_impact = next(i for i in cogs_scenario.impacts if i.metric == "Operating EBITDA Compression")
    assert ebitda_impact.absolute_change == analysis.snapshot.income_statement.cogs * 0.03
    
    # 4. FX stress (exists because usd_import_cost_percent is in metadata)
    fx_scenario = next(s for s in result.scenarios if s.scenario_key == "fx_stress")
    assert fx_scenario.severity == "high"
    import_cost_impact = next(i for i in fx_scenario.impacts if i.metric == "Procurement Cost Expansion")
    expected_cogs_portion = analysis.snapshot.income_statement.cogs * 0.72
    assert import_cost_impact.absolute_change == expected_cogs_portion * 0.02

def test_stress_tests_fx_stress_unavailable_when_metadata_missing():
    analysis = get_demo_analysis()
    analysis.snapshot.metadata = {}  # remove metadata
    
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    
    result = build_demo_stress_tests(analysis, risk_score)
    fx_scenario = next(s for s in result.scenarios if s.scenario_key == "fx_stress")
    assert fx_scenario.severity == "unavailable"
    assert len(fx_scenario.warnings) > 0

def test_stress_tests_nan_infinity_protection():
    analysis = get_demo_analysis()
    analysis.ratios.dscr.value = float("nan")
    
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    result = build_demo_stress_tests(analysis, risk_score)
    
    assert result.scenarios is not None
    # Ensure serialization doesn't fail
    result_dict = result.model_dump()
    assert result_dict is not None


# Phase 3.4 Facility Structuring Tests

from app.services.advisory.facility_structuring_engine import build_facility_structuring

def test_demo_facility_structures_endpoint_200():
    response = client.get("/api/advisory/demo-facility-structures")
    assert response.status_code == 200
    data = response.json()
    assert "companyId" in data
    assert "companyName" in data
    assert "candidates" in data
    assert len(data["candidates"]) > 0
    assert "preferredCandidateKeys" in data
    assert "disclaimer" in data
    assert "warnings" in data

def test_facility_structuring_candidates():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    
    result = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    
    # Check revolving working capital line
    wc_facility = next(c for c in result.candidates if c.facility_key == "revolving_working_capital")
    assert wc_facility.label == "Revolving Working Capital Line"
    assert wc_facility.estimated_limit > 0
    assert wc_facility.estimated_pricing_bps is not None
    assert wc_facility.estimated_annual_cost == (wc_facility.estimated_limit * wc_facility.estimated_pricing_bps) / 10000.0
    
    # Check receivables finance
    ar_facility = next(c for c in result.candidates if c.facility_key == "receivables_finance")
    assert ar_facility.label == "Receivables Financing Facility"
    assert ar_facility.estimated_limit > 0
    
    # Check trade finance
    trade_facility = next(c for c in result.candidates if c.facility_key == "trade_finance")
    assert trade_facility.label == "Trade Finance & LC Facility"
    assert trade_facility.estimated_limit > 0
    
    # Check term loan
    term_loan = next(c for c in result.candidates if c.facility_key == "term_loan")
    # In demo, DSCR = 0.62 < 1.0, so fit band should be constrained and not in preferred
    assert term_loan.fit_assessment.fit_band == "constrained"
    assert "term_loan" not in result.preferred_candidate_keys
    
    # Check FX hedging context
    fx_hedging = next(c for c in result.candidates if c.facility_key == "fx_hedging")
    assert fx_hedging.estimated_limit is None
    assert fx_hedging.estimated_pricing_bps is None
    assert fx_hedging.estimated_annual_cost is None
    assert fx_hedging.fit_assessment.fit_band == "adequate" # high FX stress in demo

def test_facility_pricing_scales_with_risk_band():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    
    # Elevated risk band
    risk_score_elevated = build_unified_risk_score(analysis, precheck)
    risk_score_elevated.band = "elevated"
    stress_tests = build_demo_stress_tests(analysis, risk_score_elevated)
    
    result_elevated = build_facility_structuring(analysis, precheck, risk_score_elevated, stress_tests)
    wc_elevated = next(c for c in result_elevated.candidates if c.facility_key == "revolving_working_capital")
    
    # High risk band
    risk_score_high = build_unified_risk_score(analysis, precheck)
    risk_score_high.band = "high"
    result_high = build_facility_structuring(analysis, precheck, risk_score_high, stress_tests)
    wc_high = next(c for c in result_high.candidates if c.facility_key == "revolving_working_capital")
    
    assert wc_high.estimated_pricing_bps > wc_elevated.estimated_pricing_bps

def test_facility_hard_gate_fail_reduces_limits():
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    precheck.overall_status = "fail"
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    
    # Mock very large WC gap
    analysis.ratios.working_capital_gap.value = 10_000_000.0
    
    result = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    wc_facility = next(c for c in result.candidates if c.facility_key == "revolving_working_capital")
    
    # Capped at 1.5M because hard gate failed
    assert wc_facility.estimated_limit == 1500000.0

def test_facility_structuring_safety_language():
    response = client.get("/api/advisory/demo-facility-structures")
    assert response.status_code == 200
    data = response.json()
    
    unsafe_words = [
        "approved", "rejected", "lender approved", "final offer",
        "guaranteed rate", "guaranteed limit", "formal underwriting",
        "automated credit decision", "approval probability"
    ]
    
    json_str = str(data).lower()
    for word in unsafe_words:
        assert word not in json_str, f"Unsafe word '{word}' found in response: {data}"

def test_facility_structuring_nan_infinity_protection():
    analysis = get_demo_analysis()
    analysis.ratios.working_capital_gap.value = float("nan")
    
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    result = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    
    assert result.candidates is not None
    # Ensure serialization doesn't fail
    result_dict = result.model_dump()
    assert result_dict is not None

