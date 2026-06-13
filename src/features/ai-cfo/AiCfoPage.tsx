/* eslint-disable @typescript-eslint/no-explicit-any */
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
  Loader2,
  Play,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import SkeletonLoader from '../../components/platform/SkeletonLoader'
import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { getAdvisoryBlueprint, getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { getFundingChannelRanking, getRedFlagsMacroSummary } from '../market-watch/api/marketWatchApi'
import type { AdvisoryBlueprintResponse, CreditScoringResult } from '../advisory-blueprint/types'
import type { FinancialAnalysisResponse, FundingChannelRankingResponse, RedFlagsMacroSummaryResponse } from '../market-watch/types'
import { postChatQuestion, type AdvisoryChatSource } from './api/aiCfoApi'
import {
  triggerAnalysisRun,
  fetchAllRunStatuses,
  getRunStatusLabel,
  fetchBackendConfig,
} from '../../lib/workspaceRunHelpers'
import { API_BASE_URL } from '../../lib/apiBase'
import { useWorkspace } from '../../context/workspaceContext'

type AiMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: AdvisoryChatSource[]
  aiMode?: string
  disclaimer?: string
  warnings?: string[]
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

const renderMarkdown = (text: string, isUser: boolean = false) => {
  if (!text) return null;
  
  const lines = text.split('\n');
  const renderedElements: React.ReactNode[] = [];
  
  const textColor = isUser ? 'text-white' : 'text-softform-text-secondary';
  const headerColor = isUser ? 'text-white' : 'text-softform-navy-950';
  const strongColor = isUser ? 'text-white' : 'text-softform-navy-950';
  
  lines.forEach((line, index) => {
    const trimmed = line.trim();
    
    // Check if it's a list item
    const isListItem = trimmed.startsWith('- ') || trimmed.startsWith('* ');
    
    // Process formatting within a line (bold/italic)
    const processInline = (str: string) => {
      const parts = str.split('**');
      return parts.map((part, i) => {
        if (i % 2 === 1) {
          return <strong key={i} className={`font-bold ${strongColor}`}>{part}</strong>;
        }
        return part;
      });
    };

    if (trimmed.startsWith('### ')) {
      renderedElements.push(
        <h3 key={index} className={`text-sm font-bold mt-3 mb-1.5 first:mt-0 ${headerColor}`}>
          {processInline(trimmed.substring(4))}
        </h3>
      );
    } else if (trimmed.startsWith('## ')) {
      renderedElements.push(
        <h2 key={index} className={`text-base font-bold mt-4 mb-2 first:mt-0 ${headerColor}`}>
          {processInline(trimmed.substring(3))}
        </h2>
      );
    } else if (trimmed.startsWith('# ')) {
      renderedElements.push(
        <h1 key={index} className={`text-lg font-extrabold mt-5 mb-2.5 first:mt-0 ${headerColor}`}>
          {processInline(trimmed.substring(2))}
        </h1>
      );
    } else if (isListItem) {
      renderedElements.push(
        <li key={index} className={`ml-4 list-disc text-sm my-0.5 leading-relaxed ${textColor}`}>
          {processInline(trimmed.substring(2))}
        </li>
      );
    } else if (trimmed === '---' || trimmed === '***') {
      renderedElements.push(
        <hr key={index} className={`my-3 ${isUser ? 'border-white/20' : 'border-softform-navy-950/10'}`} />
      );
    } else if (trimmed === '') {
      renderedElements.push(<div key={index} className="h-1.5" />);
    } else {
      renderedElements.push(
        <p key={index} className={`text-sm leading-relaxed my-0.5 font-normal ${textColor}`}>
          {processInline(line)}
        </p>
      );
    }
  });
  
  return <div className="space-y-0.5">{renderedElements}</div>;
};

export default function AiCfoPage() {
  const { activeWorkspace } = useWorkspace()
  const [context, setContext] = useState<AiContext>({ financial: null, credit: null, funding: null, macro: null, blueprint: null })
  const [messages, setMessages] = useState<AiMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [latestAiMode, setLatestAiMode] = useState<string | null>(null)

  // Readiness gate states
  const [snapshot, setSnapshot] = useState<any>(null)
  const [runStatuses, setRunStatuses] = useState<Record<string, any | null>>({})
  const [hasSnapshot, setHasSnapshot] = useState<boolean | null>(null)
  const [isProdMode, setIsProdMode] = useState(false)
  const [runningType, setRunningType] = useState<string | null>(null)
  const [checkingReadiness, setCheckingReadiness] = useState(true)

  const { financial, credit, funding } = context
  const valuation = getValuation(financial)
  const topChannel = funding?.channels?.find((channel) => channel.key === funding.topChannelKey) ?? funding?.channels?.[0]

  const loadContext = async () => {
    setLoading(true)
    setCheckingReadiness(true)
    setError(null)
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) {
      setHasSnapshot(false)
      setCheckingReadiness(false)
      setLoading(false)
      return
    }

    try {
      // 1. Fetch backend config
      const config = await fetchBackendConfig()
      setIsProdMode(config.isProduction)

      // 2. Fetch active snapshot
      const snapshotRes = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/snapshot/active`, {
        headers: { 'x-workspace-id': workspaceId }
      })
      if (!snapshotRes.ok) {
        setHasSnapshot(false)
        setCheckingReadiness(false)
        setLoading(false)
        return
      }
      const snapshotData = await snapshotRes.json()
      setSnapshot(snapshotData)
      setHasSnapshot(true)

      // 3. Fetch run statuses
      const statuses = await fetchAllRunStatuses(workspaceId)
      setRunStatuses(statuses)

      // 4. Fetch legacy analyses context
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
          content: 'I have loaded the current CFO workspace context. Ask about valuation, credit readiness, funding strategy, macro risks, or the advisor-ready brief.',
        },
      ])
    } catch (e) {
      console.error('AI CFO context load failed', e)
      setError('AI CFO is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
      setCheckingReadiness(false)
    }
  }

  const handleTriggerRunInGate = async (runType: string) => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setRunningType(runType)
    try {
      await triggerAnalysisRun(workspaceId, runType)
      // Refresh statuses
      const statuses = await fetchAllRunStatuses(workspaceId)
      setRunStatuses(statuses)

      // Reload matching legacy data
      if (runType === 'financial_health' || runType === 'valuation') {
        const financial = await getFinancialHealthAnalysis().catch(() => null)
        setContext(prev => ({ ...prev, financial }))
      } else if (runType === 'credit_score') {
        const credit = await getCreditScore().catch(() => null)
        setContext(prev => ({ ...prev, credit }))
      } else if (runType === 'funding_strategy') {
        const funding = await getFundingChannelRanking().catch(() => null)
        setContext(prev => ({ ...prev, funding }))
      } else if (runType === 'advisory_blueprint') {
        const blueprint = await getAdvisoryBlueprint().catch(() => null)
        setContext(prev => ({ ...prev, blueprint }))
      }
    } catch (err: any) {
      console.error(`Failed to trigger run for ${runType}:`, err)
      alert(`Failed to run ${runType}: ${err.message || err}`)
    } finally {
      setRunningType(null)
    }
  }

  useEffect(() => {
    loadContext()
  }, [])

  const isInsufficientData = useMemo(() => {
    return (
      (context.financial && 'status' in context.financial && context.financial.status === 'insufficient_data') ||
      (context.credit && 'status' in context.credit && context.credit.status === 'insufficient_data') ||
      (context.blueprint && 'status' in context.blueprint && context.blueprint.status === 'insufficient_data') ||
      (context.funding && 'status' in context.funding && context.funding.status === 'insufficient_data')
    )
  }, [context])

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

  const submitQuestion = async (question: string) => {
    const trimmed = question.trim()
    if (!trimmed || chatLoading) return
    const userMessage: AiMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setChatLoading(true)
    setChatError(null)
    try {
      const response = await postChatQuestion({ question: trimmed })
      const assistantMessage: AiMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        aiMode: response.aiMode,
        disclaimer: response.disclaimer,
        warnings: response.warnings,
      }
      setMessages((prev) => [...prev, assistantMessage])
      setLatestAiMode(response.aiMode)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response from AI CFO.'
      setChatError(errorMessage)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Unable to get a response: ${errorMessage}. Please check the backend connection and try again.`,
          aiMode: 'error',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    submitQuestion(input)
  }

  if (loading || checkingReadiness) {
    return (
      <div className="space-y-8 pb-12">
        {/* Header Skeleton */}
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>

        {/* Cockpit Skeleton */}
        <SkeletonLoader variant="card" className="min-h-[200px]" />

        {/* 4 Metric Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SkeletonLoader variant="metric" count={4} />
        </div>

        {/* Double columns skeleton */}
        <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
          <SkeletonLoader variant="card" className="min-h-[350px]" />
          <SkeletonLoader variant="card" className="min-h-[350px]" />
        </div>
      </div>
    )
  }

  if (hasSnapshot === false) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="AI CFO"
          subtitle="Ask questions across the current financial, valuation, readiness, funding, market, and advisory context."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <BotMessageSquare size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">No Active Financial Snapshot</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              You need to select a workspace, upload financial statements, and compile an active financial snapshot before you can consult the AI CFO.
            </p>
          </div>
          <Link
            to="/platform/data-room"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-sm font-semibold rounded-full shadow-sm transition-colors"
          >
            <span>Go to Data Room</span>
            <ArrowRight size={14} />
          </Link>
        </div>
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

  if (isInsufficientData) {
    const missing = (context.financial && 'missingRequirements' in context.financial ? (context.financial.missingRequirements as string[]) : undefined) ||
                    (context.credit && 'missingRequirements' in context.credit ? (context.credit.missingRequirements as string[]) : undefined) ||
                    (context.blueprint && 'missingRequirements' in context.blueprint ? (context.blueprint.missingRequirements as string[]) : undefined) ||
                    (context.funding && 'missingRequirements' in context.funding ? (context.funding.missingRequirements as string[]) : undefined)
    const nextAct = (context.financial && 'nextActions' in context.financial ? (context.financial.nextActions as string[]) : undefined) ||
                    (context.credit && 'nextActions' in context.credit ? (context.credit.nextActions as string[]) : undefined) ||
                    (context.blueprint && 'nextActions' in context.blueprint ? (context.blueprint.nextActions as string[]) : undefined) ||
                    (context.funding && 'nextActions' in context.funding ? (context.funding.nextActions as string[]) : undefined)
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="AI CFO"
          subtitle="Ask questions across the current financial, valuation, readiness, funding, market, and advisory context."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={missing}
          nextActions={nextAct}
        />
      </div>
    )
  }

  const requiredKeys = ['financial_health', 'credit_score', 'funding_strategy', 'advisory_blueprint']
  const runLabels: Record<string, string> = {
    financial_health: 'Financial Health',
    valuation: 'Valuation',
    credit_score: 'Credit Readiness',
    funding_strategy: 'Funding Strategy',
    advisory_blueprint: 'Advisory Blueprint',
  }
  const completedCoreCount = requiredKeys.filter(key => getRunStatusLabel(runStatuses[key]) === 'completed').length
  const isReady = completedCoreCount === requiredKeys.length

  const renderContextNotReadyPanel = () => {
    return (
      <div className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm p-6 mb-8 w-full space-y-6">
        <div>
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 font-medium">AI CFO Context Readiness</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            {isProdMode 
              ? 'Required context runs are missing. In production mode, the AI CFO cannot start a consultation until the required workspace context is generated.' 
              : 'Some recommended context runs are missing. You can consult the AI CFO in local mode, but running all core analyses is recommended for accurate answers.'}
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[...requiredKeys, 'valuation'].map((key) => {
            const status = getRunStatusLabel(runStatuses[key])
            const label = runLabels[key]
            const isRequired = requiredKeys.includes(key)
            const isExecuting = runningType === key
            
            return (
              <div 
                key={key} 
                className={`flex items-center justify-between p-3.5 rounded-2xl border ${
                  status === 'completed' 
                    ? 'bg-emerald-50/20 dark:bg-emerald-950/5 border-emerald-100/30 dark:border-emerald-900/10' 
                    : isRequired 
                    ? 'bg-amber-50/20 dark:bg-amber-950/5 border-amber-100/30 dark:border-amber-900/10'
                    : 'bg-slate-50/30 dark:bg-slate-800/10 border-slate-150/40 dark:border-slate-800/30'
                }`}
              >
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 font-medium">
                    {label}
                  </span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium mt-0.5">
                    {status === 'completed' ? '✓ Ready' : isRequired ? '⚠ Required' : '○ Recommended'}
                  </span>
                </div>
                {status !== 'completed' && (
                  <button
                    onClick={() => handleTriggerRunInGate(key)}
                    disabled={!!runningType || loading}
                    className="flex items-center justify-center w-7 h-7 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-250 dark:border-slate-700 rounded-full shadow-sm hover:shadow transition-shadow disabled:opacity-55"
                    title="Run Analysis"
                  >
                    {isExecuting ? (
                      <Loader2 size={12} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
                    ) : (
                      <Play size={11} fill="currentColor" className="ml-0.5" />
                    )}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderContextBadge = () => {
    const runDates = requiredKeys.map(key => runStatuses[key]?.createdAt).filter(Boolean)
    const latestDate = runDates.length > 0 ? new Date(Math.max(...runDates.map(d => new Date(d).getTime()))).toLocaleString() : 'N/A'
    
    return (
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 px-4 py-2 bg-emerald-50/10 dark:bg-emerald-950/5 border border-emerald-100/30 dark:border-emerald-900/10 rounded-2xl text-[11px] text-emerald-800 dark:text-emerald-300 backdrop-blur-sm mb-4">
        <div className="flex items-center gap-1">
          <span className="font-semibold">Context Active:</span>
          <span>Snapshot {snapshot?.id ? `${snapshot.id.slice(0, 8)}...` : 'N/A'}</span>
        </div>
        <span className="hidden sm:inline text-slate-300 dark:text-slate-750">|</span>
        <div className="flex items-center gap-1">
          <span className="font-semibold">Runs Loaded:</span>
          <span>{completedCoreCount}/{requiredKeys.length} Core</span>
        </div>
        <span className="hidden sm:inline text-slate-300 dark:text-slate-750">|</span>
        <div>
          <span className="font-semibold">Freshness:</span> {latestDate}
        </div>
      </div>
    )
  }

  // Hard gate: in production, block consulting if not ready
  if (isProdMode && !isReady) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="AI CFO"
          subtitle="Ask questions across the current financial, valuation, readiness, funding, market, and advisory context."
          chip={<StatusChip variant="caution">Context not ready</StatusChip>}
        />
        {renderContextNotReadyPanel()}
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="AI CFO"
        subtitle="Ask questions across the current financial, valuation, readiness, funding, market, and advisory context."
        chip={
          activeWorkspace?.id === 'workspace_sample_novus' ? (
            <StatusChip variant="caution">Synthetic Demo Data</StatusChip>
          ) : (
            <StatusChip variant={isReady ? 'signal' : 'neutral'}>{isReady ? 'Context ready' : 'Context incomplete'}</StatusChip>
          )
        }
      />

      {/* Show context warning banner in dev/local mode if not ready */}
      {!isReady && renderContextNotReadyPanel()}

      {/* Digital CFO Assistant Hero Section in Premium Navy Contrast Card */}
      <section className="softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse">Digital CFO assistant</span>
            <h2 className="text-3xl font-semibold text-white tracking-tight flex items-center gap-2 flex-wrap">
              <span>{financial?.snapshot.companyName ?? 'Workspace Company'} · ask your CFO workspace</span>
              {activeWorkspace?.id === 'workspace_sample_novus' && (
                <span className="rounded-full bg-softform-amber-500/20 text-softform-amber-300 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider">
                  Synthetic Demo Data
                </span>
              )}
            </h2>
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              Ask questions across financial health, valuation, credit readiness, funding strategy, macro risks, and the advisory blueprint. Responses are powered by the configured advisory engine with visible sources.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Link to="/platform/reports" className="rounded-[22px] border border-white/10 bg-white/5 p-4 shadow-soft-inner hover-lift">
              <FileText size={18} className="text-softform-aqua-300 animate-pulse" />
              <p className="mt-3 text-sm font-semibold text-white">Reports</p>
              <p className="mt-1 text-xs text-white/70">Open CFO snapshot.</p>
            </Link>
            <Link to="/platform/advisory-blueprint" className="rounded-[22px] border border-white/10 bg-white/5 p-4 shadow-soft-inner hover-lift">
              <Sparkles size={18} className="text-softform-aqua-300 animate-pulse" />
              <p className="mt-3 text-sm font-semibold text-white">Blueprint</p>
              <p className="mt-1 text-xs text-white/70">Open advisor brief.</p>
            </Link>
          </div>
        </div>
      </section>

      {/* Metric cards context grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Readiness"
            value={credit?.compositeScore ?? 'N/A'}
            description={formatBand(credit?.fundingReadiness)}
            icon={<ShieldCheck size={16} className="text-softform-teal-500" />}
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Top channel"
            value={topChannel?.label ?? 'N/A'}
            description={formatBand(topChannel?.fitBand)}
            icon={<Landmark size={16} className="text-softform-teal-500" />}
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Financial band"
            value={formatBand(financial?.summary?.overallBand)}
            description={`Revenue ${formatHKD(financial?.snapshot.incomeStatement.revenue)}`}
            icon={<BotMessageSquare size={16} className="text-softform-teal-500" />}
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Valuation EV"
            value={formatHKD(valuation?.dcf?.enterpriseValue)}
            description={`WACC ${formatPercent(valuation?.wacc?.wacc)}`}
            icon={<Sparkles size={16} className="text-softform-teal-500" />}
          />
        </div>
      </section>

      {/* Suggested questions & Chat */}
      <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <SectionBlock
          title="Suggested questions"
          action={<StatusChip variant="neutral">Prompts</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => submitQuestion(prompt)}
                className="softform-action-card group w-full rounded-xl px-4 py-3 text-left hover-lift"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-softform-navy-950">{prompt}</span>
                  <ArrowRight size={14} className="mt-0.5 text-softform-teal-deep transition group-hover:translate-x-1 shrink-0" />
                </div>
              </button>
            ))}
          </div>
          <p className="text-[11px] leading-relaxed text-softform-text-muted mt-4">
            Local testing note: answers are generated locally from current app context, not from a production LLM service.
          </p>
        </SectionBlock>

        <div className="softform-card rounded-[28px] p-0 overflow-hidden flex flex-col justify-between h-full min-h-[500px]">
          <div>
            <div className="border-b border-softform-navy-950/5 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white/30">
              <h2 className="text-lg font-semibold text-softform-navy-950 flex items-center gap-2">
                <BotMessageSquare size={20} className="text-softform-teal-500 animate-pulse" />
                Conversation
              </h2>
              <div className="flex flex-wrap items-center gap-2">
                {latestAiMode && (
                  <span className={`rounded-full px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.1em] ${
                    latestAiMode === 'provider_configured' || latestAiMode === 'openai' || latestAiMode === 'azure_openai' || latestAiMode === 'google_ai'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300'
                      : latestAiMode === 'deterministic_fallback'
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-300'
                      : latestAiMode === 'provider_not_configured'
                      ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-300'
                  }`}>
                    {latestAiMode === 'provider_configured' || latestAiMode === 'openai' || latestAiMode === 'azure_openai' || latestAiMode === 'google_ai'
                      ? `AI Powered (${latestAiMode === 'google_ai' ? 'Gemini' : latestAiMode.replace('_', ' ')})`
                      : latestAiMode === 'deterministic_fallback'
                      ? 'Deterministic'
                      : latestAiMode === 'provider_not_configured'
                      ? 'No AI Provider'
                      : latestAiMode}
                  </span>
                )}
                {isReady && renderContextBadge()}
              </div>
            </div>

            <div className="max-h-[560px] overflow-y-auto px-6 py-5 space-y-4 bg-white/25">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[86%] rounded-[24px] px-5 py-4 ${message.role === 'user' ? 'softform-navy-card text-white' : 'softform-panel text-softform-text-secondary border border-white/75 shadow-sm'}`}>
                    <div className={`text-sm leading-relaxed ${message.role === 'user' ? 'text-white' : 'text-softform-navy-950 font-normal'}`}>
                      {renderMarkdown(message.content, message.role === 'user')}
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5 border-t border-softform-navy-950/5 pt-2">
                        {message.sources.map((source, idx) => (
                          <span
                            key={`${source.title}-${idx}`}
                            title={source.snippet ?? undefined}
                            className="rounded-full bg-softform-mist-100 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-softform-teal-deep cursor-help"
                          >
                            {source.title}{source.chunkIndex !== undefined && source.chunkIndex !== null ? ` (Chunk ${source.chunkIndex})` : ""}
                          </span>
                        ))}
                      </div>
                    )}
                    {message.warnings && message.warnings.length > 0 && (
                      <div className="mt-3 space-y-1 border-t border-amber-200/50 pt-2">
                        {message.warnings.map((warning, i) => (
                          <p key={i} className="text-[10px] text-amber-700 dark:text-amber-400 flex items-start gap-1.5">
                            <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                            <span>{warning}</span>
                          </p>
                        ))}
                      </div>
                    )}
                    {message.disclaimer && (
                      <div className="mt-2">
                        <p className="text-[9px] text-slate-400 dark:text-slate-500 italic leading-relaxed">
                          {message.disclaimer}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={onSubmit} className="border-t border-softform-navy-950/5 p-4 bg-white/70">
            {chatError && (
              <p className="mb-3 px-3 py-2 rounded-xl bg-red-50 dark:bg-red-950/10 border border-red-100 dark:border-red-900/20 text-[11px] text-red-700 dark:text-red-400 flex items-center gap-1.5">
                <AlertTriangle size={12} />
                {chatError}
              </p>
            )}
            <div className="flex gap-3">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask about valuation, funding readiness, macro risks, or advisor brief..."
                disabled={chatLoading}
                className="min-w-0 flex-1 rounded-xl border border-softform-aqua-300/25 bg-white px-4 py-3 text-sm text-softform-navy-950 outline-none focus:border-softform-teal-deep/50 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={chatLoading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-softform-navy-900 px-4 py-3 text-xs font-semibold text-white shadow-sm hover:bg-softform-navy-800 transition disabled:opacity-55 disabled:cursor-not-allowed"
              >
                {chatLoading ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Send size={15} />
                )}
                {chatLoading ? 'Thinking...' : 'Ask'}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}
