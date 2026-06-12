import json
import os
from typing import List
from app.core.config import settings
from app.models.market_watch import FundingProduct
from app.services.market_watch.provider_adapters import BOCHKProductCatalogAdapter

class ProductCatalogService:
    def __init__(self):
        # Path relative to repository root
        self.local_json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "demo_data",
            "funding_products.json"
        )

    async def get_products(self) -> List[FundingProduct]:
        if settings.BOCHK_CATALOG_CONFIGURED:
            # Configured: use the provider adapter
            adapter = BOCHKProductCatalogAdapter()
            res = await adapter.fetch()
            if res.get("status", {}).get("mode") == "provider_configured" and res.get("data"):
                products_list = res["data"].get("products", [])
                return [FundingProduct(**p) for p in products_list]
            
        # Fallback to local JSON catalog
        if not os.path.exists(self.local_json_path):
            return []
        try:
            with open(self.local_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [FundingProduct(**p) for p in data]
        except Exception:
            return []

product_catalog_service = ProductCatalogService()
