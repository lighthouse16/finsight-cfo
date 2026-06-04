import httpx
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HKABWebClient:
    def __init__(self):
        self.url = "https://www.hkab.org.hk/en/rates/hibor"
        self.timeout = 10.0

    async def fetch_latest_hibor(self) -> Optional[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(self.url, headers=headers)
                if res.status_code != 200:
                    logger.error(f"HKAB page returned status {res.status_code}")
                    return None
                return self.parse_html(res.text)
        except Exception as e:
            logger.error(f"Failed to fetch HIBOR from HKAB page: {e}")
            return None

    def parse_html(self, html: str) -> Optional[Dict[str, Any]]:
        # Extract date
        date_match = re.search(r'on\s+(\d{4})-(\d{1,2})-(\d{1,2})', html)
        if not date_match:
            logger.warning("HKAB HIBOR page date not found via regex")
            return None
        
        year, month, day = date_match.groups()
        source_date = f"{year}-{int(month):02d}-{int(day):02d}"
        
        # Extract table rows
        pattern = r'<div class="general_table_cell hibor_maturity"><div>([^<]+)</div></div><div class="general_table_cell last"><div>([^<]+)</div></div>'
        matches = re.findall(pattern, html)
        
        rates = {}
        for maturity, rate_str in matches:
            maturity = maturity.strip()
            try:
                val = float(rate_str.strip())
                rates[maturity] = val
            except ValueError:
                pass
                
        if not rates:
            logger.warning("No HIBOR rates parsed from HKAB page")
            return None
            
        return {
            "source_date": source_date,
            "rates": rates,
            "source_label": "HKAB public HIBOR page"
        }

hkab_web_client = HKABWebClient()
