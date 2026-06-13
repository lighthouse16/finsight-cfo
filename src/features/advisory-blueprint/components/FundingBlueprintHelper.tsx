import { useState } from 'react'
import { Loader2, Play, DollarSign, Database, Activity, Landmark, ShieldCheck } from 'lucide-react'
import SectionBlock from '../../../components/platform/SectionBlock'
import StatusChip from '../../../components/platform/StatusChip'
import { API_BASE_URL } from '../../../lib/apiBase'

interface FundingBlueprintHelperProps {
  onRun?: () => void;
}

interface FundingResult {
  pd_estimate?: { tier?: string };
  stress_test?: { stressed_dscr?: number; status?: string };
  loan_structure?: {
    weighted_average_cost_bps?: number;
    recommended_facilities?: Array<{ facility: string; amount: number }>;
    recommendation_summary?: string;
  };
  cdi_data?: {
    provider_name?: string;
    delivered_invoice_total?: number;
    alternative_collateral_hkd?: number;
  };
}

export default function FundingBlueprintHelper({ onRun }: FundingBlueprintHelperProps) {
  const [amount, setAmount] = useState(10000000)
  const [consent, setConsent] = useState(false)
  const [shockBps, setShockBps] = useState(150)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<FundingResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const workspaceId = localStorage.getItem('active_workspace_id') || 'demo_company'
      
      const res = await fetch(`${API_BASE_URL}/api/advisory/funding-blueprint`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-workspace-id': workspaceId
        },
        body: JSON.stringify({
          company_id: workspaceId,
          requested_amount_hkd: amount,
          consent_granted: consent,
          scenario_shock_bps: shockBps
        })
      })

      if (!res.ok) {
        throw new Error('Failed to fetch funding blueprint')
      }

      const data = await res.json()
      setResult(data)
      if (onRun) onRun()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <SectionBlock
      title="Phase 3: Funding Blueprint Engine"
      icon={<Landmark size={20} className="text-softform-teal-500" />}
      action={<StatusChip variant="signal">BOCHK Optimizer</StatusChip>}
      containerType="card"
      className="rounded-[32px] p-6 sm:p-8 space-y-6 mt-8 border border-softform-teal-500/30"
    >
      <div className="flex flex-col md:flex-row gap-6">
        <div className="w-full md:w-1/3 space-y-5 bg-white/40 p-5 rounded-[22px] border border-white/60">
          <h3 className="font-semibold text-softform-navy-950 text-sm">Engine Parameters</h3>
          
          <div className="space-y-4 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-softform-navy-950/70">Requested Amount (HKD)</label>
              <input
                type="number"
                value={amount}
                onChange={e => setAmount(Number(e.target.value))}
                className="w-full bg-white/60 border border-white/80 rounded-xl px-3 py-2 text-softform-navy-950 focus:outline-none focus:ring-2 focus:ring-softform-teal-deep/20"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-softform-navy-950/70">CDI Data Consent</label>
              <button
                onClick={() => setConsent(!consent)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${consent ? 'bg-softform-teal-500' : 'bg-slate-300'}`}
              >
                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${consent ? 'translate-x-4' : 'translate-x-1'}`} />
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-softform-navy-950/70">HIBOR Shock (bps)</label>
              <input
                type="number"
                value={shockBps}
                onChange={e => setShockBps(Number(e.target.value))}
                className="w-full bg-white/60 border border-white/80 rounded-xl px-3 py-2 text-softform-navy-950 focus:outline-none focus:ring-2 focus:ring-softform-teal-deep/20"
              />
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-softform-navy-900 hover:bg-softform-navy-800 text-white text-xs font-semibold rounded-xl transition shadow-sm disabled:opacity-50"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              Run Engine
            </button>
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        </div>

        <div className="w-full md:w-2/3 space-y-4">
          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center p-8 bg-white/20 rounded-[22px] border border-dashed border-softform-navy-950/10 text-center">
              <Activity className="text-softform-navy-950/20 mb-3" size={32} />
              <p className="text-sm text-softform-text-secondary">Run the engine to generate the deterministic funding blueprint.</p>
            </div>
          )}

          {loading && (
            <div className="h-full flex flex-col items-center justify-center p-8 bg-white/20 rounded-[22px] border border-softform-navy-950/10 text-center">
              <Loader2 className="animate-spin text-softform-teal-500 mb-3" size={32} />
              <p className="text-sm text-softform-text-secondary animate-pulse">Running BOCHK Optimization Models...</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Output Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-white/60 rounded-[18px] border border-white/80 shadow-sm flex items-center gap-3">
                  <div className="p-2 bg-softform-teal-deep/10 text-softform-teal-deep rounded-xl"><ShieldCheck size={18} /></div>
                  <div>
                    <p className="text-[10px] font-semibold text-softform-text-muted uppercase">PD Tier</p>
                    <p className="font-bold text-sm text-softform-navy-950">{result.pd_estimate?.tier || 'N/A'}</p>
                  </div>
                </div>
                <div className="p-4 bg-white/60 rounded-[18px] border border-white/80 shadow-sm flex items-center gap-3">
                  <div className="p-2 bg-softform-amber-500/10 text-softform-amber-500 rounded-xl"><Activity size={18} /></div>
                  <div>
                    <p className="text-[10px] font-semibold text-softform-text-muted uppercase">Stressed DSCR</p>
                    <p className="font-bold text-sm text-softform-navy-950">{result.stress_test?.stressed_dscr?.toFixed(2)}x ({result.stress_test?.status?.toUpperCase()})</p>
                  </div>
                </div>
              </div>

              {/* Loan Structure */}
              {result.loan_structure && (
                <div className="p-5 bg-softform-navy-900 rounded-[22px] text-white shadow-md">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-sm font-semibold tracking-wide flex items-center gap-2"><DollarSign size={16} className="text-softform-aqua-300"/> Recommended Structure</h4>
                    <span className="text-xs bg-white/10 px-2 py-0.5 rounded-md border border-white/20">{result.loan_structure.weighted_average_cost_bps} bps avg</span>
                  </div>
                  <div className="space-y-2">
                    {result.loan_structure.recommended_facilities?.map((f: { facility: string; amount: number }, i: number) => (
                      <div key={i} className="flex justify-between items-center text-xs border-b border-white/10 pb-2 last:border-0 last:pb-0">
                        <span className="text-white/80">{f.facility}</span>
                        <span className="font-bold">HKD {f.amount.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-white/50 mt-4 italic">{result.loan_structure.recommendation_summary}</p>
                </div>
              )}

              {/* CDI Box */}
              {result.cdi_data && (
                <div className="p-4 border border-softform-teal-500/30 bg-softform-teal-500/5 rounded-[18px] text-xs">
                  <div className="flex items-center gap-2 font-semibold text-softform-navy-950 mb-1">
                    <Database size={14} className="text-softform-teal-deep" />
                    CDI Alternative Data
                  </div>
                  <p className="text-softform-text-secondary leading-relaxed">
                    {result.cdi_data.provider_name}. Delivered Invoice Total: HKD {result.cdi_data.delivered_invoice_total?.toLocaleString()}. Alternative Collateral HKD: {result.cdi_data.alternative_collateral_hkd?.toLocaleString()}.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </SectionBlock>
  )
}
