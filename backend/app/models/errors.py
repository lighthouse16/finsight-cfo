from fastapi import HTTPException
from typing import List, Optional

def raise_missing_workspace_error(code: str = "ACTIVE_SNAPSHOT_NOT_FOUND"):
    raise HTTPException(
        status_code=404,
        detail={
            "code": code,
            "message": "Active workspace data is required before this analysis can run.",
            "source": "workspace",
            "nextActions": [
                "Upload financial records",
                "Build financial snapshot",
                "Review Data Room"
            ]
        }
    )

def raise_insufficient_data_error(missing_requirements: List[str]):
    raise HTTPException(
        status_code=422,
        detail={
            "code": "INSUFFICIENT_WORKSPACE_DATA",
            "message": "The active workspace snapshot is incomplete or cannot be analyzed.",
            "source": "workspace",
            "missingRequirements": missing_requirements,
            "nextActions": [
                "Upload missing documents",
                "Review snapshot mapping",
                "Rebuild financial snapshot"
            ]
        }
    )

def raise_upstream_unavailable_error(message: Optional[str] = None):
    raise HTTPException(
        status_code=503,
        detail={
            "code": "UPSTREAM_UNAVAILABLE",
            "message": message or "Live market data provider is currently unavailable and no valid cached snapshot exists.",
            "source": "provider",
            "nextActions": [
                "Retry later",
                "Check provider configuration",
                "Continue without market overlay if the target analysis supports it"
            ]
        }
    )

def raise_cdi_unavailable_error():
    raise HTTPException(
        status_code=503,
        detail={
            "code": "CONSENT_PROVIDER_UNAVAILABLE",
            "message": "Consent-based data provider is not configured for this workspace.",
            "source": "provider",
            "nextActions": [
                "Configure a consent provider",
                "Continue with financial-statement-only analysis if supported",
                "Return to Data Room"
            ]
        }
    )
