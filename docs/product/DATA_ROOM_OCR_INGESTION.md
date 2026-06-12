# Data Room OCR & Document Ingestion

## Overview

The FinSight CFO Data Room supports multiple document formats, with the goal of extracting financial statement rows into a structured format for calibration and advisory models. To enable "real as possible" document ingestion for PDF and DOCX files without falsely claiming cloud OCR capabilities when they are unavailable, the ingestion flow is built on a fallback hierarchy.

## Document Ingestion Pipeline

1. **Structured Ingestion (CSV/XLSX)**
   If a file is uploaded as CSV or XLSX, it is directly processed using pandas. Lines are parsed, and known metric fields are normalized against `EXPECTED_FIELDS`.

2. **Text-Layer PDF Parsing**
   If a file is a PDF, the system first attempts to extract the embedded text layer using `pypdf`.
   - The parser reads text from each page.
   - Text is split into lines and heuristics are applied to separate financial metrics from trailing numeric values.
   - Example line splitting matches patterns with multi-spaces, tabs, or trailing numbers.
   - If a text layer exists, the parsed lines are forwarded to the unified `structured_parser`, and the file status is mapped to `parsed_pdf_text_layer`.

3. **DOCX Parsing**
   If a file is a DOCX, the system utilizes `python-docx` to read all paragraphs and tables.
   - Each paragraph text is evaluated.
   - Table rows are converted into line items.
   - Similar to PDF text layers, lines are separated into `[metric, value]` pairs via regex/heuristics.
   - The file status is recorded as `parsed_docx_text`.

4. **OCR Adapter Stub**
   If a PDF contains no text layer (e.g. image-only PDF, scans) or extraction fails entirely:
   - The system checks an environment configuration (`CLOUD_OCR_API_KEY`) via `OCRAdapter`.
   - Since cloud provider integration remains pending in demo contexts, the adapter returns `provider_not_configured`.
   - No mock numbers are invented. The user is shown an explicit warning, and the file status maps to `ocr_provider_not_configured`.
   - The user is then presented with a Call to Action (CTA) in the Data Room to upload a structured CSV/XLSX file or configure OCR.

## File Statuses & UI Labels

The unified `UploadedFileRecord` utilizes the following source modes for file extraction:
- `parsed_structured`: CSV/XLSX parsed successfully.
- `parsed_pdf_text_layer`: Native text successfully extracted from PDF.
- `parsed_docx_text`: Native text successfully extracted from DOCX.
- `ocr_provider_configured`: An image file sent to OCR requires manual review.
- `ocr_provider_not_configured`: Image file could not be parsed; no OCR credential found.
- `unsupported`: Unknown or incompatible file type.

## Dependencies

- **pypdf**: Used for lightweight, dependency-free text-layer PDF parsing.
- **python-docx**: Used for native Word document parsing.

Both libraries operate entirely locally and safely read bytes directly from the FastApi upload handlers, without requiring disk temp-files.
