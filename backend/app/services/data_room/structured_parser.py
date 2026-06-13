import csv
import io
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import UploadFile

from app.models.data_room import DataRoomParsePreview, ParsedFinancialRecord

try:  # Optional dependency: only enable XLSX parsing if available.
    import openpyxl  # type: ignore
except ImportError:  # pragma: no cover - depends on environment
    openpyxl = None

PARSEABLE_RECORD_KEYS = {
    "pl-statement": "profit_and_loss",
    "balance-sheet": "balance_sheet",
    "cash-flow": "cash_flow",
    "debt-schedule": "debt_schedule",
    "receivables-aging": "receivables_aging",
}

EXPECTED_FIELDS: dict[str, set[str]] = {
    "pl-statement": {
        "revenue",
        "cogs",
        "gross_profit",
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
        "retained_earnings",
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
        "monthly_debt_service",
    },
    "receivables-aging": {
        "current_0_30",
        "days_31_60",
        "days_61_90",
        "days_90_plus",
    },
}

FIELD_ALIASES: dict[str, str] = {
    "sales": "revenue",
    "turnover": "revenue",
    "cost_of_goods_sold": "cogs",
    "cost_of_sales": "cogs",
    "opex": "operating_expenses",
    "operating_expense": "operating_expenses",
    "operating_profit": "ebit",
    "operating_income": "ebit",
    "ebit_margin": "ebit_margin",
    "gross_margin": "gross_profit",
    "gross_earnings": "gross_profit",
    "pbt": "ebt",
    "profit_before_tax": "ebt",
    "earnings_before_tax": "ebt",
    "income_tax": "taxes",
    "tax_expense": "taxes",
    "finance_costs": "interest_expense",
    "interest_paid": "interest_expense",
    "d_a": "depreciation_amortization",
    "da": "depreciation_amortization",
    "depreciation": "depreciation_amortization",
    "amortization": "depreciation_amortization",
    "depreciation_and_amortization": "depreciation_amortization",
    "interest": "interest_expense",
    "tax": "taxes",
    "profit_after_tax": "net_income",
    "net_profit": "net_income",
    "net_earnings": "net_income",
    "profit_for_the_year": "net_income",
    "profit_loss_for_the_year": "net_income",
    "cash_and_cash_equivalents": "cash",
    "ar": "accounts_receivable",
    "trade_receivables": "accounts_receivable",
    "stock": "inventory",
    "fixed_assets": "ppe_net",
    "ap": "accounts_payable",
    "trade_payables": "accounts_payable",
    "short_term_borrowings": "short_term_debt",
    "current_portion_of_long_term_debt": "current_portion_long_term_debt",
    "ltd": "long_term_debt",
    "shareholders_equity": "equity",
    "total_current_assets": "current_assets",
    "total_current_liabilities": "current_liabilities",
    "accumulated_losses": "retained_earnings",
    "retained_profit": "retained_earnings",
    "lease_liability": "lease_liabilities",
    "finance_lease_obligations": "lease_liabilities",
    "operating_cash_flow": "cfo",
    "cash_flow_from_operations": "cfo",
    "capital_expenditure": "capex",
    "capital_expenditures": "capex",
    "purchase_of_ppe": "capex",
    "additions_to_ppe": "capex",
    "principal_repaid": "debt_repaid",
    "dividends_paid": "dividends",
    "distributions": "dividends",
    "0_30": "current_0_30",
    "0_30_days": "current_0_30",
    "current": "current_0_30",
    "31_60": "days_31_60",
    "31_60_days": "days_31_60",
    "61_90": "days_61_90",
    "61_90_days": "days_61_90",
    "90_plus": "days_90_plus",
    "90": "days_90_plus",
    "over_90": "days_90_plus",
    "90_days_plus": "days_90_plus",
}


def normalize_field_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[%$€£¥,()]", " ", text)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return FIELD_ALIASES.get(text, text)


def normalize_numeric_value(value: Any) -> tuple[float | None, list[str]]:
    warnings: list[str] = []
    if value is None:
        return None, ["Value is blank."]

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None, ["Value is blank."]
        negative = text.startswith("(") and text.endswith(")")
        text = text.strip("()")
        text = re.sub(r"[,$€£¥\s]", "", text)
        try:
            number = float(Decimal(text))
        except (InvalidOperation, ValueError):
            return None, ["Value could not be normalized as a number."]
        if negative:
            number = -number

    if not math.isfinite(number):
        return None, ["Value is not a finite number."]
    return number, warnings


def _records_from_rows(record_key: str, rows: list[list[Any]]) -> DataRoomParsePreview:
    expected = EXPECTED_FIELDS[record_key]
    parsed: list[ParsedFinancialRecord] = []
    unsupported: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    data_rows = [row for row in rows if any(str(cell or "").strip() for cell in row)]
    if not data_rows:
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(expected),
            unsupportedFields=[],
            rowCount=0,
            warnings=["No readable rows found. Analysis was not updated."],
        )

    header = [normalize_field_name(cell) for cell in data_rows[0]]
    metric_idx = 0
    value_idx = 1 if len(header) > 1 else -1
    for candidate in ("metric", "account", "field", "field_key", "line_item"):
        if candidate in header:
            metric_idx = header.index(candidate)
            break
    for candidate in ("value", "amount", "balance"):
        if candidate in header:
            value_idx = header.index(candidate)
            break

    if value_idx < 0:
        warnings.append("No value column found. Expected a simple metric,value or account,value shape.")
        body_rows: list[list[Any]] = []
    else:
        body_rows = data_rows[1:] if len(data_rows) > 1 else []

    for row in body_rows:
        if metric_idx >= len(row) or value_idx >= len(row):
            warnings.append("Skipped a row with missing metric or value cells.")
            continue
        raw_field = row[metric_idx]
        field_key = normalize_field_name(raw_field)
        if not field_key:
            warnings.append("Skipped a row with a blank field name.")
            continue
        if field_key not in expected:
            unsupported.append(field_key)
            continue
        raw_value = row[value_idx]
        normalized, value_warnings = normalize_numeric_value(raw_value)
        raw_value_text = "" if raw_value is None else str(raw_value)
        if normalized is None and raw_value_text.strip().lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
            raw_value_text = "non-finite"
        seen.add(field_key)
        parsed.append(
            ParsedFinancialRecord(
                fieldKey=field_key,
                label=str(raw_field or field_key).strip() or field_key,
                rawValue=raw_value_text,
                normalizedValue=normalized,
                confidence="high" if normalized is not None else "medium",
                warnings=value_warnings,
            )
        )

    missing = sorted(expected - seen)
    if not parsed:
        warnings.append("No expected financial fields were found. Analysis was not updated.")
    else:
        warnings.append("Preview only — analysis not updated and file was not stored.")

    return DataRoomParsePreview(
        recordKey=record_key,
        statementType=PARSEABLE_RECORD_KEYS[record_key],
        parsedRecords=parsed,
        missingExpectedFields=missing,
        unsupportedFields=sorted(set(unsupported)),
        rowCount=max(len(data_rows) - 1, 0),
        warnings=warnings,
    )


def parse_csv_bytes(record_key: str, file_bytes: bytes) -> DataRoomParsePreview:
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="replace")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
            unsupportedFields=[],
            rowCount=0,
            warnings=[f"CSV could not be parsed safely: {exc}. Analysis was not updated."],
        )
    return _records_from_rows(record_key, rows)


def parse_xlsx_bytes(record_key: str, file_bytes: bytes) -> DataRoomParsePreview:
    if openpyxl is None:
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
            unsupportedFields=[],
            rowCount=0,
            warnings=["XLSX parsing is unavailable because openpyxl is not installed. Analysis was not updated."],
        )
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        sheet = workbook.active
        rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    except Exception as exc:  # noqa: BLE001 - safe preview should never crash endpoint.
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
            unsupportedFields=[],
            rowCount=0,
            warnings=[f"XLSX could not be parsed safely: {exc}. Analysis was not updated."],
        )
    return _records_from_rows(record_key, rows)


async def parse_structured_financial_file(
    record_key: str,
    upload_file: UploadFile,
) -> DataRoomParsePreview:
    file_name = upload_file.filename or "unknown"
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    file_bytes = await upload_file.read()

    if extension == "csv" or (upload_file.content_type or "").lower() == "text/csv":
        return parse_csv_bytes(record_key, file_bytes)
    if extension == "xlsx":
        return parse_xlsx_bytes(record_key, file_bytes)
    if extension == "pdf":
        from app.services.data_room.pdf_parser import parse_pdf_bytes
        return parse_pdf_bytes(record_key, file_bytes)
    if extension == "docx":
        from app.services.data_room.docx_parser import parse_docx_bytes
        return parse_docx_bytes(record_key, file_bytes)

    warning = (
        "XLS parsing is not available in this environment. Analysis was not updated."
        if extension == "xls"
        else "This file type is not supported for structured parsing preview. Analysis was not updated."
    )
    return DataRoomParsePreview(
        recordKey=record_key,
        statementType=PARSEABLE_RECORD_KEYS[record_key],
        parsedRecords=[],
        missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
        unsupportedFields=[],
        rowCount=0,
        warnings=[warning],
    )
