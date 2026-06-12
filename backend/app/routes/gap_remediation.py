from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter

router = APIRouter()


def _logistic(z_score: float) -> float:
    return 1 / (1 + math.exp(-z_score))


@router.get("/summary")
def get_gap_remediation_summary() -> dict[str, Any]:
    return {
        "status": "demo_gap_closure_ready",
        "coverage": [
            "OCR/PDF/NER ingestion blueprint endpoint",
            "TimescaleDB/Redis/Celery target architecture endpoint",
            "Macro prediction scenario endpoint",
            "Logistic PD demo endpoint",
            "Facility optimization demo endpoint",
            "Wired provider credentials for HKMA, CME, Apify, SQX/Cbonds, and CDI gateways.",
        ],
        "remainingProductionWork": [
            "Replace mocked OCR with deployed OCR/PDF parser workers.",
            "Train and validate calibrated PD model with real bureau/CDI performance data.",
            "Replace heuristic optimizer with PuLP or scipy linprog after final constraints are approved.",
        ],
    }


@router.get("/ingestion-pipeline")
def get_ingestion_pipeline_gap_closure() -> dict[str, Any]:
    return {
        "gap": "OCR/PDF/NER ingestion",
        "demoStatus": "closed_by_design_and_contract",
        "productionStatus": "requires_worker_implementation",
        "targetPipeline": [
            {
                "step": 0,
                "name": "Document intake",
                "input": ["pdf", "xlsx", "csv", "docx"],
                "output": "raw_file_metadata + checksum + consent/audit context",
            },
            {
                "step": 1,
                "name": "OCR/PDF extraction",
                "tooling": ["pdfplumber", "pytesseract_or_cloud_ocr", "openpyxl"],
                "output": "raw tables + page spans + confidence score",
            },
            {
                "step": 2,
                "name": "NER and canonical mapping",
                "tooling": ["rule_dictionary", "layout_aware_line_item_mapper", "industry_code_classifier"],
                "output": "canonical P&L, balance sheet, cash-flow, debt schedule",
            },
            {
                "step": 3,
                "name": "Integrity validation",
                "checks": ["assets = liabilities + equity", "cash reconciliation", "EBITDA bridge"],
                "output": "CompanyFinancialSnapshot + IntegrityCheckResult[]",
            },
        ],
        "currentRepoPath": [
            "/api/data-room/demo-parse-preview",
            "/api/data-room/demo-snapshot-preview",
            "/api/financials/preview-analysis",
        ],
        "acceptanceCriteria": [
            "Every parsed snapshot has source filename, confidence, and warnings.",
            "Low-confidence fields remain review-required instead of silently scoring.",
            "Canonical snapshot feeds Stage 1 integrity checks before ratios or valuation.",
        ],
    }


@router.get("/target-architecture")
def get_target_architecture_gap_closure() -> dict[str, Any]:
    return {
        "gap": "TimescaleDB, Redis, Celery production architecture",
        "demoStatus": "closed_by_architecture_contract",
        "productionStatus": "requires_infrastructure_provisioning",
        "components": {
            "postgresTimescale": {
                "purpose": "Persist company workspaces, uploaded records, market time series, scenario outputs, and audit trails.",
                "tables": [
                    "company_workspace",
                    "financial_snapshot",
                    "market_rate_timeseries",
                    "funding_channel_score",
                    "cdi_consent_audit",
                    "workflow_run",
                ],
            },
            "redis": {
                "purpose": "Cache market provider responses and short-lived workflow/session context.",
                "keys": [
                    "market:rates-liquidity:latest",
                    "market:source-status:latest",
                    "workflow:{company_id}:latest",
                ],
            },
            "celery": {
                "purpose": "Run scheduled market refresh, source status checks, and slow document parsing jobs.",
                "tasks": [
                    "refresh_hkma_rates_hourly",
                    "refresh_fedwatch_daily",
                    "parse_uploaded_financial_document",
                    "recalculate_workspace_workflow",
                ],
            },
        },
        "acceptanceCriteria": [
            "Market Watch can refresh asynchronously without blocking API requests.",
            "Workflow outputs are persisted with timestamp and source status.",
            "Every consent/CDI pull has audit trail and expiry metadata.",
        ],
    }


@router.get("/macro-prediction")
def get_macro_prediction_gap_closure() -> dict[str, Any]:
    base_hibor = 0.043
    fed_cut_probability = 0.58
    scenarios = [
        {
            "scenario": "base_case",
            "projectedHibor3m": round(base_hibor, 4),
            "fundingCostDirection": "stable",
            "rationale": "HIBOR remains near current funding reference and Fed cut probability is balanced.",
        },
        {
            "scenario": "downside_liquidity_squeeze",
            "projectedHibor3m": round(base_hibor + 0.015, 4),
            "fundingCostDirection": "up",
            "rationale": "Stress overlay applies +150 bps HIBOR shock from challenge workflow.",
        },
        {
            "scenario": "easing_case",
            "projectedHibor3m": round(base_hibor - 0.0075, 4),
            "fundingCostDirection": "down",
            "rationale": "Higher Fed cut probability lowers expected HKD funding pressure in the demo model.",
        },
    ]
    return {
        "gap": "Prophet/LSTM macro prediction",
        "demoStatus": "closed_by_scenario_model",
        "productionStatus": "requires_provider_history_and_model_training",
        "modelContract": {
            "inputs": ["HKMA HIBOR", "CME FedWatch", "IPO pipeline", "bond yield spreads", "sector stress flags"],
            "methods": ["Prophet_baseline", "LSTM_optional", "scenario_overlay"],
            "outputs": ["projectedHibor3m", "fundingCostDirection", "redFlags", "confidenceBand"],
        },
        "fedCutProbability": fed_cut_probability,
        "scenarios": scenarios,
        "acceptanceCriteria": [
            "Prediction output feeds stress testing and funding channel ranking.",
            "Model response includes provider status and fallback mode.",
            "Red flags explain whether funding should be accelerated, delayed, or hedged.",
        ],
    }


@router.get("/logistic-pd")
def get_logistic_pd_gap_closure(score: int = 72, dscr: float = 1.32, bureau_band: str = "clear") -> dict[str, Any]:
    bureau_adjustment = {
        "clear": -0.35,
        "watch": 0.25,
        "adverse": 0.85,
    }.get(bureau_band, 0.25)
    z_score = -1.2 - 0.045 * (score - 60) - 0.55 * (dscr - 1.0) + bureau_adjustment
    pd = _logistic(z_score)
    if pd < 0.02:
        tier = "low"
    elif pd < 0.05:
        tier = "moderate"
    elif pd < 0.10:
        tier = "elevated"
    else:
        tier = "high"
    return {
        "gap": "Calibrated logistic PD",
        "demoStatus": "closed_by_formula_contract",
        "productionStatus": "requires_training_data_calibration_and_validation",
        "formula": "P(Default)=1/(1+e^-Z)",
        "inputs": {
            "score": score,
            "dscr": dscr,
            "bureauBand": bureau_band,
        },
        "zScore": round(z_score, 4),
        "pd": round(pd, 4),
        "pdPercent": round(pd * 100, 2),
        "tier": tier,
        "calibrationNotes": [
            "Coefficients are demonstrative, not regulatory calibrated.",
            "Production model must be trained with observed defaults and bureau/CDI labels.",
            "Reject-inference, bias monitoring, and approval governance are required before bank use.",
        ],
    }


@router.get("/facility-optimization")
def get_facility_optimization_gap_closure(
    requested_amount: float = 3_000_000,
    eligible_invoices: float = 1_715_000,
    dscr: float = 1.32,
) -> dict[str, Any]:
    max_receivables_advance = eligible_invoices * 0.70
    sfgs_core = min(requested_amount * 0.55, 1_650_000)
    trade_finance = min(max_receivables_advance, requested_amount * 0.35)
    liquidity_buffer = max(0.0, requested_amount - sfgs_core - trade_finance)
    feasible = dscr >= 1.25 and liquidity_buffer <= requested_amount * 0.20
    weighted_cost_bps = (
        sfgs_core * 330 + trade_finance * 280 + liquidity_buffer * 420
    ) / max(requested_amount, 1)
    return {
        "gap": "PuLP / linprog facility optimization",
        "demoStatus": "closed_by_heuristic_optimizer_contract",
        "productionStatus": "replace_with_pulp_or_scipy_linprog_after_constraints_finalized",
        "objective": "Minimize weighted funding cost subject to LTV, DSCR, invoice advance, and liquidity-buffer limits.",
        "constraints": {
            "receivablesAdvanceRateMax": 0.70,
            "minimumDscr": 1.25,
            "liquidityBufferMaxShare": 0.20,
        },
        "inputs": {
            "requestedAmount": requested_amount,
            "eligibleInvoices": eligible_invoices,
            "dscr": dscr,
        },
        "recommendedStack": [
            {
                "facility": "Core SFGS / term facility context",
                "amount": round(sfgs_core, 2),
                "pricingBps": 330,
            },
            {
                "facility": "Receivables / trade finance",
                "amount": round(trade_finance, 2),
                "pricingBps": 280,
            },
            {
                "facility": "Liquidity buffer / overdraft context",
                "amount": round(liquidity_buffer, 2),
                "pricingBps": 420,
            },
        ],
        "weightedCostBps": round(weighted_cost_bps, 1),
        "feasible": feasible,
        "warnings": [] if feasible else [
            "Recommended stack breaches DSCR or buffer constraints under current demo inputs."
        ],
    }
