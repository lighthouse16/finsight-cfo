from typing import Optional, Union, Any
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import ValidationError


from fastapi import Depends
import datetime
from app.routes.workspaces import get_report_repository_dependency, get_workspace_repository_dependency
from app.persistence.interfaces import ReportRepository, WorkspaceRepository
from app.models.advisory import (
    AdvisorReportRequest,
    AdvisorReportResponse,
    AdvisorReadyReportPayload,
    AdvisorReportSection,
    ReportCitation,
)

from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    CreditScoringResult,
    StressTestingResponse,
    FacilityStructuringResponse,
    AdvisoryBlueprintResponse,
    AdvisoryChatRequest,
    AdvisoryChatResponse,
    AdvisoryChatSource,
    StressTestRequest,
)
from app.models.financials import FinancialAnalysisResponse, CompanyFinancialSnapshot
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.credit_scoring_engine import build_credit_scoring_result
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.blueprint_engine import build_advisory_blueprint

router = APIRouter()


def _get_active_or_demo_analysis(
    x_workspace_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> Any:
    """
    Return the active Data Room preview/workspace analysis if available,
    otherwise fall back to the demo company analysis.
    """
    return get_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=workspace_id)


@router.get("/demo-precheck")
def get_demo_precheck(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes the active financial analysis output and returns a structured,
    explainable, context-only eligibility/risk precheck for advisory readiness.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_advisory_precheck_run
        run = execute_advisory_precheck_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    return build_hard_gate_precheck(analysis)


@router.get("/demo-risk-score")
def get_demo_risk_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes the active financial analysis output and advisory precheck to produce a
    unified, context-only risk scoring foundation for advisory readiness.
    """
    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    return build_unified_risk_score(analysis, precheck)


@router.get("/credit-score")
def get_credit_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Produces a finance-first, explainable PD / credit scoring foundation using
    ratios, receivables diagnostics, FCFF/valuation context, and stress overlay.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_credit_score_run
        run = execute_credit_score_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    return build_credit_scoring_result(analysis)


@router.get("/demo-credit-score")
def get_demo_credit_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Backward-compatible demo alias for /credit-score.
    """
    return get_credit_score(x_workspace_id=x_workspace_id, workspace_id=workspace_id)


@router.get("/demo-stress-tests")
def get_demo_stress_tests(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
    shock_bps: int = 150,
):
    """
    Consumes the active financial analysis output and unified risk score to perform
    context-only deterministic scenario stress testing.
    The optional shock_bps parameter controls the rate shock severity (default 150).
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_stress_test_run
        run = execute_stress_test_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    return build_demo_stress_tests(analysis, risk_score, shock_bps=shock_bps)


@router.post("/stress-tests", response_model=StressTestingResponse)
def post_stress_tests(
    request: StressTestRequest,
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
):
    """
    Consumes financial analysis and risk score to run parameterized stress testing.
    Validates bounds:
    - HIBOR shock: 0 to 1000 bps
    - DSO shock: 0 to 180 days
    - Input cost shock: -50% to +100%
    - FX shock: -50% to +50%
    """
    ws_id = request.company_id or x_workspace_id
    analysis = _get_active_or_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=ws_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
        
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    
    return build_demo_stress_tests(
        analysis,
        risk_score,
        shock_bps=request.hibor_shock_bps,
        dso_days_shock=request.dso_days_shock,
        input_cost_shock_pct=request.input_cost_shock_pct,
        fx_shock_pct=request.fx_shock_pct
    )


@router.get("/demo-facility-structures")
def get_demo_facility_structures(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes financial analysis, precheck, risk score, and stress tests to construct
    candidate facility structures with cost and fit estimations.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_facility_structuring_run
        run = execute_facility_structuring_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    return build_facility_structuring(analysis, precheck, risk_score, stress_tests)


@router.get("/demo-blueprint")
def get_demo_blueprint(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
    shock_bps: int = 150,
):
    """
    Consolidates the financial analysis, precheck, risk score, stress tests, and
    facility structuring outputs into a deterministic advisor-ready briefing.
    The optional shock_bps parameter controls the rate shock severity (default 150).
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_advisory_blueprint_run
        run = execute_advisory_blueprint_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score, shock_bps=shock_bps)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    return build_advisory_blueprint(analysis, precheck, risk_score, stress_tests, facility_structuring)


# -------------------------------------------------------------------------
# Phase 3: BOCHK Challenge Endpoints
# -------------------------------------------------------------------------


from fastapi import Depends
import datetime
from app.routes.workspaces import get_report_repository_dependency, get_workspace_repository_dependency
from app.persistence.interfaces import ReportRepository, WorkspaceRepository
from app.models.advisory import (
    AdvisorReportRequest,
    AdvisorReportResponse,
    AdvisorReadyReportPayload,
    AdvisorReportSection,
    ReportCitation,
)

from app.models.advisory import (
    CdiConsentRequest,
    CdiConsentResponse,
    CdiMockResponse,
    FundingBlueprintRequest,
    FundingBlueprintResponse,
    BlueprintSectionText
)
from app.services.advisory.cdi_mock_gateway import get_cdi_mock_data
from app.services.advisory.pd_engine import calculate_pd
from app.services.advisory.loan_structuring_engine import optimize_loan_structure

@router.post("/cdi/mock-consent", response_model=CdiConsentResponse)
def post_cdi_mock_consent(request: CdiConsentRequest):
    """
    Mock consent gateway for CDI alternative data.
    """
    if request.consent_granted:
        return CdiConsentResponse(
            consent_token=f"mock_token_{request.company_id}",
            status="success",
            message="Consent granted. CDI alternative data access authorized."
        )
    return CdiConsentResponse(
        status="denied",
        message="Consent denied."
    )

@router.get("/cdi/mock-data", response_model=CdiMockResponse)
def get_cdi_mock_data_endpoint(
    company_id: str,
    consent_granted: bool = False
):
    """
    Retrieves mock CargoX/logistics alternative data based on consent.
    """
    return get_cdi_mock_data(consent_granted)


@router.post("/funding-blueprint", response_model=FundingBlueprintResponse)
def generate_funding_blueprint(
    request: FundingBlueprintRequest,
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id")
):
    """
    Comprehensive Phase 3 endpoint orchestrating:
    - Hard gate precheck
    - Unified risk score
    - CDI alternative data mock
    - Logistic-style PD estimate
    - BOCHK specific HIBOR stress test
    - Loan structuring optimization
    """
    ws_id = request.company_id or x_workspace_id
    analysis = _get_active_or_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=ws_id)
    
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        raise HTTPException(status_code=400, detail="Insufficient financial data for blueprint.")
        
    # 1. Hard Gate & Risk Score
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    
    # 2. CDI Alternative Data
    cdi_data = get_cdi_mock_data(request.consent_granted)
    
    # 3. PD Estimate
    ratios = analysis.ratios
    dscr = ratios.dscr.value if ratios and ratios.dscr else 1.0
    debt_ratio = ratios.debt_ratio.value if ratios and ratios.debt_ratio else 0.5
    margin = analysis.snapshot.income_statement.ebitda / analysis.snapshot.income_statement.revenue if (analysis.snapshot and analysis.snapshot.income_statement.revenue > 0) else 0.1
    
    pd_estimate = calculate_pd(
        company_id=ws_id or "demo_company",
        dscr=dscr,
        debt_ratio=debt_ratio,
        margin=margin,
        cdi_collateral_hkd=cdi_data.alternative_collateral_hkd if cdi_data else 0.0
    )
    
    # 4. Stress Test
    from app.services.advisory.stress_testing_engine import build_bochk_stress_test
    stress_test = build_bochk_stress_test(analysis, request.scenario_shock_bps)
    
    # 5. Loan Structuring
    loan_structure = optimize_loan_structure(
        company_id=ws_id or "demo_company",
        requested_amount_hkd=request.requested_amount_hkd,
        analysis=analysis,
        cdi_data=cdi_data
    )
    
    # 6. Blueprint Sections (Natural Language Ready)
    sections = [
        BlueprintSectionText(
            title="Executive Summary",
            content=f"Funding request for HKD {request.requested_amount_hkd:,.0f}. Risk Tier: {pd_estimate.tier}."
        ),
        BlueprintSectionText(
            title="Alternative Data (CDI)",
            content=f"Consent granted: {request.consent_granted}. Secured HKD {cdi_data.alternative_collateral_hkd if cdi_data else 0:,.0f} in alternative collateral."
        ),
        BlueprintSectionText(
            title="Stress Test Impact",
            content=f"Under +{request.scenario_shock_bps} bps shock, DSCR moves to {stress_test.stressed_dscr:.2f}x ({stress_test.status.upper()})."
        ),
        BlueprintSectionText(
            title="Proposed Structure",
            content=loan_structure.recommendation_summary
        )
    ]
    
    disclaimers = [
        "This Funding Blueprint is a deterministic advisory response for BOCHK Challenge context.",
        "Relationship manager review required; not formal bank underwriting.",
        "Company records are required for production usage."
    ]
    
    return FundingBlueprintResponse(
        company_id=ws_id or "demo_company",
        hard_gate_summary=precheck.overall_status,
        unified_risk_score=risk_score.score,
        unified_risk_tier=pd_estimate.tier,
        cdi_data=cdi_data,
        pd_estimate=pd_estimate,
        stress_test=stress_test,
        loan_structure=loan_structure,
        blueprint_sections=sections,
        disclaimers=disclaimers
    )


# -------------------------------------------------------------------------
# AI CFO Chat Endpoint
# -------------------------------------------------------------------------

from app.services.advisory.ai_provider import (
    get_advisory_response,
    get_ai_mode,
    AdvisorySource,
)


@router.post("/chat", response_model=AdvisoryChatResponse)
def post_advisory_chat(
    request: AdvisoryChatRequest,
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
):
    """
    AI CFO chat endpoint.

    Accepts a natural-language question and optional workspace context.
    If a workspace_id is provided, the endpoint also retrieves relevant
    document excerpts from the workspace document index (RAG) and includes
    them in the advisory context passed to the AI provider.

    Returns an advisory response whose mode depends on provider configuration:

    - **deterministic_fallback**:  no LLM provider configured — template answer
    - **openai / azure_openai**:   LLM provider configured
    - **provider_not_configured**: no env keys at all
    """
    ws_id = request.workspace_id or x_workspace_id

    # Gather workspace context if available
    workspace_data = None
    if ws_id:
        try:
            analysis = get_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=ws_id)
            if analysis and not (isinstance(analysis, dict) and analysis.get("status") == "insufficient_data"):
                workspace_data = _build_chat_workspace_data(analysis, ws_id)
        except Exception:
            pass  # continue without workspace data

    # --- RAG: retrieve relevant document excerpts ---
    if ws_id:
        try:
            from app.services.data_room.document_index import get_document_index
            index = get_document_index()
            chunks = index.retrieve(
                workspace_id=ws_id,
                query=request.question,
                top_k=5,
            )
            if chunks:
                excerpts = []
                for c in chunks:
                    excerpts.append({
                        "title": c.metadata.get("title", c.source_file or "Untitled"),
                        "snippet": c.text[:500],
                        "document_id": c.document_id,
                        "chunk_index": c.chunk_index,
                        "relevance_score": getattr(c, "relevance_score", None), # Though chunk object from BM25 doesn't currently store score, we can leave it
                    })
                if workspace_data is None:
                    workspace_data = {}
                workspace_data["document_excerpts"] = excerpts
        except Exception:
            pass  # RAG retrieval is best-effort

    resp = get_advisory_response(question=request.question, workspace_data=workspace_data)

    return AdvisoryChatResponse(
        ai_mode=str(resp.ai_mode),
        answer=resp.answer,
        sources=[
            AdvisoryChatSource(
                title=s.title,
                snippet=s.snippet,
                document_id=s.document_id,
                chunk_index=getattr(s, 'chunk_index', None),
                relevance_score=getattr(s, 'relevance_score', None),
            )
            for s in resp.sources
        ],
        disclaimer=resp.disclaimer,
        warnings=resp.warnings,
    )


def _build_chat_workspace_data(
    analysis: Any,
    workspace_id: str,
) -> dict:
    """Flatten a FinancialAnalysisResponse into a dict suitable for RAG context."""
    if isinstance(analysis, dict):
        analysis = FinancialAnalysisResponse.model_validate(analysis)

    data: dict = {}

    snapshot = analysis.snapshot
    if snapshot:
        data["company_name"] = snapshot.company_name
        data["company_id"] = snapshot.company_id
        data["period_label"] = snapshot.reporting_period
        data["currency"] = snapshot.currency

    # Financial summary from income statement
    if snapshot and snapshot.income_statement:
        inc = snapshot.income_statement
        data["financial_summary"] = {
            "revenue": inc.revenue,
            "gross_profit": inc.gross_profit,
            "ebitda": inc.ebitda,
            "net_income": inc.net_income,
            "ebit": inc.ebit,
            "interest_expense": inc.interest_expense,
        }

    # Balance sheet fields
    if snapshot and snapshot.balance_sheet:
        bs = snapshot.balance_sheet
        fs = data.setdefault("financial_summary", {})
        fs["cash_and_equivalents"] = bs.cash
        fs["total_assets"] = bs.total_assets
        fs["total_liabilities"] = bs.total_liabilities
        fs["equity"] = bs.equity
        fs["accounts_receivable"] = bs.accounts_receivable
        fs["current_assets"] = bs.current_assets
        fs["current_liabilities"] = bs.current_liabilities

    # Ratios
    ratios_obj = analysis.ratios
    if ratios_obj:
        data["ratios"] = {
            "current_ratio": getattr(ratios_obj.current_ratio, "value", None),
            "quick_ratio": getattr(ratios_obj.quick_ratio, "value", None),
            "interest_coverage": getattr(ratios_obj.interest_coverage, "value", None),
            "dscr": getattr(ratios_obj.dscr, "value", None),
            "debt_ratio": getattr(ratios_obj.debt_ratio, "value", None),
            "net_debt_to_ebitda": getattr(ratios_obj.net_debt_to_ebitda, "value", None),
            "dso": getattr(ratios_obj.dso, "value", None),
            "working_capital_gap": getattr(ratios_obj.working_capital_gap, "value", None),
        }

    # Valuation from metadata
    metadata = getattr(snapshot, "metadata", None) if snapshot else None
    if metadata and isinstance(metadata, dict):
        val = metadata.get("valuation_summary") or metadata.get("valuation")
        if val:
            data["valuation_summary"] = val if isinstance(val, dict) else {"value": str(val)}

    return data

@router.post("/report", response_model=AdvisorReportResponse)
def compile_advisor_report(
    request: AdvisorReportRequest,
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository_dependency),
    report_repo: ReportRepository = Depends(get_report_repository_dependency),
):
    ws_id = x_workspace_id
    if not ws_id:
        raise HTTPException(status_code=400, detail="Missing workspace_id")
    
    workspace = workspace_repo.get_workspace(ws_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    analysis = get_demo_analysis(x_workspace_id=ws_id, workspace_id=ws_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        raise HTTPException(status_code=400, detail="Insufficient financial data for report.")

    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_test = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_test)
    blueprint = build_advisory_blueprint(analysis, precheck, risk_score, stress_test, facility_structuring)
    
    company_snapshot = {}
    data_quality = {}
    if analysis and analysis.snapshot:
        company_snapshot = {
            "company_name": analysis.snapshot.company_name,
            "reporting_period": analysis.snapshot.reporting_period,
            "currency": analysis.snapshot.currency,
        }
        data_quality = getattr(analysis.snapshot, 'data_quality', {}) or {}
        
    sections = []
    
    # Financial Health
    sections.append(AdvisorReportSection(
        title="Financial Health",
        content=f"Risk Score: {risk_score.score} - {getattr(risk_score, 'band', getattr(risk_score, 'tier', 'N/A'))}\n{precheck.overall_status}"
    ))
    
    # Valuation
    valuation = "N/A"
    if analysis and analysis.snapshot and analysis.snapshot.metadata:
        val = analysis.snapshot.metadata.get("valuation_summary")
        if val:
            valuation = str(val)
    sections.append(AdvisorReportSection(
        title="Valuation Summary",
        content=valuation
    ))
    
    # Market Context
    sections.append(AdvisorReportSection(
        title="Market Context",
        content=f"Stress Test: LGD {getattr(stress_test, 'loss_given_default', getattr(stress_test, 'stressed_dscr', 'N/A'))} under +150 bps HIBOR shock."
    ))

    # Advisory Blueprint
    blueprint_content = []
    for section in getattr(blueprint, 'blueprint_sections', getattr(blueprint, 'sections', [])):
        blueprint_content.append(f"### {section.title}\n{section.content}")
        
    sections.append(AdvisorReportSection(
        title="Advisory Blueprint",
        content="\n\n".join(blueprint_content)
    ))
    
    # AI CFO Chat excerpts if objective is provided
    ai_mode = "deterministic_fallback"
    citations = []
    if request.objective:
        workspace_data = _build_chat_workspace_data(analysis, ws_id)
        try:
            from app.services.data_room.document_index import get_document_index
            index = get_document_index()
            chunks = index.retrieve(
                workspace_id=ws_id,
                query=request.objective,
                top_k=5,
            )
            if chunks:
                excerpts = []
                for c in chunks:
                    excerpts.append({
                        "title": c.metadata.get("title", c.source_file or "Untitled"),
                        "snippet": c.text[:500],
                        "document_id": c.document_id,
                        "chunk_index": c.chunk_index,
                        "relevance_score": getattr(c, "relevance_score", None),
                    })
                workspace_data["document_excerpts"] = excerpts
        except Exception:
            pass
            
        resp = get_advisory_response(question=request.objective, workspace_data=workspace_data)
        ai_mode = str(resp.ai_mode)
        
        for s in resp.sources:
            citations.append(ReportCitation(
                title=s.title,
                snippet=s.snippet or "",
                document_id=s.document_id,
                chunk_index=getattr(s, "chunk_index", None),
                relevance_score=getattr(s, "relevance_score", None),
                source_mode="workspace_derived"
            ))
            
        sections.append(AdvisorReportSection(
            title="AI CFO Notes",
            content=resp.answer,
            citations=citations
        ))
        
    report_title = f"Advisor Ready Report - {company_snapshot.get('company_name', 'Workspace')}"
    if request.objective:
        report_title += f" ({request.objective})"

    payload = AdvisorReadyReportPayload(
        workspace_id=ws_id,
        generated_at=datetime.datetime.utcnow().isoformat() + "Z",
        title=report_title,
        company_snapshot=company_snapshot,
        data_quality=data_quality,
        sections=sections,
        ai_mode=ai_mode,
        limitations=["Information based on provided workspace data; subject to RM review."]
    )
    
    # Save report
    report = None
    try:
        report = report_repo.save_report(
            workspace_id=ws_id,
            report_type="advisor_ready",
            title=report_title,
            report_payload=payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
            metadata={"source": "advisor_report_endpoint"}
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to save report: {e}")
        pass
        
    return AdvisorReportResponse(
        report_id=report["id"] if report else None,
        job_id=None,
        payload=payload
    )
