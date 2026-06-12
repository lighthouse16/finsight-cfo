/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import {
  FileText,
  ArrowRight,
  Database,
  Compass,
  TrendingUp,
  CheckSquare,
  Upload,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Activity,
  Check,
  Trash2,
  Sparkles,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import MetricDisplay from '../../components/platform/MetricDisplay'
import SourceInfoTooltip from '../market-watch/components/SourceInfoTooltip'
import WorkspaceSelector from '../../components/platform/WorkspaceSelector'
import WorkspaceRunReadiness from '../../components/platform/WorkspaceRunReadiness'
import {
  fetchWorkspaceFiles,
  uploadWorkspaceFile,
  buildWorkspaceSnapshot,
  fetchActiveWorkspaceSnapshot,
  deleteWorkspaceFile,
  UploadedFileRecord,
} from './api/dataRoomApi'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import { API_BASE_URL } from '../../lib/apiBase'
import { fetchBackendConfig, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'
import ReleaseOnboardingChecklist from '../../components/platform/ReleaseOnboardingChecklist'

type UploadState = {
  uploading: boolean
  error: string | null
}

const REQUIRED_SNAPSHOT_RECORD_KEYS = ['pl-statement', 'balance-sheet', 'cash-flow', 'debt-schedule'] as const

const SNAPSHOT_RECORD_LABELS: Record<string, string> = {
  'pl-statement': 'P&L Statement',
  'balance-sheet': 'Balance Sheet',
  'cash-flow': 'Cash Flow',
  'debt-schedule': 'Debt Schedule',
  'receivables-aging': 'Receivables Aging',
}

const CORE_RATIO_KEYS = [
  'currentRatio',
  'quickRatio',
  'interestCoverage',
  'dscr',
  'workingCapitalGap',
] as const

const formatRatioValue = (value: number | null | undefined, key: string) => {
  if (value === null || value === undefined) return '—'
  if (key === 'workingCapitalGap') return value.toLocaleString(undefined, { maximumFractionDigits: 0 })
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

interface DataRoomRecord {
  id: string
  name: string
  category: string
  purpose: string
  status: 'demo_available' | 'missing' | 'connected' | 'optional'
  requiredFor: string[]
  lastUpdated?: string | null
  actionLabel: string
  extractionStatus?: string
}

interface DataRoomResponse {
  records: DataRoomRecord[]
  dependencies: { recordGroup: string; outputs: string[] }[]
}

export default function DataRoomPage() {
  const [activeNotification, setActiveNotification] = useState<string | null>(null)
  
  // Workspace context state
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>(localStorage.getItem('active_workspace_id') || '')
  const [activeWorkspaceName, setActiveWorkspaceName] = useState<string>('')
  
  // Backend checklist & files state
  const [checklistTemplate, setChecklistTemplate] = useState<DataRoomResponse | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileRecord[]>([])
  const [isLoadingChecklist, setIsLoadingChecklist] = useState(true)
  
  // Upload states per record key
  const [uploadStates, setUploadStates] = useState<Record<string, UploadState>>({})
  
  // Snapshot & analysis states
  const [activeSnapshot, setActiveSnapshot] = useState<any>(null)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  
  // Build snapshot states
  const [isBuilding, setIsBuilding] = useState(false)
  const [buildError, setBuildError] = useState<string | null>(null)
  
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [isResetting, setIsResetting] = useState(false)
  const [showDemoHelper, setShowDemoHelper] = useState(false)
  const [isRunningWorkspaceAnalysis, setIsRunningWorkspaceAnalysis] = useState(false)

  const activeDataMode = useMemo(() => {
    if (!analysisResult?.snapshot) return 'demo_sample'
    const meta = analysisResult.snapshot.metadata
    if (meta?.source === 'workspace_persistent_snapshot' || meta?.persistent === true) {
      return 'persistent_workspace'
    }
    if (meta?.source === 'data_room_workspace_preview' || meta?.preview_only === true) {
      return 'preview_parsed'
    }
    return 'demo_sample'
  }, [analysisResult])

  const handleRunWorkspaceAnalysis = async () => {
    if (!activeWorkspaceId) return
    setIsRunningWorkspaceAnalysis(true)
    try {
      await triggerAnalysisRun(activeWorkspaceId, 'financial_health')
      await reloadWorkspaceData(activeWorkspaceId)
      setActiveNotification('Workspace financial health analysis run triggered and completed successfully.')
      setTimeout(() => setActiveNotification(null), 4000)
    } catch (err: any) {
      console.error(err)
      alert(err.message || 'Failed to trigger workspace financial analysis run.')
    } finally {
      setIsRunningWorkspaceAnalysis(false)
    }
  }

  const handleLoadDemoWorkspace = async () => {
    setIsResetting(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/workspaces/reset-sample`, {
        method: 'POST'
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail?.message || 'Failed to initialize sample workspace')
      }
      const data = await res.json()
      localStorage.setItem('active_workspace_id', data.workspaceId)
      setActiveWorkspaceId(data.workspaceId)
      window.dispatchEvent(new Event('workspaceChanged'))
      setActiveNotification('Sample company (Novus Retail Solutions Ltd) successfully initialized and pre-analyzed.')
      
      // Force refresh data
      await reloadWorkspaceData(data.workspaceId)
    } catch (err: any) {
      console.error(err)
      alert(err.message || 'Error initializing sample workspace')
    } finally {
      setIsResetting(false)
    }
  }

  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({})

  // Fetch workspaces list on mount to get active workspace metadata
  const fetchWorkspaceMeta = useCallback(async (wsId: string) => {
    if (!wsId) return
    try {
      const res = await fetch(`${API_BASE_URL}/api/workspaces/${wsId}`)
      if (res.ok) {
        const ws = await res.json()
        setActiveWorkspaceName(ws.companyName || ws.company_name || '')
      }
    } catch (err) {
      console.error('Failed to fetch workspace metadata', err)
    }
  }, [])

  // Load live files list from workspace
  const loadWorkspaceFiles = useCallback(async (wsId: string) => {
    if (!wsId) return
    try {
      const files = await fetchWorkspaceFiles(wsId)
      setUploadedFiles(files)
    } catch (err) {
      console.error('Failed to load workspace files', err)
    }
  }, [])

  // Load active snapshot metadata
  const loadActiveSnapshot = useCallback(async (wsId: string) => {
    if (!wsId) return
    try {
      const res = await fetchActiveWorkspaceSnapshot(wsId)
      if (res.status === 'success') {
        setActiveSnapshot(res.snapshot)
      } else {
        setActiveSnapshot(null)
      }
    } catch (err) {
      console.error('Failed to load active snapshot', err)
      setActiveSnapshot(null)
    }
  }, [])

  // Load live analysis parameters derived from snapshot
  const loadAnalysis = useCallback(async () => {
    try {
      const res = await getFinancialHealthAnalysis()
      if (res && !('status' in res && res.status === 'insufficient_data')) {
        setAnalysisResult(res)
      } else {
        setAnalysisResult(null)
      }
    } catch (err) {
      console.error('Failed to load financial analysis', err)
      setAnalysisResult(null)
    }
  }, [])

  // Combined function to reload everything for the active workspace
  const reloadWorkspaceData = useCallback(async (wsId: string) => {
    if (!wsId) return
    setIsLoadingChecklist(true)
    await Promise.all([
      fetchWorkspaceMeta(wsId),
      loadWorkspaceFiles(wsId),
      loadActiveSnapshot(wsId),
      loadAnalysis(),
    ])
    setIsLoadingChecklist(false)
  }, [fetchWorkspaceMeta, loadWorkspaceFiles, loadActiveSnapshot, loadAnalysis])

  // Fetch checklist template definition once
  useEffect(() => {
    const fetchChecklistTemplate = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/data-room/readiness-template`)
        if (res.ok) {
          const data = await res.json()
          setChecklistTemplate(data)
        }
      } catch (err) {
        console.error('Failed to load readiness checklist template', err)
      }
    }
    const checkConfig = async () => {
      try {
        const config = await fetchBackendConfig()
        setShowDemoHelper(!config.isProduction)
      } catch (e) {
        console.warn('Failed to load backend config:', e)
      }
    }
    fetchChecklistTemplate()
    checkConfig()
  }, [])

  // Load workspace data when active workspace changes
  useEffect(() => {
    if (activeWorkspaceId) {
      reloadWorkspaceData(activeWorkspaceId)
    }
  }, [activeWorkspaceId, reloadWorkspaceData])

  // Listen to workspaceChanged custom events
  useEffect(() => {
    const handleWorkspaceChanged = () => {
      const nextId = localStorage.getItem('active_workspace_id') || ''
      setActiveWorkspaceId(nextId)
    }
    window.addEventListener('workspaceChanged', handleWorkspaceChanged)
    return () => window.removeEventListener('workspaceChanged', handleWorkspaceChanged)
  }, [])

  // Map checklist records with real workspace file records
  const computedRecords = useMemo(() => {
    const records = checklistTemplate?.records ?? []
    return records.map((rec) => {
      const uploaded = uploadedFiles.find((f) => f.recordKey === rec.id)
      if (uploaded) {
        return {
          ...rec,
          status: 'connected' as const,
          lastUpdated: `Uploaded ${new Date(uploaded.uploadedAt).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}`,
          actionLabel: 'Upload' as const, // Support re-upload/overwrite
          extractionStatus: uploaded.status,
          fileName: uploaded.fileName,
          parserStatus: uploaded.parserStatus || (uploaded as any).parser_status,
          recordCount: uploaded.recordCount || (uploaded as any).record_count,
          warnings: uploaded.warnings || [],
        }
      }
      return {
        ...rec,
        status: rec.status === 'optional' ? ('optional' as const) : ('missing' as const),
        lastUpdated: rec.status === 'optional' ? 'Not Connected' : 'Pending Record Connection',
        actionLabel: rec.id === 'pl-statement' || rec.id === 'balance-sheet' || rec.id === 'cash-flow' ? ('Upload' as const) : rec.actionLabel,
      }
    })
  }, [checklistTemplate?.records, uploadedFiles])

  // Computed metrics
  const totalRequired = useMemo(
    () => computedRecords.filter((rec) => rec.category !== 'Risk & Treasury' && (rec.status as string) !== 'optional').length,
    [computedRecords]
  )
  const connectedRequired = useMemo(
    () => computedRecords.filter((rec) => rec.status === 'connected' && (rec.status as string) !== 'optional').length,
    [computedRecords]
  )
  const missingRequired = useMemo(
    () => computedRecords.filter((rec) => rec.status === 'missing' && (rec.status as string) !== 'optional').length,
    [computedRecords]
  )
  const readinessPercentage = useMemo(
    () => (totalRequired ? Math.round((connectedRequired / totalRequired) * 100) : 0),
    [totalRequired, connectedRequired]
  )

  const locallyMissingRequiredStatements = useMemo(() => {
    return REQUIRED_SNAPSHOT_RECORD_KEYS.filter(
      (key) => !uploadedFiles.some((f) => f.recordKey === key)
    )
  }, [uploadedFiles])

  // Trigger file dialog
  const handleUploadClick = useCallback((recordId: string) => {
    fileInputRefs.current[recordId]?.click()
  }, [])

  // Upload file physically
  const handleFileSelected = useCallback(
    async (record: DataRoomRecord, event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      if (!activeWorkspaceId) {
        alert('Please select or create a workspace first.')
        return
      }

      setUploadStates((prev) => ({
        ...prev,
        [record.id]: { uploading: true, error: null },
      }))

      try {
        await uploadWorkspaceFile(activeWorkspaceId, record.id, file)
        
        // Reload workspace records and files
        await loadWorkspaceFiles(activeWorkspaceId)
        
        setUploadStates((prev) => ({
          ...prev,
          [record.id]: { uploading: false, error: null },
        }))

        setActiveNotification(`Successfully uploaded "${file.name}" to workspace.`)
        setTimeout(() => setActiveNotification(null), 4000)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Upload failed.'
        setUploadStates((prev) => ({
          ...prev,
          [record.id]: { uploading: false, error: message },
        }))
      }

      // Reset the file input
      event.target.value = ''
    },
    [activeWorkspaceId, loadWorkspaceFiles]
  )

  // Delete file physically
  const handleDeleteFile = useCallback(
    async (recordId: string) => {
      if (!activeWorkspaceId) return
      
      const fileRecord = uploadedFiles.find((f) => f.recordKey === recordId)
      if (!fileRecord) return

      if (!confirm(`Are you sure you want to delete the uploaded file for ${SNAPSHOT_RECORD_LABELS[recordId] || recordId}?`)) {
        return
      }

      try {
        await deleteWorkspaceFile(activeWorkspaceId, fileRecord.id)
        
        // Reload workspace records and files
        await reloadWorkspaceData(activeWorkspaceId)
        
        setActiveNotification(`Successfully deleted statement file.`)
        setTimeout(() => setActiveNotification(null), 4000)
      } catch (err) {
        console.error(err)
        alert(err instanceof Error ? err.message : 'Failed to delete file.')
      }
    },
    [activeWorkspaceId, uploadedFiles, reloadWorkspaceData]
  )

  // Compile active financial snapshot
  const handleBuildSnapshot = async () => {
    if (!activeWorkspaceId) return
    setIsBuilding(true)
    setBuildError(null)
    try {
      const res = await buildWorkspaceSnapshot(activeWorkspaceId)
      if (res.status === 'success') {
        setActiveNotification('Workspace financial snapshot compiled successfully!')
        setTimeout(() => setActiveNotification(null), 4000)
        // Refresh all workspace status
        await reloadWorkspaceData(activeWorkspaceId)
      } else {
        setBuildError(res.warnings?.join(', ') || 'Failed to compile snapshot. Verify uploaded statement data formats.')
      }
    } catch (err) {
      console.error(err)
      setBuildError(err instanceof Error ? err.message : 'Failed to connect to snapshot builder.')
    } finally {
      setIsBuilding(false)
    }
  }

  const handleActionClick = (recordName: string, action: string) => {
    setActiveNotification(
      `Connector simulated: "${action}" for ${recordName}. Direct live connector requires enterprise bank integration.`
    )
    setTimeout(() => {
      setActiveNotification(null)
    }, 6000)
  }

  const filteredRecords = useMemo(() => {
    return computedRecords.filter((rec) => selectedCategory === 'All' || rec.category === selectedCategory)
  }, [computedRecords, selectedCategory])

  const dependencies = checklistTemplate?.dependencies ?? []

  const getStatusChipVariant = (status: string) => {
    switch (status) {
      case 'connected':
        return 'signal'
      case 'missing':
        return 'caution'
      case 'optional':
      default:
        return 'neutral'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'missing':
        return 'Missing'
      case 'optional':
        return 'Optional'
      default:
        return status
    }
  }

  if (!activeWorkspaceId) {
    return (
      <div className="space-y-8 pb-12">
        {/* 1. Page Header */}
        <PageHeader
          title="Data Room"
          subtitle="Manage company financial records and upload statements for workspace calibration."
          actions={
            <div className="flex items-center gap-3">
              {showDemoHelper && (
                <button
                  onClick={handleLoadDemoWorkspace}
                  disabled={isResetting}
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-white/70 bg-white/60 hover:bg-white text-softform-navy-950 text-xs font-semibold rounded-xl shadow-sm disabled:opacity-50 transition-colors"
                  title="Safe developer helper to reset and populate sample company statements."
                >
                  {isResetting ? (
                    <Loader2 size={13} className="animate-spin text-softform-teal-deep" />
                  ) : (
                    <Sparkles size={13} className="text-softform-teal-deep" />
                  )}
                  <span>Initialize Sample Workspace</span>
                </button>
              )}
              <WorkspaceSelector />
            </div>
          }
        />
        <div className="softform-panel relative overflow-hidden rounded-[32px] p-8 sm:p-10 shadow-floating-panel bg-[linear-gradient(145deg,rgba(255,255,255,0.76),rgba(231,240,244,0.66))] border border-white">
          <div className="mx-auto flex max-w-lg flex-col items-center text-center relative z-10 py-8">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-[20px] bg-softform-mist-100/80 text-softform-amber-500 ring-4 ring-softform-aqua-300/10 shadow-soft-inner">
              <Database size={28} strokeWidth={1.5} />
            </div>
            <h2 className="mb-2 text-lg font-bold text-softform-navy-950">No Workspace Selected</h2>
            <p className="mb-6 text-sm leading-relaxed text-softform-text-secondary">
              To upload financial statements and compile calibration snapshots, you must select an existing workspace or create a new one.
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <span className="text-xs text-softform-text-muted">Use the workspace menu to select or create a workspace:</span>
              <WorkspaceSelector />
              {showDemoHelper && (
                <>
                  <span className="text-xs text-softform-text-muted">or</span>
                  <button
                    onClick={handleLoadDemoWorkspace}
                    disabled={isResetting}
                    className="inline-flex items-center gap-1.5 px-4 py-2 border border-white/70 bg-white/60 hover:bg-white text-softform-navy-950 text-xs font-semibold rounded-xl shadow-sm disabled:opacity-50 transition-colors"
                    title="Safe developer helper to reset and populate sample company statements."
                  >
                    {isResetting ? (
                      <Loader2 size={13} className="animate-spin text-softform-teal-deep" />
                    ) : (
                      <Sparkles size={13} className="text-softform-teal-deep" />
                    )}
                    <span>Initialize Sample Workspace</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Page Header */}
      <PageHeader
        title="Data Room"
        subtitle="Manage company financial records and upload statements for workspace calibration."
        titleAddon={
          <SourceInfoTooltip
            title="Data Room Ingestion"
            sources={[
              { label: 'Workspace Files Storage', mode: 'workspace-derived' },
              { label: 'Calculated Financial Context', mode: 'workspace-derived' },
            ]}
            ariaLabel="Data room source information"
          />
        }
        chip={
          <StatusChip variant={readinessPercentage === 100 ? 'signal' : 'caution'}>
            {activeWorkspaceName ? `${activeWorkspaceName}: ` : ''}{readinessPercentage}% Uploaded
          </StatusChip>
        }
        actions={
          <div className="flex items-center gap-3">
            {showDemoHelper && (
              <button
                onClick={handleLoadDemoWorkspace}
                disabled={isResetting}
                className="inline-flex items-center gap-1.5 px-4 py-2 border border-white/70 bg-white/60 hover:bg-white text-softform-navy-950 text-xs font-semibold rounded-xl shadow-sm disabled:opacity-50 transition-colors"
                title="Safe developer helper to reset and populate sample company statements."
              >
                {isResetting ? (
                  <Loader2 size={13} className="animate-spin text-softform-teal-deep" />
                ) : (
                  <Sparkles size={13} className="text-softform-teal-deep" />
                )}
                <span>Initialize Sample Workspace</span>
              </button>
            )}
            <WorkspaceSelector />
          </div>
        }
      />

      {/* State Notification Toast */}
      <AnimatePresence>
        {activeNotification && (
          <div className="fixed bottom-6 right-6 z-50 max-w-md rounded-2xl border border-white/60 bg-white/95 p-4 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-xl transition-all duration-300">
            <div className="flex gap-3">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-softform-teal-50 text-softform-teal-600">
                <Check size={12} />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-softform-navy-950">Data Room System</p>
                <p className="text-xs text-softform-text-secondary leading-relaxed">
                  {activeNotification}
                </p>
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. Active Data Mode Banner */}
      <div className="rounded-[24px] border border-white bg-white/70 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-floating-panel">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-softform-text-muted uppercase tracking-[0.14em]">
              Active Data Engine Mode
            </span>
            {activeDataMode === 'persistent_workspace' && (
              <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 border border-emerald-500/20">
                Persistent Workspace Active
              </span>
            )}
            {activeDataMode === 'preview_parsed' && (
              <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-600 border border-amber-500/20">
                Temporary Preview Active
              </span>
            )}
            {activeDataMode === 'demo_sample' && (
              <span className="inline-flex items-center rounded-full bg-slate-500/10 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-500/20">
                Demo Sample Active
              </span>
            )}
          </div>
          <p className="text-sm text-softform-navy-950 font-semibold">
            {activeDataMode === 'persistent_workspace' && `Displaying persisted records for ${activeWorkspaceName || 'Workspace'}.`}
            {activeDataMode === 'preview_parsed' && "Displaying temporary in-memory preview. Build active snapshot to persist."}
            {activeDataMode === 'demo_sample' && "Displaying default sample records (Harbour & Finch fallback). Select a workspace to persist uploaded data."}
          </p>
          <p className="text-xs text-softform-text-secondary">
            {activeDataMode === 'persistent_workspace' && "All outcome modules are fully calibrated against your uploaded CSV/XLSX statements."}
            {activeDataMode === 'preview_parsed' && "Projections and diagnostic models will revert to default demo templates when the backend process restarts."}
            {activeDataMode === 'demo_sample' && "Create a workspace and upload financial files to calibrate outcomes against actual SME performance."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            onClick={handleBuildSnapshot}
            disabled={isBuilding || locallyMissingRequiredStatements.length > 0}
            className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-softform-navy-800 disabled:cursor-not-allowed disabled:opacity-45 shadow-sm"
          >
            {isBuilding ? <Loader2 size={12} className="animate-spin" /> : <Database size={12} />}
            <span>Save as active workspace financial snapshot</span>
          </button>
          <button
            onClick={handleRunWorkspaceAnalysis}
            disabled={isRunningWorkspaceAnalysis || !activeSnapshot}
            className="inline-flex items-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-xs font-semibold text-softform-navy-950 hover:bg-white disabled:cursor-not-allowed disabled:opacity-45 shadow-sm transition"
          >
            {isRunningWorkspaceAnalysis ? <Loader2 size={12} className="animate-spin" /> : <Activity size={12} className="text-softform-teal-deep" />}
            <span>Run workspace financial analysis</span>
          </button>
        </div>
      </div>
      {/* Responsive Grid Layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_380px] items-start">
        {/* Left Column (Main Content) */}
        <div className="space-y-6">
          <section className="grid gap-4 sm:grid-cols-4">
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Workspace Required Records"
            value={totalRequired}
            description="Core statements checklist"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Uploaded Records"
            value={connectedRequired}
            description="Statements stored in workspace"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Missing Records"
            value={missingRequired}
            description="Awaiting ingestion"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Ingestion Readiness"
            value={`${readinessPercentage}%`}
            description="Active snapshot threshold"
          />
        </div>
      </section>

      {/* 3. Required Records Checklist */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex flex-col gap-4 border-b border-softform-navy-950/5 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-softform-navy-950">Ingestion Status</h2>
            <span className="text-xs font-medium text-softform-text-muted">
              {isLoadingChecklist ? 'Syncing files...' : 'Required statements upload tracker'}
            </span>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-2 pt-1">
            {['All', 'Core Financials', 'Debt & Credit', 'Commercial & Trade', 'Risk & Treasury'].map((cat) => {
              const isActive = selectedCategory === cat
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border shadow-sm ${
                    isActive
                      ? 'bg-softform-navy-900 border-softform-navy-950/10 text-white hover:bg-softform-navy-800'
                      : 'bg-white/70 border-white/60 text-softform-text-secondary hover:bg-white/95'
                  }`}
                >
                  {cat}
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex flex-col gap-4">
          {filteredRecords.map((rec) => {
            const uploadState = uploadStates[rec.id]
            const isConnected = rec.status === 'connected'
            const isMissing = rec.status === 'missing'

            return (
              <div
                key={rec.id}
                className="relative rounded-[24px] border border-white/60 bg-white/45 p-5 sm:p-6 shadow-base-card hover-lift transition-all duration-300 overflow-hidden"
              >
                {/* Left indicator strip */}
                <div
                  className={`absolute left-0 top-0 bottom-0 w-1.5 ${
                    isConnected
                      ? 'bg-softform-teal-500'
                      : isMissing
                        ? 'bg-softform-amber-500'
                        : 'bg-softform-text-muted/30'
                  }`}
                />

                {/* Hidden file input for Upload records */}
                {rec.actionLabel === 'Upload' && (
                  <input
                    ref={(el) => {
                      fileInputRefs.current[rec.id] = el
                    }}
                    type="file"
                    id={`file-input-${rec.id}`}
                    name={`file-input-${rec.id}`}
                    accept=".csv,.xlsx,.pdf,.docx"
                    aria-label={`Upload statement for ${rec.name}`}
                    className="sr-only"
                    onChange={(e) => handleFileSelected(rec, e)}
                  />
                )}

                <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr_1.2fr] gap-6 items-start">
                  {/* Col 1: Icon & Info */}
                  <div className="flex items-start gap-4">
                    <div
                      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-[14px] border shadow-sm ${
                        isConnected
                          ? 'bg-softform-teal-500/10 border-softform-teal-500/20 text-softform-teal-deep'
                          : isMissing
                            ? 'bg-softform-amber-500/10 border-softform-amber-500/20 text-softform-amber-500'
                            : 'bg-softform-mist-100/60 border-softform-aqua-300/10 text-softform-text-muted'
                      }`}
                    >
                      {isConnected ? (
                        <CheckSquare size={20} strokeWidth={2} />
                      ) : isMissing ? (
                        <AlertCircle size={20} strokeWidth={2} />
                      ) : (
                        <FileText size={20} strokeWidth={2} />
                      )}
                    </div>

                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-softform-navy-950 text-base leading-tight">
                          {rec.name}
                        </h3>
                        <span className="inline-flex items-center rounded-md bg-white/60 px-2 py-0.5 text-[10px] font-medium text-softform-text-secondary border border-white/85 shadow-sm">
                          {rec.category}
                        </span>
                      </div>
                      <p className="text-xs text-softform-text-secondary leading-relaxed max-w-xl">
                        {rec.purpose}
                      </p>
                      
                      {isConnected && (
                        <div className="mt-2 space-y-1 rounded-xl bg-white/40 border border-white/60 p-2.5">
                          <p className="text-xs text-softform-navy-900 font-semibold truncate flex items-center gap-1.5">
                            <FileText size={12} className="text-softform-teal-deep" />
                            <span>File: {(rec as any).fileName}</span>
                          </p>
                          
                          {/* Parser Status */}
                          <div className="flex items-center gap-2 text-[10px] font-semibold pt-0.5">
                            {(rec as any).parserStatus === 'parsed' && (
                              <span className="text-emerald-600 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                                Parsed successfully ({(rec as any).recordCount} rows)
                              </span>
                            )}
                            {(rec as any).parserStatus === 'unsupported_without_ocr' && (
                              <span className="text-amber-600 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                                Accepted Metadata (PDF/Word requires OCR)
                              </span>
                            )}
                            {(rec as any).parserStatus === 'unsupported_type' && (
                              <span className="text-red-600 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                Unsupported File Type
                              </span>
                            )}
                            {(rec as any).parserStatus === 'failed' && (
                              <span className="text-red-600 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                Parsing Failed
                              </span>
                            )}
                          </div>

                          {/* Parser status specific details */}
                          {(rec as any).parserStatus === 'unsupported_without_ocr' && (
                            <p className="text-[10px] text-softform-text-secondary leading-relaxed mt-1">
                              <strong>Next Action:</strong> PDF statement text parsing and OCR are disabled in this build. Please convert to structured CSV or XLSX and upload.
                            </p>
                          )}

                          {/* Parser warnings */}
                          {(rec as any).warnings && (rec as any).warnings.length > 0 && (
                            <div className="mt-1 space-y-0.5">
                              {(rec as any).warnings.map((warn: string, wIdx: number) => (
                                <p key={wIdx} className="text-[10px] text-softform-amber-500 font-semibold flex items-start gap-1">
                                  <AlertCircle size={10} className="shrink-0 mt-0.5" />
                                  <span>{warn}</span>
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Col 2: Dependency Fits */}
                  <div className="space-y-2 lg:pl-4">
                    <span className="block text-[10px] font-medium uppercase tracking-[0.12em] text-softform-text-muted">
                      Feeds outcome engines
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {rec.requiredFor.map((rf) => (
                        <span
                          key={rf}
                          className="inline-block rounded-lg bg-softform-mist-100/50 px-2.5 py-1 text-[10px] text-softform-teal-deep font-semibold border border-softform-aqua-300/10 uppercase tracking-[0.05em]"
                        >
                          {rf}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Col 3: Status & Action Control */}
                  <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between lg:justify-start gap-4 lg:gap-3 lg:text-right w-full">
                    <div className="space-y-1">
                      <StatusChip variant={getStatusChipVariant(rec.status)}>
                        {getStatusLabel(rec.status)}
                      </StatusChip>
                      {rec.extractionStatus && rec.extractionStatus !== 'parsed_structured' && (
                        <div className="mt-1">
                          {rec.extractionStatus === 'parsed_pdf_text_layer' && <StatusChip variant="signal">Parsed PDF Text</StatusChip>}
                          {rec.extractionStatus === 'parsed_docx_text' && <StatusChip variant="signal">Parsed DOCX</StatusChip>}
                          {rec.extractionStatus === 'ocr_provider_not_configured' && <StatusChip variant="caution">OCR Unavailable</StatusChip>}
                          {rec.extractionStatus === 'ocr_provider_configured' && <StatusChip variant="caution">Review Required</StatusChip>}
                          {rec.extractionStatus === 'unsupported' && <StatusChip variant="caution">Unsupported</StatusChip>}
                          {rec.extractionStatus === 'validation_warning' && <StatusChip variant="caution">Review Required</StatusChip>}
                        </div>
                      )}
                      {rec.extractionStatus && ['ocr_provider_not_configured', 'ocr_provider_configured', 'unsupported', 'validation_warning'].includes(rec.extractionStatus) && (
                        <p className="hidden lg:block text-[10px] text-softform-amber-500 font-semibold mt-1">
                          Try uploading CSV/XLSX
                        </p>
                      )}
                      {rec.lastUpdated && (
                        <p className="hidden lg:block text-[10px] text-softform-text-muted/80 mt-1">
                          {rec.lastUpdated}
                        </p>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-1 shrink-0">
                      {rec.actionLabel === 'Upload' ? (
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleUploadClick(rec.id)}
                            disabled={uploadState?.uploading}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 border-softform-navy-950/10 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-softform-navy-800 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 shadow-sm"
                          >
                            {uploadState?.uploading ? (
                              <Loader2 size={12} className="animate-spin" />
                            ) : (
                              <Upload size={12} />
                            )}
                            {isConnected ? 'Replace File' : uploadState?.uploading ? 'Uploading...' : 'Upload statement'}
                          </button>
                          {isConnected && (
                            <button
                              type="button"
                              onClick={() => handleDeleteFile(rec.id)}
                              className="inline-flex items-center justify-center h-8 w-8 rounded-xl bg-white border border-white/60 text-softform-amber-500 hover:bg-red-50 hover:text-red-600 hover:-translate-y-0.5 transition shadow-sm"
                              title="Delete file"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleActionClick(rec.name, rec.actionLabel)}
                          className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold transition border shadow-sm ${
                            rec.actionLabel === 'Connect'
                              ? 'bg-white border-white/60 text-softform-navy-950 hover:bg-white hover:-translate-y-0.5'
                              : 'bg-white/40 border-white/30 text-softform-text-muted cursor-not-allowed'
                          }`}
                          disabled={rec.actionLabel === 'Coming soon'}
                        >
                          {rec.actionLabel}
                        </button>
                      )}
                      {rec.lastUpdated && (
                        <p className="block lg:hidden text-[10px] text-softform-text-muted/80">
                          {rec.lastUpdated}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Inline Error drawer */}
                {uploadState?.error && (
                  <div className="mt-4 pt-4 border-t border-softform-navy-950/5">
                    <div className="rounded-[18px] border border-softform-amber-500/20 bg-softform-cream/30 p-4 space-y-1">
                      <div className="flex items-center gap-1.5">
                        <AlertCircle size={14} className="text-softform-amber-500" />
                        <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-softform-text-secondary">
                          Upload Failed
                        </span>
                      </div>
                      <p className="text-xs text-softform-amber-500 leading-relaxed font-semibold">
                        {uploadState.error}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* 4. Financial Snapshot Calibration & Preview */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex flex-col gap-3 border-b border-softform-navy-950/5 pb-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-softform-teal-deep" />
              <h2 className="text-lg font-semibold text-softform-navy-950">Financial Snapshot Calibration</h2>
            </div>
            <p className="text-xs text-softform-text-muted leading-relaxed">
              Compile uploaded financial statements into a unified balance sheet and income statement model.
            </p>
            {activeSnapshot ? (
              <p className="text-[11px] text-softform-teal-deep font-semibold">
                Active workspace snapshot: Period {activeSnapshot.reportingPeriod || 'FY2025'} ({activeSnapshot.currency || 'HKD'}) is compiled and validated.
              </p>
            ) : (
              <p className="text-[11px] text-softform-amber-500 font-semibold">
                No active financial snapshot built for this workspace yet. Upload statements to compile calibration models.
              </p>
            )}
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <StatusChip variant={activeSnapshot ? 'signal' : 'caution'}>
              {activeSnapshot ? 'Snapshot Compiled' : 'Pending Ingestion'}
            </StatusChip>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted/90">
              Uploaded statements
            </p>
            <p className="text-2xl font-bold text-softform-navy-950 tabular-finance">
              {uploadedFiles.filter(f => REQUIRED_SNAPSHOT_RECORD_KEYS.includes(f.recordKey as any)).length}/{REQUIRED_SNAPSHOT_RECORD_KEYS.length}
            </p>
            <p className="text-xs text-softform-text-secondary">Core required sheets uploaded</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted/90">
              Integrity check checks
            </p>
            <p className="text-2xl font-bold text-softform-teal-deep tabular-finance">
              {analysisResult?.integrityChecks ? analysisResult.integrityChecks.filter((check: any) => check.passed).length : 0}
            </p>
            <p className="text-xs text-softform-text-secondary">Checks passed in active analysis</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted/90">
              Calculated warnings
            </p>
            <p className="text-2xl font-bold text-softform-amber-500 tabular-finance">
              {analysisResult?.warnings ? analysisResult.warnings.length : 0}
            </p>
            <p className="text-xs text-softform-text-secondary">System ratio warnings reported</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted/90">
              Ratios generated
            </p>
            <p className="text-2xl font-bold text-softform-navy-950 tabular-finance">
              {analysisResult?.ratios ? Object.keys(analysisResult.ratios).length : 0}
            </p>
            <p className="text-xs text-softform-text-secondary">Ratio metrics generated</p>
          </div>
        </div>

        {locallyMissingRequiredStatements.length > 0 && (
          <div className="rounded-2xl border border-softform-navy-950/5 bg-white/35 px-4 py-3 text-xs text-softform-text-secondary">
            <span className="font-semibold text-softform-navy-950">Missing required core statements for calibration:</span>{' '}
            {locallyMissingRequiredStatements.map((recordKey) => SNAPSHOT_RECORD_LABELS[recordKey] ?? recordKey).join(', ')}
          </div>
        )}

        {/* Compile Snapshot trigger button */}
        <div className="flex justify-between items-center bg-softform-mist-100/35 border border-softform-aqua-300/25 p-4 rounded-[22px] gap-4">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-softform-navy-950">Compile Active Workspace Snapshot</p>
            <p className="text-[11px] text-softform-text-secondary">
              Parses the uploaded templates, runs accounting validation checks, and publishes models to outcomes dashboard.
            </p>
          </div>
          <button
            type="button"
            onClick={handleBuildSnapshot}
            disabled={isBuilding || locallyMissingRequiredStatements.length > 0}
            className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-softform-navy-800 disabled:cursor-not-allowed disabled:opacity-45 shadow-sm"
          >
            {isBuilding ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Database size={12} />
            )}
            {isBuilding ? 'Compiling snapshot...' : 'Compile Snapshot'}
          </button>
        </div>

        {buildError && (
          <div className="flex items-start gap-2 rounded-2xl border border-softform-amber-500/20 bg-softform-cream/30 px-4 py-3 text-xs text-softform-amber-500 font-semibold">
            <AlertCircle size={14} className="mt-0.5 shrink-0" />
            <span>{buildError}</span>
          </div>
        )}

        {analysisResult && (
          <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
            <div className="rounded-[22px] border border-white/60 bg-white/40 p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-softform-teal-deep" />
                <h3 className="text-sm font-semibold text-softform-navy-950">Snapshot Validation Checks</h3>
              </div>
              <div className="space-y-2">
                {analysisResult.integrityChecks.slice(0, 4).map((check: any) => (
                  <div key={check.checkName} className="rounded-xl bg-white/45 px-3 py-2 text-xs">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-softform-navy-950">{check.checkName}</span>
                      <StatusChip variant={check.passed ? 'signal' : 'caution'}>
                        {check.passed ? 'Passed' : 'Review'}
                      </StatusChip>
                    </div>
                    <p className="mt-1 text-softform-text-secondary leading-relaxed">{check.message}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[22px] border border-white/60 bg-white/40 p-5 space-y-3">
              <h3 className="text-sm font-semibold text-softform-navy-950">Workspace Ratio Engine Calibration</h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {CORE_RATIO_KEYS.map((ratioKey) => {
                  const ratio = analysisResult.ratios?.[ratioKey]
                  return (
                    <div key={ratioKey} className="rounded-xl bg-white/45 px-3 py-2">
                      <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-softform-text-muted">
                        {ratio?.label ?? ratioKey}
                      </p>
                      <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">
                        {formatRatioValue(ratio?.value, ratioKey)}
                      </p>
                      {ratio?.warning && (
                        <p className="mt-1 text-[11px] font-medium text-softform-amber-500">{ratio.warning}</p>
                      )}
                    </div>
                  )
                })}
              </div>
              <p className="text-[11px] text-softform-text-muted leading-relaxed">
                Calibration is workspace-derived. Projections and valuations recalculate dynamically based on active statements.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Analysis Run Status */}
      {activeSnapshot && (
        <section className="flex justify-center">
          <WorkspaceRunReadiness
            workspaceId={activeWorkspaceId}
            onStatusChange={() => {
              if (activeWorkspaceId) {
                reloadWorkspaceData(activeWorkspaceId)
              }
            }}
          />
        </section>
      )}

      {/* 5. Analysis Dependency Map */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-semibold text-softform-navy-950">Analysis Dependency Mapping</h2>
          <p className="text-xs text-softform-text-muted mt-1">
            Understanding how integrated documents feed the advisory models
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {dependencies.map((feed: any) => (
            <div
              key={feed.recordGroup}
              className="p-5 rounded-[22px] bg-white/40 border border-white/60 shadow-sm space-y-4 hover-lift"
            >
              <h3 className="font-semibold text-softform-navy-950 text-sm leading-snug">
                {feed.recordGroup}
              </h3>
              <div className="h-[1px] bg-softform-navy-950/5" />
              <div className="space-y-2">
                <span className="text-[9px] font-medium text-softform-text-muted/90 uppercase tracking-[0.14em]">
                  Feeds Engine Outcomes
                </span>
                <ul className="space-y-2 pt-1">
                  {feed.outputs.map((out: string, oIdx: number) => (
                    <li key={oIdx} className="text-xs text-softform-text-secondary flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-softform-teal-deep/70 shrink-0" />
                      <span className="font-medium text-softform-navy-900/90">{out}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 6. Active Workspace Environment Details */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-5">
        <h2 className="text-base font-semibold text-softform-navy-950">Active Workspace Environment</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-medium text-softform-navy-950 block">Active Workspace</span>
            <span className="text-softform-teal-deep font-bold block truncate">
              {activeWorkspaceName || 'Unnamed Workspace'}
            </span>
            <span className="text-[10px] text-softform-text-secondary block">
              ID: {activeWorkspaceId}
            </span>
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-medium text-softform-navy-950 block">Snapshot Parameters</span>
            {activeSnapshot ? (
              <>
                <span className="text-softform-teal-deep font-bold block">
                  {activeSnapshot.currency || 'HKD'} • {activeSnapshot.reportingPeriod || 'FY2025'}
                </span>
                <span className="text-[10px] text-softform-text-secondary block">
                  Built: {activeSnapshot.metadata?.built_at ? new Date(activeSnapshot.metadata.built_at).toLocaleString() : 'N/A'}
                </span>
              </>
            ) : (
              <>
                <span className="text-softform-amber-500 font-bold block">
                  No Snapshot Active
                </span>
                <span className="text-[10px] text-softform-text-secondary block">
                  Awaiting statement upload
                </span>
              </>
            )}
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-medium text-softform-navy-950 block">Connected Ingestion Streams</span>
            <span className="text-softform-teal-deep font-bold block">
              {uploadedFiles.length} of {REQUIRED_SNAPSHOT_RECORD_KEYS.length + 1} Files Connected
            </span>
            <span className="text-[10px] text-softform-text-secondary block">
              Data mode: Ingestion active
            </span>
          </div>
        </div>
      </section>

        </div>

        {/* Right Column (Sidebar) */}
        <div className="space-y-6 lg:w-[380px] shrink-0">
          {/* Onboarding checklist */}
          <ReleaseOnboardingChecklist compact={true} />

          {/* Accepted Formats & Ingestion Guide */}
          <div className="softform-card rounded-[24px] p-6 space-y-4">
            <h3 className="text-sm font-bold text-softform-navy-950 flex items-center gap-2">
              <Database size={16} className="text-softform-teal-500" />
              <span>Accepted Formats & Ingestion</span>
            </h3>
            <div className="text-xs text-softform-text-secondary space-y-3">
              <div className="space-y-1">
                <span className="font-semibold text-softform-navy-950 block">Supported Extensions</span>
                <p>• <strong className="text-softform-navy-900">CSV (.csv):</strong> Clean, raw tabular rows without formulas.</p>
                <p>• <strong className="text-softform-navy-900">Excel (.xlsx):</strong> Standard sheets. Ensure data begins on cell A1.</p>
                <p>• <strong className="text-softform-navy-900">PDF/DOCX (.pdf, .docx):</strong> Standard digital text layers only.</p>
              </div>

              <div className="p-3 bg-amber-500/5 border border-amber-500/10 rounded-xl space-y-1">
                <span className="font-semibold text-softform-amber-500 block">OCR Disclaimer</span>
                <p className="text-[10px] leading-relaxed">
                  Cloud OCR parsing is currently <strong>not configured</strong>. Scanned documents, image-only files, or non-searchable PDFs are not supported. Please convert them to CSV or XLSX before uploading.
                </p>
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-softform-navy-950 block">Upload Template Guidelines</span>
                <p>Make sure uploaded files include key columns such as <code>Date</code>, <code>Category</code>, <code>Amount</code>, or standard financial ratios. Row names should match standard bookkeeping nomenclature.</p>
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-softform-navy-950 block">Ingestion Parser Statuses</span>
                <div className="space-y-1.5 pt-1 text-[11px]">
                  <p>• <span className="font-semibold text-emerald-600 bg-emerald-50 px-1 py-0.25 rounded">Parsed:</span> Record structure successfully matched and validated by accounting engine.</p>
                  <p>• <span className="font-semibold text-amber-600 bg-amber-50 px-1 py-0.25 rounded">Unsupported without OCR:</span> Non-text PDF detected. Needs CSV/XLSX structure.</p>
                  <p>• <span className="font-semibold text-rose-600 bg-rose-50 px-1 py-0.25 rounded">Failed:</span> Malformed layout, invalid dates, or out-of-balance values.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Next Actions */}
          <div className="softform-card rounded-[24px] p-6 space-y-4">
            <h3 className="text-sm font-bold text-softform-navy-950 flex items-center gap-2">
              <ArrowRight size={16} className="text-softform-teal-500" />
              <span>Recommended Next Actions</span>
            </h3>
            <div className="space-y-2.5">
              <button
                onClick={handleBuildSnapshot}
                disabled={isBuilding || locallyMissingRequiredStatements.length > 0}
                className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-850 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 transition flex items-center justify-between group disabled:opacity-50"
              >
                <div>
                  <p className="text-xs font-semibold text-softform-navy-950">1. Compile Snapshot</p>
                  <p className="text-[10px] text-softform-text-muted">Validate & publish active financials</p>
                </div>
                <Database size={14} className="text-slate-400 group-hover:text-softform-teal-deep transition" />
              </button>
              
              <Link
                to="/platform/financial-health"
                className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-105 dark:bg-slate-850 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 transition flex items-center justify-between group block"
              >
                <div>
                  <p className="text-xs font-semibold text-softform-navy-950">2. Review Financial Health</p>
                  <p className="text-[10px] text-softform-text-muted">Inspect ratio profiles & diagnostics</p>
                </div>
                <Activity size={14} className="text-slate-400 group-hover:text-softform-teal-deep transition" />
              </Link>

              <Link
                to="/platform/advisory-blueprint"
                className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-105 dark:bg-slate-850 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 transition flex items-center justify-between group block"
              >
                <div>
                  <p className="text-xs font-semibold text-softform-navy-950">3. Go to Advisory Blueprint</p>
                  <p className="text-[10px] text-softform-text-muted">Parameterize stress tests & view brief</p>
                </div>
                <Compass size={14} className="text-slate-400 group-hover:text-softform-teal-deep transition" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 7. Link to Advisory Blueprint & Market Watch */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <h3 className="font-semibold text-softform-navy-950 text-base">Explore Workspace Modules</h3>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            After compiling records here, review context-only market signals and the advisory readiness brief.
          </p>
        </div>
        <div className="flex gap-3.5 shrink-0 w-full sm:w-auto justify-center sm:justify-end">
          <Link
            to="/platform/market-watch"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-xs font-semibold text-softform-navy-950 hover:bg-white transition shadow-sm"
          >
            <TrendingUp size={14} className="text-softform-teal-deep" />
            Review Market Watch
          </Link>
          <Link
            to="/platform/advisory-blueprint"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
          >
            <Compass size={14} className="text-softform-teal-deep" />
            View Advisory Blueprint
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* Footer Info */}
      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted">
          {activeSnapshot ? `Workspace records active for ${activeWorkspaceName}.` : `Awaiting statement ingestion for ${activeWorkspaceName}.`}
        </p>
        <p className="text-xs text-softform-text-muted">
          FinSight CFO Workspace • Powered by softform design token system.
        </p>
      </footer>
    </div>
  )
}
