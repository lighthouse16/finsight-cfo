from typing import List
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    StressTestingResponse,
    FacilityStructuringResponse,
    AdvisoryBriefSection,
    AdvisoryBlueprintAction,
    AdvisoryBlueprintResponse,
    BlueprintKeySections,
)


def build_advisory_blueprint(
    analysis: FinancialAnalysisResponse,
    precheck: HardGatePrecheckResult,
    risk_score: UnifiedRiskScoreResult,
    stress_tests: StressTestingResponse,
    facility_structuring: FacilityStructuringResponse,
) -> AdvisoryBlueprintResponse:
    """
    Consolidates existing Phase 1 and Phase 3 outputs into a deterministic,
    advisor-ready briefing contract.

    This function does not recalculate ratios, create a new score, call an LLM,
    or determine credit outcomes. It only organizes context already produced by
    the financial summary, hard-gate precheck, risk score, stress tests, and
    facility structuring engines.
    """
    snapshot = analysis.snapshot
    summary = analysis.summary

    disclaimer = (
        "This advisory blueprint is deterministic, context-only, and assumptions-based. "
        "It consolidates demo financial analysis, risk context, stress sensitivities, "
        "and candidate structures for briefing preparation. It is not a credit decision, "
        "loan commitment, or calibrated default model. Company records are required for production."
    )

    company_id = snapshot.company_id if snapshot else "demo_company"
    company_name = snapshot.company_name if snapshot else "Demo Company"

    blueprint_status = "unavailable_context"
    if summary and precheck and risk_score:
        if precheck.overall_status == "fail" or risk_score.band == "high" or summary.overall_band == "constrained":
            blueprint_status = "constrained_context"
        elif precheck.overall_status == "watch" or risk_score.band == "elevated" or summary.overall_band == "watch":
            blueprint_status = "watch_context"
        else:
            blueprint_status = "ready_context"

    def _dedup(items: List[str]) -> List[str]:
        seen = set()
        return [item for item in items if item and not (item in seen or seen.add(item))]

    def _top_stress_takeaways() -> List[str]:
        severity_rank = {"high": 4, "elevated": 3, "moderate": 2, "low": 1, "unavailable": 0}
        scenarios = sorted(
            stress_tests.scenarios if stress_tests else [],
            key=lambda scenario: severity_rank.get(scenario.severity, 0),
            reverse=True,
        )
        return [f"{scenario.label}: {scenario.key_takeaway}" for scenario in scenarios[:3]]

    preferred_candidates = []
    constrained_candidates = []
    candidate_required_data: List[str] = []
    if facility_structuring:
        for candidate in facility_structuring.candidates:
            if candidate.facility_key in facility_structuring.preferred_candidate_keys:
                preferred_candidates.append(
                    f"{candidate.label} ({candidate.fit_assessment.fit_band} fit, est. limit HKD "
                    f"{candidate.estimated_limit:,.0f})" if candidate.estimated_limit is not None
                    else f"{candidate.label} ({candidate.fit_assessment.fit_band} fit)"
                )
            if candidate.fit_assessment.fit_band in ("watch", "constrained", "unavailable"):
                constrained_candidates.append(
                    f"{candidate.label}: {candidate.fit_assessment.rationale}"
                )
            candidate_required_data.extend(candidate.fit_assessment.required_data)

    financial_signals = []
    if summary:
        financial_signals = [
            f"{signal.label}: {signal.band} — {signal.evidence}"
            for signal in summary.key_signals[:5]
        ]

    financial_posture = AdvisoryBriefSection(
        section_key="financial_posture",
        title="Financial posture context",
        summary=(
            f"Financial summary band is {summary.overall_band}; debt-service is "
            f"{summary.debt_service_band}, liquidity is {summary.liquidity_band}, "
            f"and leverage is {summary.leverage_band}."
            if summary else "Financial analysis summary is unavailable."
        ),
        signals=financial_signals,
        constraints=summary.constraints if summary else [],
        next_data_needed=summary.next_data_needed if summary else ["Complete financial analysis summary"],
        source_refs=["financial_analysis.summary"],
        warnings=summary.warnings if summary else [],
    )

    advisory_readiness = AdvisoryBriefSection(
        section_key="advisory_readiness",
        title="Advisory readiness context",
        summary=(
            f"Unified advisory risk score is {risk_score.score}/100 with {risk_score.band} band; "
            f"hard-gate precheck status is {precheck.overall_status}."
            if risk_score and precheck else "Risk context is unavailable."
        ),
        signals=[factor.message for factor in risk_score.factors[:5]] if risk_score else [],
        constraints=_dedup((precheck.constraints if precheck else []) + (risk_score.constraints if risk_score else [])),
        next_data_needed=precheck.next_data_needed if precheck else ["Complete advisory precheck"],
        source_refs=["advisory_precheck", "unified_risk_score"],
        warnings=_dedup((precheck.warnings if precheck else []) + (risk_score.warnings if risk_score else [])),
    )

    stress_context = AdvisoryBriefSection(
        section_key="stress_context",
        title="Stress sensitivity context",
        summary=(
            "Deterministic stress tests highlight sensitivity to rate, receivables, input cost, "
            "and FX scenarios."
            if stress_tests else "Stress testing context is unavailable."
        ),
        signals=_top_stress_takeaways(),
        constraints=[
            f"{scenario.label} severity is {scenario.severity}."
            for scenario in (stress_tests.scenarios if stress_tests else [])
            if scenario.severity in ("high", "elevated")
        ],
        next_data_needed=["Scenario calibration assumptions", "Company cash flow records"],
        source_refs=["stress_testing.scenarios"],
        warnings=stress_tests.warnings if stress_tests else [],
    )

    candidate_structures = AdvisoryBriefSection(
        section_key="candidate_structures",
        title="Facility structuring context",
        summary=(
            f"{len(facility_structuring.candidates)} candidate structures were generated; "
            f"preferred context keys are {', '.join(facility_structuring.preferred_candidate_keys) or 'none'}."
            if facility_structuring else "Facility structuring context is unavailable."
        ),
        signals=preferred_candidates,
        constraints=_dedup((facility_structuring.constraints if facility_structuring else []) + constrained_candidates[:3]),
        next_data_needed=_dedup((facility_structuring.next_data_needed if facility_structuring else []) + candidate_required_data)[:8],
        source_refs=["facility_structuring.candidates"],
        warnings=facility_structuring.warnings if facility_structuring else [],
    )

    required_data = _dedup(
        financial_posture.next_data_needed + advisory_readiness.next_data_needed + candidate_structures.next_data_needed
    )[:8]

    data_readiness = AdvisoryBriefSection(
        section_key="data_readiness",
        title="Data readiness context",
        summary=(
            f"Advisory blueprint is context-only. {len(required_data)} next data items are required "
            "to transition from demo context to production advisory."
        ),
        signals=[],
        constraints=[],
        next_data_needed=required_data,
        source_refs=[
            "financial_analysis.summary",
            "advisory_precheck",
            "facility_structuring",
        ],
        warnings=[],
    )

    actions: List[AdvisoryBlueprintAction] = [
        AdvisoryBlueprintAction(
            action_key="collect_required_records",
            label="Collect production records for advisor review",
            priority="high",
            rationale="The briefing remains demo and context-only until company records are reconciled.",
            owner_hint="Relationship manager / finance team",
            required_data=required_data,
            related_candidate_keys=facility_structuring.preferred_candidate_keys if facility_structuring else [],
        ),
        AdvisoryBlueprintAction(
            action_key="review_debt_service_headroom",
            label="Review debt-service headroom before sizing new debt",
            priority="high" if blueprint_status == "constrained_context" else "medium",
            rationale="Debt-service coverage is a primary constraint in the current advisory context.",
            owner_hint="Advisor / credit product specialist",
            required_data=["Debt schedule", "Monthly cash flow forecast"],
            related_candidate_keys=["revolving_working_capital", "term_loan"],
        ),
        AdvisoryBlueprintAction(
            action_key="compare_working_capital_options",
            label="Compare working-capital and receivables-based structures",
            priority="medium",
            rationale="Candidate structures indicate working-capital and receivables facilities are the most relevant contexts to compare.",
            owner_hint="Advisor / treasury specialist",
            required_data=["Receivables aging ledger", "Bank statement summaries"],
            related_candidate_keys=facility_structuring.preferred_candidate_keys if facility_structuring else [],
        ),
    ]

    warnings = _dedup(
        (analysis.warnings if analysis else [])
        + financial_posture.warnings
        + advisory_readiness.warnings
        + stress_context.warnings
        + candidate_structures.warnings
        + data_readiness.warnings
    )

    executive_brief = (
        f"{company_name} has a {blueprint_status.replace('_', ' ')} advisory profile. "
        f"The financial summary is {summary.overall_band if summary else 'unavailable'}, "
        f"the advisory risk band is {risk_score.band if risk_score else 'unavailable'}, "
        f"and the precheck status is {precheck.overall_status if precheck else 'unavailable'}. "
        "Use this briefing to focus advisor discussion on constraints, sensitivities, "
        "candidate structures, and records needed for production review."
    )

    key_sections = BlueprintKeySections(
        financial_posture=financial_posture,
        advisory_readiness=advisory_readiness,
        stress_context=stress_context,
        candidate_structures=candidate_structures,
        data_readiness=data_readiness,
    )

    return AdvisoryBlueprintResponse(
        company_id=company_id,
        company_name=company_name,
        blueprint_status=blueprint_status,
        executive_brief=executive_brief,
        key_sections=key_sections,
        recommended_actions=actions,
        source_outputs=[
            "financial_analysis.summary",
            "hard_gate_precheck",
            "unified_risk_score",
            "stress_testing",
            "facility_structuring",
        ],
        disclaimer=disclaimer,
        warnings=warnings,
    )
