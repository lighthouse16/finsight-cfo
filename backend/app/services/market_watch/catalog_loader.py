import os
import json
import logging
from typing import Dict, List, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def load_lender_catalog() -> List[Dict[str, Any]]:
    # Fallback paths
    paths = []
    if settings.LENDER_CATALOG_PATH:
        paths.append(settings.LENDER_CATALOG_PATH)
    paths.extend([
        os.path.join("demo_data", "provider_catalog.json"),
        os.path.join("demo_data", "provider_catalog.sample.json")
    ])
    
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lenders = data.get("lenders", [])
                    if lenders:
                        logger.info(f"Successfully loaded lender catalog from {path}")
                        return lenders
            except Exception as e:
                logger.error(f"Failed to load lender catalog from {path}: {e}")
                
    return []
