export type CdiConsentScope =
  | 'bank_transactions'
  | 'trade_receivables'
  | 'tax_filing_summary'
  | 'payroll_mpf_signal'
  | 'credit_bureau_summary'

export type CdiConsentSession = {
  consentId: string
  companyId: string
  companyName: string
  status: 'created' | 'authorized' | 'expired' | 'revoked'
  requestedScopes: CdiConsentScope[]
  authorizationUrl: string
  createdAt: string
  expiresAt: string
  disclaimer: string
}

export type CdiMockDataResponse = {
  consentId: string
  companyId: string
  companyName: string
  status: 'created' | 'authorized' | 'expired' | 'revoked'
  source: string
  generatedAt: string
  cashflowSignal: {
    averageMonthlyInflow: number
    averageMonthlyOutflow: number
    netCashflowTrend: 'improving' | 'stable' | 'deteriorating'
    volatilityBand: 'low' | 'moderate' | 'high'
    bouncedPaymentCount6m: number
  }
  receivablesSignal: {
    verifiedInvoiceValue: number
    eligibleInvoiceValue: number
    topBuyerConcentration: number
    averageDaysToCollect: number
    digitalCollateralBand: 'strong' | 'moderate' | 'watch'
  }
  creditBureauSignal: {
    repaymentDelinquencyCount12m: number
    bureauBand: 'clear' | 'watch' | 'adverse'
    tradeReferenceCount: number
  }
  fundingImplications: string[]
  riskImplications: string[]
  disclaimer: string
}

import { API_BASE_URL } from '../../lib/apiBase'


export async function createMockCdiConsent(params: {
  companyId: string
  companyName: string
  requestedScopes?: CdiConsentScope[]
}): Promise<CdiConsentSession> {
  const response = await fetch(`${API_BASE_URL}/api/cdi/mock-consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      companyId: params.companyId,
      companyName: params.companyName,
      requestedScopes: params.requestedScopes ?? [
        'bank_transactions',
        'trade_receivables',
        'credit_bureau_summary',
      ],
    }),
    signal: AbortSignal.timeout(8000),
  })

  if (!response.ok) {
    throw new Error(`Mock CDI consent API returned status ${response.status}`)
  }

  return response.json()
}

export async function getMockCdiData(consentId: string): Promise<CdiMockDataResponse> {
  const response = await fetch(`${API_BASE_URL}/api/cdi/mock-data/${consentId}`, {
    signal: AbortSignal.timeout(8000),
  })

  if (!response.ok) {
    throw new Error(`Mock CDI data API returned status ${response.status}`)
  }

  return response.json()
}

export async function createAndFetchMockCdiData(params: {
  companyId: string
  companyName: string
  requestedScopes?: CdiConsentScope[]
}): Promise<{ consent: CdiConsentSession; data: CdiMockDataResponse }> {
  const consent = await createMockCdiConsent(params)
  const data = await getMockCdiData(consent.consentId)
  return { consent, data }
}
