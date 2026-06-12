import io
import re

from app.models.data_room import DataRoomParsePreview
from app.services.data_room.structured_parser import _records_from_rows, PARSEABLE_RECORD_KEYS, EXPECTED_FIELDS
from app.services.data_room.ocr_adapter import ocr_adapter

try:
    import pypdf
except ImportError:
    pypdf = None

def parse_pdf_bytes(record_key: str, file_bytes: bytes) -> DataRoomParsePreview:
    if pypdf is None:
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
            unsupportedFields=[],
            rowCount=0,
            warnings=["PDF parsing is unavailable because pypdf is not installed. Analysis was not updated."],
        )
    
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as exc:
        return DataRoomParsePreview(
            recordKey=record_key,
            statementType=PARSEABLE_RECORD_KEYS[record_key],
            parsedRecords=[],
            missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
            unsupportedFields=[],
            rowCount=0,
            warnings=[f"PDF could not be parsed safely: {exc}. Analysis was not updated."],
        )
    
    warnings = []
    is_ocr = False
    
    if not text.strip():
        # It might be an image-only PDF
        ocr_status = ocr_adapter.check_status()
        if ocr_status == "provider_not_configured":
            warning = "PDF appears to be an image or has no text layer, and OCR provider is not configured."
        else:
            warning = "PDF requires OCR, but adapter returned no text."
            ocr_text = ocr_adapter.process_document(file_bytes)
            if ocr_text:
                text = ocr_text
                warning = "PDF text extracted via OCR."
                is_ocr = True

        warnings.append(warning)
        if not text.strip():
            return DataRoomParsePreview(
                recordKey=record_key,
                statementType=PARSEABLE_RECORD_KEYS[record_key],
                parsedRecords=[],
                missingExpectedFields=sorted(EXPECTED_FIELDS[record_key]),
                unsupportedFields=[],
                rowCount=0,
                warnings=warnings,
            )
        
    rows = [["metric", "value"]]
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split by 2 or more spaces or tab
        parts = re.split(r'\s{2,}|\t', line)
        if len(parts) >= 2:
            rows.append([parts[0], parts[-1]])
        elif len(parts) == 1:
            match = re.search(r'^(.*?)\s+([\d.,()\-]+)$', line)
            if match:
                rows.append([match.group(1), match.group(2)])
            
    preview = _records_from_rows(record_key, rows)
    preview.warnings.extend(warnings)
    return preview
