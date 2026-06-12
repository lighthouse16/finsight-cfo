import uuid
from datetime import datetime, timedelta
from app.models.advisory import CdiMockResponse, CdiInvoiceRecord
from app.core.config import get_settings
from app.services.providers.cdi_connector import CDIConnector
from app.services.providers.base import ProviderNotConfiguredError

def get_cdi_mock_data(consent_granted: bool) -> CdiMockResponse:
    """
    Returns alternative data from logistics/trade platforms.
    Routes to live CDI connector if configured, otherwise falls back to deterministic mock data.
    """
    if not consent_granted:
        return CdiMockResponse(
            consent_token=None,
            provider_name="CDI Commercial Gateway",
            invoices=[],
            delivered_invoice_total=0.0,
            in_transit_invoice_total=0.0,
            alternative_collateral_hkd=0.0,
            disclaimer="Consent denied. CDI alternative data cannot be accessed.",
            warnings=["No consent provided for alternative data flow."]
        )

    settings = get_settings()
    
    # Try Live Provider first
    if settings.provider_configured("cdi") or not settings.ALLOW_DEMO_FALLBACK:
        try:
            connector = CDIConnector()
            live_data = connector.fetch_alternative_data(consent_id=f"consent_{uuid.uuid4().hex[:8]}")
            
            return CdiMockResponse(
                consent_token=live_data["data"].get("consent_id", ""),
                provider_name=live_data["source_name"],
                invoices=[],
                delivered_invoice_total=1000000.0,  # Stub mapped from live data
                in_transit_invoice_total=500000.0,  # Stub mapped from live data
                alternative_collateral_hkd=800000.0, # Stub mapped from live data
                disclaimer=live_data["caveat"],
                warnings=["Live CDI data parsed metrics are using stub aggregations until specs are defined."]
            )
        except ProviderNotConfiguredError:
            if not settings.ALLOW_DEMO_FALLBACK:
                raise
                
    # Fallback to Mock Data
    token = f"cdi_tok_{uuid.uuid4().hex[:12]}"
    now = datetime.now()
    
    invoices = [
        CdiInvoiceRecord(
            invoice_id="INV-9901",
            buyer_name="Global Retail Partners",
            amount=1200000.0,
            currency="HKD",
            status="DELIVERED",
            expected_payment_date=(now + timedelta(days=15)).strftime("%Y-%m-%d")
        ),
        CdiInvoiceRecord(
            invoice_id="INV-9902",
            buyer_name="MegaTech Manufacturing",
            amount=850000.0,
            currency="HKD",
            status="IN_TRANSIT",
            expected_payment_date=(now + timedelta(days=30)).strftime("%Y-%m-%d")
        ),
        CdiInvoiceRecord(
            invoice_id="INV-9903",
            buyer_name="Asia Logistics Hub",
            amount=450000.0,
            currency="HKD",
            status="DELIVERED",
            expected_payment_date=(now + timedelta(days=5)).strftime("%Y-%m-%d")
        )
    ]
    
    delivered_total = sum(i.amount for i in invoices if i.status == "DELIVERED")
    in_transit_total = sum(i.amount for i in invoices if i.status == "IN_TRANSIT")
    
    # Example logic: delivered invoices can serve as alternative collateral at 80% advance rate
    alternative_collateral_hkd = delivered_total * 0.80
    
    return CdiMockResponse(
        consent_token=token,
        provider_name="CargoX / Tradelink CDI Mock",
        invoices=invoices,
        delivered_invoice_total=delivered_total,
        in_transit_invoice_total=in_transit_total,
        alternative_collateral_hkd=alternative_collateral_hkd,
        disclaimer="This is a mocked CDI alternative data flow. It does not connect to the real HKMA CDI platform. Provided for BOCHK Challenge demo context only.",
        warnings=[]
    )
