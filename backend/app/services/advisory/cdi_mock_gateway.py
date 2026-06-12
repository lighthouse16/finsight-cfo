import uuid
from datetime import datetime, timedelta
from app.models.advisory import CdiMockResponse, CdiInvoiceRecord

def get_cdi_mock_data(consent_granted: bool) -> CdiMockResponse:
    """
    Returns deterministic mocked alternative data from logistics/trade platforms
    via a mocked CDI gateway integration, simulating the consent-based flow.
    """
    if not consent_granted:
        return CdiMockResponse(
            consent_token=None,
            provider_name="CDI Commercial Gateway (Mock)",
            invoices=[],
            delivered_invoice_total=0.0,
            in_transit_invoice_total=0.0,
            alternative_collateral_hkd=0.0,
            disclaimer="Consent denied. CDI alternative data cannot be accessed.",
            warnings=["No consent provided for alternative data flow."]
        )
        
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
