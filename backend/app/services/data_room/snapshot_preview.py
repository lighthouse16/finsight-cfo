import math
from typing import Callable

from pydantic import ValidationError

from app.models.data_room import (
    DataRoomParsedRecordSet,
    DataRoomSnapshotPreviewInput,
    DataRoomSnapshotPreviewResponse,
)
from app.models.financials import (
    BalanceSheetPeriod,
    CashFlowStatementPeriod,
    CompanyFinancialSnapshot,
    DebtSchedule,
    IncomeStatementPeriod,
    IntegrityCheckResult,
    ReceivablesAging,
)
from app.services.financials.integrity_checks import run_integrity_checks
from app.services.financials.ratio_engine import calculate_ratios

REQUIRED_CORE_RECORD_KEYS = [
    "pl-statement",
    "balance-sheet",
    "cash-flow",
    "debt-schedule",
]

REQUIRED_FIELDS: dict[str, set[str]] = {
    "pl-statement": {
        "revenue",
        "cogs",
        "operating_expenses",
        "ebit",
        "depreciation_amortization",
        "ebitda",
        "interest_expense",
        "ebt",
        "taxes",
        "net_income",
    },
    "balance-sheet": {
        "cash",
        "accounts_receivable",
        "inventory",
        "prepaid",
        "current_assets",
        "ppe_net",
        "total_assets",
        "accounts_payable",
        "accrued",
        "short_term_debt",
        "current_portion_long_term_debt",
        "long_term_debt",
        "lease_liabilities",
        "current_liabilities",
        "total_liabilities",
        "equity",
    },
    "cash-flow": {
        "cfo",
        "capex",
        "debt_issued",
        "debt_repaid",
        "dividends",
        "net_change_cash",
    },
    "debt-schedule": {
        "scheduled_interest",
        "scheduled_principal",
    },
    "receivables-aging": {
        "current_0_30",
        "days_31_60",
        "days_61_90",
        "days_90_plus",
    },
}


StatementFactory = Callable[[dict], object]


STATEMENT_FACTORIES: dict[str, StatementFactory] = {
    "pl-statement": IncomeStatementPeriod,
    "balance-sheet": BalanceSheetPeriod,
    "cash-flow": CashFlowStatementPeriod,
    "debt-schedule": DebtSchedule,
    "receivables-aging": ReceivablesAging,
}


def _safe_record_values(record_set: DataRoomParsedRecordSet) -> dict[str, float]:
    values: dict[str, float] = {}
    for record in record_set.parsedRecords:
        value = record.normalizedValue
        if value is None or not math.isfinite(value):
            continue
        values[record.fieldKey] = float(value)
    return values


def _build_statement(
    record_key: str,
    record_set: DataRoomParsedRecordSet | None,
    warnings: list[str],
):
    if record_set is None:
        return None

    values = _safe_record_values(record_set)
    required = REQUIRED_FIELDS.get(record_key, set())
    missing_fields = sorted(required - set(values.keys()))
    if missing_fields:
        warnings.append(
            f"{record_key} is missing required preview fields: {', '.join(missing_fields)}."
        )
        return None

    try:
        return STATEMENT_FACTORIES[record_key](**values)
    except ValidationError as exc:
        warnings.append(f"{record_key} could not be converted into the financial model: {exc.errors()[0]['msg']}.")
    except (TypeError, ValueError) as exc:
        warnings.append(f"{record_key} could not be converted into the financial model: {exc}.")
    return None


def _failure_check(name: str, message: str) -> IntegrityCheckResult:
    return IntegrityCheckResult(
        check_name=name,
        passed=False,
        message=message,
        details={"preview_only": True},
    )


def build_snapshot_preview(
    preview_input: DataRoomSnapshotPreviewInput,
) -> DataRoomSnapshotPreviewResponse:
    """Build a temporary financial snapshot preview from parsed record sets.

    The result is derived from request payload records only. It does not persist
    data and does not update the demo analysis pipeline.
    """
    company_id = preview_input.companyId or "demo-company"
    company_name = preview_input.companyName or "Harbour & Finch Trading Ltd."
    currency = preview_input.currency or "HKD"
    reporting_period = preview_input.reportingPeriod or "FY2025"
    warnings: list[str] = [
        "Preview only — analysis was not updated and no file or snapshot was stored."
    ]

    record_sets = {record_set.recordKey: record_set for record_set in preview_input.recordSets}
    missing_required_statements = [
        record_key for record_key in REQUIRED_CORE_RECORD_KEYS if record_key not in record_sets
    ]
    if missing_required_statements:
        warnings.append(
            "Core preview is partial because required statements are missing: "
            + ", ".join(missing_required_statements)
            + "."
        )

    for record_set in preview_input.recordSets:
        warnings.extend(record_set.warnings)

    income_statement = _build_statement("pl-statement", record_sets.get("pl-statement"), warnings)
    balance_sheet = _build_statement("balance-sheet", record_sets.get("balance-sheet"), warnings)
    cash_flow_statement = _build_statement("cash-flow", record_sets.get("cash-flow"), warnings)
    debt_schedule = _build_statement("debt-schedule", record_sets.get("debt-schedule"), warnings)
    receivables_aging = _build_statement(
        "receivables-aging",
        record_sets.get("receivables-aging"),
        warnings,
    )

    if "receivables-aging" not in record_sets:
        warnings.append("Receivables aging was not provided; receivables-specific ratio output may be unavailable.")

    if not all([income_statement, balance_sheet, cash_flow_statement, debt_schedule]):
        integrity_checks = [
            _failure_check(
                "Snapshot Preview Completeness",
                "Snapshot preview could not be built because one or more required model inputs are missing.",
            )
        ]
        return DataRoomSnapshotPreviewResponse(
            companyId=company_id,
            companyName=company_name,
            currency=currency,
            reportingPeriod=reporting_period,
            snapshotPreview=None,
            integrityChecks=[check.model_dump(by_alias=True) for check in integrity_checks],
            ratios=None,
            missingRequiredStatements=missing_required_statements,
            warnings=warnings,
        )

    snapshot = CompanyFinancialSnapshot(
        company_id=company_id,
        company_name=company_name,
        reporting_period=reporting_period,
        currency=currency,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        cash_flow_statement=cash_flow_statement,
        debt_schedule=debt_schedule,
        receivables_aging=receivables_aging,
        metadata={
            "source": "data_room_snapshot_preview",
            "preview_only": True,
            "persistent": False,
        },
    )

    integrity_checks = run_integrity_checks(snapshot)
    ratios = calculate_ratios(snapshot)

    return DataRoomSnapshotPreviewResponse(
        companyId=company_id,
        companyName=company_name,
        currency=currency,
        reportingPeriod=reporting_period,
        snapshotPreview=snapshot.model_dump(by_alias=True),
        integrityChecks=[check.model_dump(by_alias=True) for check in integrity_checks],
        ratios=ratios.model_dump(by_alias=True),
        missingRequiredStatements=missing_required_statements,
        warnings=warnings,
    )
