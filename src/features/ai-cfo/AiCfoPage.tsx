import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  BotMessageSquare,
  FileText,
  Landmark,
  RotateCw,
  Send,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import DemoFlowRail from '../../components/platform/DemoFlowRail'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { getAdvisoryBlueprint, getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import type { AdvisoryBlueprintResponse, CreditScoringResult } from '../advisory-blueprint/types'
import type { FinancialAnalysisResponse, FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'

type AiMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

type AiContext = {
  financial: FinancialAnalysisResponse | null
  credit: CreditScoringResult | null
  funding: FundingChannelRankingResponse | null
  macro: RedFlagsMacroSummaryResponse | null
  blueprint: AdvisoryBlueprintResponse | null
}

function formatHKD(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  if (Math.abs(value) >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

function formatPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(2)}%`
}

function formatBand(value?: string | null) {
  if (!value) return 'Unavailable'
  return value.replace(/_/g, ' ')
}

function getValuation(financial: FinancialAnalysisResponse | null) {
  return financial?.valuation ?? null
}

function buildAnswer(question: string, context: AiContext): AiMessage {
  const q = question.toLowerCase()
  const financial = context.financial
  const credit = context.credit
  const funding = context.funding
  const macro = context.macro
  const valuation = getValuation(financial)
  const blueprint = context.blueprint
  const topChannel = funding?.channels?.find((channel) => channel.key === funding.topChannelKey) ?? funding?.channels?.[0]
  const company = financial?.snapshot.companyName ?? 'the company'

  if (q.includes('valuation') || q.includes('value') || q.includes('dcf') || q.includes('wacc')) {
    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      sources: ['Valuation', 'Financial Health'],
      content: `${company}'s indicative valuation context is ${formatHKD(valuation?.dcf?.enterpriseValue)} enterprise value and ${formatHKD(valuation?.dcf?.equityValue)} equity value. The model WACC is ${formatPercent(valuation?.wacc?.wacc)}. Treat this as planning context only: it supports the funding narrative, but should not be used as a formal appraisal without validating assumptions, forecast drivers, discount rate, and terminal value.`,
    }
  }

  if (q.includes('credit') || q.includes('readiness') || q.includes('pd') || q.includes('score')) {
    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      sources: ['Credit Readiness', 'Financial Health'],
      content: `The readiness scorecard is ${credit?.compositeScore ?? 'unavailable'}, with funding readiness marked as ${formatBand(credit?.fundingReadiness)}. ${credit?.pdProxyBand ?? 'The PD proxy band is unavailable.'} Key positives include ${(credit?.positiveDrivers ?? []).slice(0, 2).join('; ') || 'no positive drivers available'}. Key watch items include ${(credit?.riskDrivers ?? []).slice(0, 2).join('; ') || 'no risk drivers available'}. This is context-only and not a lending decision.`,
    }
  }

  if (q.includes('funding') || q.includes('facility') || q.includes('loan') || q.includes('channel')) {
    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      sources: ['Funding Strategy', 'Advisory Blueprint'],
      content: topChannel
        ? `The top funding channel context is ${topChannel.label} with ${formatBand(topChannel.fitBand)} fit and score ${topChannel.score}. Use case: ${topChannel.useCase}. Rationale: ${topChannel.rationale}. Before using this externally, validate facility amount, collateral, tenor, covenants, and updated bank eligibility requirements.`
        : 'Funding channel ranking is unavailable. Open Funding Strategy after backend/data context is available to review channels, facility fit, and constraints.',
    }
  }

  if (q.includes('risk') || q.includes('macro') || q.includes('red flag') || q.includes('market')) {
    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      sources: ['Market Watch', 'Macro Risk Summary'],
      content: `${macro?.headline ?? 'Macro context is currently unavailable.'} Key red flags: ${(macro?.redFlags ?? []).slice(0, 3).map((flag) => `${flag.label} (${flag.severity})`).join('; ') || 'none available'}. Suggested mitigants: ${(macro?.mitigants ?? []).slice(0, 2).map((item) => item.label).join('; ') || 'none available'}.`,
    }
  }

  if (q.includes('report') || q.includes('summary') || q.includes('brief') || q.includes('advisor')) {
    const actionSummary = (blueprint?.recommendedActions ?? [])
      .slice(0, 3)
      .map((action) => `${action.label}: ${action.rationale}`)
      .join(' ')

    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      sources: ['Reports', 'Advisory Blueprint'],
      content: blueprint?.executiveBrief
        ? `${blueprint.executiveBrief} Recommended next actions: ${actionSummary || 'review the advisory blueprint actions.'} Open Reports for a CFO snapshot or Advisory Blueprint for the advisor-facing version.`
        : 'The advisor-ready summary is unavailable. Open Reports for the current CFO snapshot and Advisory Blueprint for detailed advisory output.',
    }
  }

  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    sources: ['Overview', 'Financial Health', 'Credit Readiness', 'Funding Strategy'],
    content: `${company} currently shows financial health as ${formatBand(financial?.summary?.overallBand)}, readiness as ${formatBand(credit?.fundingReadiness)}, top funding context as ${topChannel?.label ?? 'unavailable'}, and valuation EV as ${formatHKD(valuation?.dcf?.enterpriseValue)}. A practical next step is to review Financial Health watch items, then move to Funding Strategy and Advisory Blueprint for a lender-facing narrative.`,
  }
}

export default function AiCfoPage() {
  const [context, setContext] = useState<AiContext>({ financial: null, credit: null, funding: null, macro: null, blueprint: null })
  const [messages, setMessages] = useState<AiMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadContext = async () => {
    setLoading(true)
    setError(null)
    try {
      const [financial, credit, funding, macro, blueprint] = await Promise.all([
        getFinancialHealthAnalysis().catch((e) => {
          console.warn('AI CFO financial context unavailable', e)
          return null
        }),
        getCreditScore().catch((e) => {
          console.warn('AI CFO credit context unavailable', e)
          return null
        }),
        getFundingChannelRanking().catch((e) => {
          console.warn('AI CFO funding context unavailable', e)
          return null
        }),
        getRedFlagsMacroSummary().catch((e) => {
          console.warn('AI CFO macro context unavailable', e)
          return null
        }),
        getAdvisoryBlueprint().catch((e) => {
          console.warn('AI CFO advisory context unavailable', e)
          return null
        }),
      ])
      const nextContext = { financial, credit, funding, macro, blueprint }
      setContext(nextContext)
      setMessages([
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          sources: ['Workspace context'],
          content: 'I have loaded the current CFO workspace context. Ask about valuation, credit readiness, funding strategy, macro risks, or the advisor-ready brief. Answers are deterministic and context-only for demo purposes.',
        },
      ])
    } catch (e) {
      console.error('AI CFO context load failed', e)
      setError('AI CFO is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadContext()
  }, [])

  const quickPrompts = useMemo(
    () => [
      'What is the current credit readiness view?',
      'Summarize the funding strategy.',
      'Explain valuation and WACC.',
      'What macro risks should we watch?',
      'Draft the advisor-ready summary.',
    ],
    [],
  )

  const submitQuestion = (question: string) => {
    const trimmed = question.trim()
    if (!trimmed) return
    const userMessage: AiMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed }
    const answer = buildAnswer(trimmed, context)
    setMessages((prev) => [...prev, userMessage, answer])
    setInput('')
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    submitQuestion(input)
  }

  if (loading) {
    return (
      <div className="flex min-h-[50dvh] flex-col items-center justify-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep animate-spin">
          <RotateCw size={24} />
        </div>
        <p className="text-sm font-medium text-softform-text-secondary animate-pulse">Loading AI CFO context...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">Service Connection Issue</p>
          <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">{error}</p>
          <button
            type="button"
            onClick={loadContext}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={14} />
            Retry Context
          </button>
        </div>
      </div>
    )
  }

  const financial = context.financial
  const credit = context.credit
  const funding = context.funding
  const valuation = getValuation(financial)
  const topChannel = funding?.channels?.find((channel) => channel.key === funding.topChannelKey) ?? funding?.channels?.[0]

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="AI CFO"
        subtitle="Ask questions across the current financial, valuation, readiness, funding, market, and advisory context."
        chip={<StatusChip variant="neutral">Context assistant</StatusChip>}
      />

      <DemoFlowRail />

      <section className="softform-panel rounded-[32px] p-8 space-y-6 shadow-floating-panel relative overflow-hidden bg-gradient-to-br from-white/95 via-softform-mist-50/70 to-softform-ice-100/50 border border-white">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-softform-teal-deep">Digital CFO assistant</span>
            <h2 className="text-3xl font-black text-softform-navy-950 tracking-tight">
              {financial?.snapshot.companyName ?? 'Workspace Company'} · ask your CFO workspace
            </h2>
            <p className="text-sm leading-relaxed text-softform-text-secondary max-w-3xl">
              This demo assistant uses deterministic context templates instead of an external LLM call. It is designed to show how the product can answer across the CFO workflow while keeping sources visible.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Link to="/platform/reports" className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner hover-lift">
              <FileText size={18} className="text-softform-teal-deep" />
              <p className="mt-3 text-sm font-black text-softform-navy-950">Reports</p>
              <p className="mt-1 text-xs text-softform-text-secondary">Open CFO snapshot.</p>
            </Link>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-softform-aqua-300/25 bg-softform-mist-100/70 p-4 shadow-soft-inner hover-lift">
              <Sparkles size={18} className="text-softform-teal-deep" />
              <p className="mt-3 text-sm font-black text-softform-navy-950">Blueprint</p>
              <p className="mt-1 text-xs text-softform-text-secondary">Open advisor brief.</p>
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm">
          <ShieldCheck size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Readiness</p>
          <p className="mt-2 text-2xl font-black text-softform-navy-950 tabular-finance">{credit?.compositeScore ?? 'N/A'}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">{formatBand(credit?.fundingReadiness)}</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm">
          <Landmark size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Top channel</p>
          <p className="mt-2 text-lg font-black text-softform-navy-950">{topChannel?.label ?? 'N/A'}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">{formatBand(topChannel?.fitBand)}</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm">
          <BotMessageSquare size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Financial band</p>
          <p className="mt-2 text-lg font-black text-softform-navy-950">{formatBand(financial?.summary?.overallBand)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">Revenue {formatHKD(financial?.snapshot.incomeStatement.revenue)}</p>
        </div>
        <div className="rounded-[22px] border border-white/60 bg-white/55 p-5 shadow-sm">
          <Sparkles size={20} className="text-softform-teal-deep" />
          <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">Valuation EV</p>
          <p className="mt-2 text-lg font-black text-softform-navy-950 tabular-finance">{formatHKD(valuation?.dcf?.enterpriseValue)}</p>
          <p className="mt-1 text-xs text-softform-text-secondary">WACC {formatPercent(valuation?.wacc?.wacc)}</p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950">Suggested questions</h2>
            <StatusChip variant="neutral">Prompts</StatusChip>
          </div>
          <div className="space-y-3">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => submitQuestion(prompt)}
                className="group w-full rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-left text-xs font-semibold text-softform-navy-950 hover:bg-white/70 transition"
              >
                <span>{prompt}</span>
                <ArrowRight size={14} className="float-right mt-0.5 text-softform-teal-deep transition group-hover:translate-x-1" />
              </button>
            ))}
          </div>
          <p className="text-[11px] leading-relaxed text-softform-text-muted">
            Demo note: answers are generated locally from current app context, not from a production LLM service.
          </p>
        </div>

        <div className="softform-card rounded-[28px] p-0 overflow-hidden">
          <div className="border-b border-softform-navy-950/5 px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <BotMessageSquare size={20} className="text-softform-teal-deep" />
              Conversation
            </h2>
            <StatusChip variant="signal">Workspace loaded</StatusChip>
          </div>

          <div className="max-h-[560px] overflow-y-auto px-6 py-5 space-y-4 bg-white/25">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[86%] rounded-[22px] px-4 py-3 shadow-sm ${message.role === 'user' ? 'bg-softform-navy-900 text-white' : 'bg-white/75 text-softform-text-secondary border border-white/70'}`}>
                  <p className={`text-sm leading-relaxed ${message.role === 'user' ? 'text-white' : 'text-softform-text-secondary'}`}>{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {message.sources.map((source) => (
                        <span key={source} className="rounded-full bg-softform-mist-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] text-softform-teal-deep">
                          {source}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={onSubmit} className="border-t border-softform-navy-950/5 p-4 bg-white/70">
            <div className="flex gap-3">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask about valuation, funding readiness, macro risks, or advisor brief..."
                className="min-w-0 flex-1 rounded-xl border border-softform-aqua-300/25 bg-white px-4 py-3 text-sm text-softform-navy-950 outline-none focus:border-softform-teal-deep/50"
              />
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-softform-navy-900 px-4 py-3 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
              >
                <Send size={15} />
                Ask
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}
