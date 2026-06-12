import os
from typing import Literal

OCRStatus = Literal["provider_not_configured", "configured"]

class OCRAdapter:
    """Adapter for interacting with an external OCR provider."""

    def check_status(self) -> OCRStatus:
        """Check if an OCR provider is configured in the environment."""
        if os.environ.get("CLOUD_OCR_API_KEY"):
            return "configured"
        return "provider_not_configured"

    def process_document(self, file_bytes: bytes) -> str | None:
        """Process a document using OCR if configured.
        
        Returns the extracted text, or None if the provider is not configured
        or the extraction fails.
        """
        if self.check_status() == "provider_not_configured":
            return None
        
        # Stub for actual cloud OCR processing.
        # This prevents claiming success if the adapter doesn't extract text.
        return None

ocr_adapter = OCRAdapter()
