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
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SourceInfoTooltip from '../market-watch/components/SourceInfoTooltip'
import {
  buildDataRoomSnapshotPreview,
  fetchDataRoomReadiness,
  parseDataRoomPreview,
  uploadDataRoomMetadata,
} from './api/dataRoomApi'
import type {
  DataRoomParsedRecordSet,
  DataRoomParseResponse,
  DataRoomRecord,
  DataRoomResponse,
  DataRoomSnapshotPreviewResponse,
  DataRoomUploadResponse,
} from './types'

type UploadState = {
  uploading: boolean
  result: DataRoomUploadResponse | null
  parsePreview: DataRoomParseResponse | null
  error: string | null
}

type SnapshotPreviewState = {
  loading: boolean
  result: DataRoomSnapshotPreviewResponse | null
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

export default function DataRoomPage() {
  const [activeNotification, setActiveNotification] = useState<string | null>(null)
  const [readinessData, setReadinessData] = useState<DataRoomResponse | null>(null)
  const [isLoadingReadiness, setIsLoadingReadiness] = useState(true)
  const [uploadStates, setUploadStates] = useState<Record<string, UploadState>>({})
  const [parsedRecordSets, setParsedRecordSets] = useState<Record<string, DataRoomParsedRecordSet>>({})
  const [snapshotPreview, setSnapshotPreview] = useState<SnapshotPreviewState>({
    loading: false,
    result: null,
    error: null,
  })
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({})

  useEffect(() => {
    let isMounted = true

    fetchDataRoomReadiness().then((data) => {
      if (!isMounted) return
      setReadinessData(data)
      setIsLoadingReadiness(false)
    })

    return () => {
      isMounted = false
    }
  }, [])

  const snapshotRecordSets = useMemo(() => Object.values(parsedRecordSets), [parsedRecordSets])

  const locallyMissingRequiredStatements = useMemo(
    () => REQUIRED_SNAPSHOT_RECORD_KEYS.filter((recordKey) => !parsedRecordSets[recordKey]),
    [parsedRecordSets]
  )

  const snapshotRequestKey = useMemo(
    () => snapshotRecordSets.map((recordSet) => recordSet.recordKey).sort().join('|'),
    [snapshotRecordSets]
  )

  useEffect(() => {
    if (snapshotRecordSets.length === 0 || locallyMissingRequiredStatements.length > 0) {
      setSnapshotPreview((prev) => ({ ...prev, loading: false, result: null, error: null }))
      return
    }

    let isMounted = true
    setSnapshotPreview((prev) => ({ ...prev, loading: true, error: null }))

    buildDataRoomSnapshotPreview({
      currency: 'HKD',
      reportingPeriod: 'FY2025',
      recordSets: snapshotRecordSets,
    })
      .then((result) => {
        if (!isMounted) return
        setSnapshotPreview({ loading: false, result, error: null })
      })
      .catch(() => {
        if (!isMounted) return
        setSnapshotPreview({
          loading: false,
          result: null,
          error: 'Snapshot preview service unavailable. Uploaded metadata and parse preview remain available.',
        })
      })

    return () => {
      isMounted = false
    }
  }, [locallyMissingRequiredStatements.length, snapshotRecordSets, snapshotRequestKey])

  const handleActionClick = (recordName: string, action: string) => {
    setActiveNotification(
      `Integration trigger simulated: "${action}" for ${recordName}. Records integration is currently set to demo context. Connection to company servers requires production connectors.`
    )
    setTimeout(() => {
      setActiveNotification(null)
    }, 6000)
  }

  const handleUploadClick = useCallback((recordId: string) => {
    fileInputRefs.current[recordId]?.click()
  }, [])

  const handleFileSelected = useCallback(
    async (record: DataRoomRecord, event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      setUploadStates((prev) => ({
        ...prev,
        [record.id]: { uploading: true, result: null, parsePreview: null, error: null },
      }))

      try {
        const result = await uploadDataRoomMetadata(record.id, file)
        let parsePreview: DataRoomParseResponse | null = null
        if (result.uploadedFile.status !== 'unsupported_type') {
          const parsedResponse = await parseDataRoomPreview(record.id, file)
          parsePreview = parsedResponse
          setParsedRecordSets((prev) => ({
            ...prev,
            [record.id]: {
              recordKey: record.id,
              parsedRecords: parsedResponse.preview.parsedRecords,
              warnings: [...parsedResponse.preview.warnings, ...parsedResponse.warnings],
            },
          }))
        }
        setUploadStates((prev) => ({
          ...prev,
          [record.id]: { uploading: false, result, parsePreview, error: null },
        }))
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'Upload metadata service unavailable. Please try again later.'
        setUploadStates((prev) => ({
          ...prev,
          [record.id]: { uploading: false, result: null, parsePreview: null, error: message },
        }))
      }

      // Reset the file input so the same file can be re-selected
      event.target.value = ''
    },
    []
  )

  const records = readinessData?.records ?? []
  const dependencies = readinessData?.dependencies ?? []
  const totalRequired = readinessData?.summary.totalRequired ?? 0
  const connectedRequired = readinessData?.summary.connectedRequired ?? 0
  const missingRequired = readinessData?.summary.missingRequired ?? 0
  const readinessPercentage = readinessData?.summary.readinessPercentage ?? 0
  const backendMissingRequiredStatements = snapshotPreview.result?.missingRequiredStatements ?? []
  const displayedMissingRequiredStatements = backendMissingRequiredStatements.length
    ? backendMissingRequiredStatements
    : locallyMissingRequiredStatements
  const passedIntegrityCount = snapshotPreview.result?.integrityChecks.filter((check) => check.passed).length ?? 0
  const failedIntegrityCount = snapshotPreview.result?.integrityChecks.filter((check) => !check.passed).length ?? 0
  const warningIntegrityCount = snapshotPreview.result?.integrityChecks.filter((check) => check.message).length ?? 0
  const previewStatus = snapshotPreview.error
    ? 'Unavailable'
    : snapshotPreview.result?.snapshotPreview
      ? 'Ready'
      : displayedMissingRequiredStatements.length
        ? 'Missing statements'
        : snapshotPreview.loading
          ? 'Building preview'
          : 'Awaiting uploads'

  const getStatusChipVariant = (status: string) => {
    switch (status) {
      case 'demo_available':
      case 'connected':
        return 'signal'
      case 'missing':
        return 'caution'
      case 'optional':
      case 'coming_soon':
      default:
        return 'neutral'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'demo_available':
        return 'Demo available'
      case 'connected':
        return 'Connected'
      case 'missing':
        return 'Missing'
      case 'optional':
        return 'Optional'
      case 'coming_soon':
        return 'Coming soon'
      default:
        return status
    }
  }

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Page Header */}
      <PageHeader
        title="Data Room"
        subtitle="Company records required for production financial analysis and advisory context."
        titleAddon={
          <SourceInfoTooltip
            title="Data Room Provenance"
            sources={[
              { label: 'Company Financial Records', mode: 'workspace-derived' },
              { label: 'Integration Status Tracker', mode: 'workspace-derived' },
            ]}
            ariaLabel="Data room source information"
          />
        }
        chip={
          <StatusChip variant={readinessPercentage === 100 ? 'signal' : 'caution'}>
            {readinessPercentage}% Connected
          </StatusChip>
        }
      />

      {/* State Notification Toast */}
      <AnimatePresence>
        {activeNotification && (
          <div className="fixed bottom-6 right-6 z-50 max-w-md rounded-2xl border border-white/60 bg-white/95 p-4 shadow-floating-panel backdrop-blur-xl transition-all duration-300">
            <div className="flex gap-3">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep">
                <Database size={12} />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-softform-navy-950">System Notification</p>
                <p className="text-xs text-softform-text-secondary leading-relaxed">
                  {activeNotification}
                </p>
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. Data Readiness Overview */}
      <section className="grid gap-4 sm:grid-cols-4">
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Required Records
          </p>
          <p className="text-2xl font-black text-softform-navy-950 tabular-finance">{totalRequired}</p>
          <p className="text-xs text-softform-text-secondary">Specified in advisory parameters</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Connected Records
          </p>
          <p className="text-2xl font-black text-softform-teal-deep tabular-finance">{connectedRequired}</p>
          <p className="text-xs text-softform-text-secondary">Currently active in demo mode</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Missing Records
          </p>
          <p className="text-2xl font-black text-softform-amber-500 tabular-finance">{missingRequired}</p>
          <p className="text-xs text-softform-text-secondary">Required for full calibration</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Production Readiness
          </p>
          <p className="text-2xl font-black text-softform-navy-950 tabular-finance">{readinessPercentage}%</p>
          <p className="text-xs text-softform-text-secondary">Demo to Production threshold</p>
        </div>
      </section>

      {/* 3. Required Records Checklist */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Integration Status</h2>
          <span className="text-xs font-medium text-softform-text-muted">
            {isLoadingReadiness ? 'Loading readiness contract' : 'Required records checklist'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-softform-navy-950/10 text-[10px] font-bold uppercase tracking-[0.16em] text-softform-text-muted/80">
                <th className="pb-4 pl-3 w-8"></th>
                <th className="pb-4">Record Name</th>
                <th className="pb-4 hidden md:table-cell">Category</th>
                <th className="pb-4">Dependency Fits</th>
                <th className="pb-4 text-center">Status</th>
                <th className="pb-4 text-right pr-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-softform-navy-950/5">
              {records.map((rec) => {
                const uploadState = uploadStates[rec.id]
                return (
                  <tr key={rec.id} className="group hover:bg-white/20 transition-all duration-200">
                    {/* Hidden file input for Upload records */}
                    {rec.actionLabel === 'Upload' && (
                      <td colSpan={0} className="hidden">
                        <input
                          ref={(el) => {
                            fileInputRefs.current[rec.id] = el
                          }}
                          type="file"
                          id={`file-input-${rec.id}`}
                          name={`file-input-${rec.id}`}
                          accept=".pdf,.csv,.xlsx,.xls,.docx"
                          aria-label={`Upload file for ${rec.name}`}
                          className="sr-only"
                          onChange={(e) => handleFileSelected(rec, e)}
                        />
                      </td>
                    )}
                    <td className="py-4 pl-3">
                      {(rec.status === 'connected' || rec.status === 'demo_available') ? (
                        <div className="flex h-5 w-5 items-center justify-center rounded bg-softform-teal-deep/10 text-softform-teal-deep border border-softform-teal-deep/20 shadow-sm" title="Connected for Analysis">
                          <CheckSquare size={11} strokeWidth={2.5} />
                        </div>
                      ) : rec.status === 'missing' ? (
                        <div className="flex h-5 w-5 items-center justify-center rounded border border-softform-amber-500/30 text-softform-amber-500/80 bg-softform-cream/40 shadow-inner" title="Required Document Missing">
                          <div className="h-1.5 w-1.5 rounded-full bg-softform-amber-500" />
                        </div>
                      ) : (
                        <div className="flex h-5 w-5 items-center justify-center rounded border border-softform-text-muted/20 text-softform-text-muted/40 bg-white/20" title="Optional Document">
                          <div className="h-1 w-1 rounded-full bg-softform-text-muted/40" />
                        </div>
                      )}
                    </td>
                    <td className="py-4 space-y-1">
                      <div className="font-bold text-softform-navy-950 text-sm flex items-center gap-2">
                        <FileText size={14} className="text-softform-text-muted/70 shrink-0" />
                        {rec.name}
                      </div>
                      <p className="text-xs text-softform-text-secondary max-w-[320px] leading-relaxed">
                        {rec.purpose}
                      </p>
                      {/* Upload result / error inline */}
                      {uploadState && (
                        <div className="mt-2 max-w-[400px]">
                          {uploadState.uploading && (
                            <div className="flex items-center gap-2 text-xs text-softform-text-secondary">
                              <Loader2 size={12} className="animate-spin" />
                              <span>Receiving metadata...</span>
                            </div>
                          )}
                          {uploadState.result && (
                            <div className="rounded-xl border border-softform-navy-950/5 bg-white/40 p-3 space-y-1.5">
                              <div className="flex items-center gap-1.5">
                                {uploadState.result.uploadedFile.status === 'unsupported_type' ? (
                                  <AlertCircle size={12} className="text-softform-amber-500" />
                                ) : (
                                  <CheckSquare size={12} className="text-softform-teal-deep" />
                                )}
                                <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-softform-text-muted">
                                  {uploadState.result.uploadedFile.status === 'unsupported_type'
                                    ? 'Unsupported file'
                                    : 'Metadata received'}
                                </span>
                              </div>
                              <p className="text-xs text-softform-text-secondary leading-relaxed">
                                {uploadState.result.uploadedFile.status === 'unsupported_type'
                                  ? 'This file type is not supported. Analysis will not be updated.'
                                  : 'File metadata received. Analysis remains unchanged until production ingestion is connected.'}
                              </p>
                              {uploadState.parsePreview && (
                                <div className="rounded-lg bg-softform-mist-100/50 px-2.5 py-2 text-[11px] text-softform-text-secondary">
                                  <span className="font-bold text-softform-navy-950">
                                    Structured preview:
                                  </span>{' '}
                                  {uploadState.parsePreview.preview.parsedRecords.length} fields read ·{' '}
                                  {uploadState.parsePreview.preview.missingExpectedFields.length} expected fields missing
                                </div>
                              )}
                              {uploadState.result.warnings.length > 0 && (
                                <p className="text-xs text-softform-amber-500 font-medium">
                                  {uploadState.result.warnings[0]}
                                </p>
                              )}
                            </div>
                          )}
                          {uploadState.error && (
                            <div className="rounded-xl border border-softform-amber-500/20 bg-softform-cream/30 p-3 space-y-1">
                              <div className="flex items-center gap-1.5">
                                <AlertCircle size={12} className="text-softform-amber-500" />
                                <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-softform-text-muted">
                                  Unavailable
                                </span>
                              </div>
                              <p className="text-xs text-softform-amber-500 leading-relaxed">
                                {uploadState.error}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-4 hidden md:table-cell">
                      <span className="text-xs font-medium text-softform-text-secondary">{rec.category}</span>
                    </td>
                    <td className="py-4">
                      <div className="flex flex-wrap gap-1">
                        {rec.requiredFor.map((rf) => (
                          <span
                            key={rf}
                            className="inline-block rounded bg-softform-mist-100/60 px-2 py-0.5 text-[10px] text-softform-teal-deep font-bold border border-softform-aqua-300/20 uppercase tracking-[0.08em]"
                          >
                            {rf}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-4 text-center">
                      <StatusChip variant={getStatusChipVariant(rec.status)}>
                        {getStatusLabel(rec.status)}
                      </StatusChip>
                    </td>
                    <td className="py-4 text-right pr-3">
                      {rec.actionLabel === 'Upload' ? (
                        <button
                          type="button"
                          onClick={() => handleUploadClick(rec.id)}
                          disabled={uploadState?.uploading}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 border-softform-navy-950/10 px-3 py-1.5 text-xs font-bold text-white transition hover:bg-softform-navy-800 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 shadow-sm"
                        >
                          {uploadState?.uploading ? (
                            <Loader2 size={12} className="animate-spin" />
                          ) : (
                            <Upload size={12} />
                          )}
                          {uploadState?.uploading ? 'Uploading...' : 'Upload'}
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleActionClick(rec.name, rec.actionLabel)}
                          className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold transition border shadow-sm ${
                            rec.actionLabel === 'Review'
                              ? 'bg-white/80 border-white/60 text-softform-navy-950 hover:bg-white hover:-translate-y-0.5'
                              : 'bg-white/40 border-white/30 text-softform-text-muted cursor-not-allowed'
                          }`}
                          disabled={rec.actionLabel === 'Coming soon'}
                        >
                          {rec.actionLabel}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. Financial Snapshot Preview */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex flex-col gap-3 border-b border-softform-navy-950/5 pb-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-softform-teal-deep" />
              <h2 className="text-lg font-bold text-softform-navy-950">Financial Snapshot Preview</h2>
            </div>
            <p className="text-xs text-softform-text-muted leading-relaxed">
              Preview-only ingestion from structured files. The main financial and advisory analysis remains unchanged.
            </p>
          </div>
          <StatusChip variant={snapshotPreview.error ? 'caution' : snapshotPreview.result?.snapshotPreview ? 'signal' : 'neutral'}>
            {previewStatus}
          </StatusChip>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
              Parsed Statements
            </p>
            <p className="text-2xl font-black text-softform-navy-950 tabular-finance">
              {snapshotRecordSets.length}/{REQUIRED_SNAPSHOT_RECORD_KEYS.length}
            </p>
            <p className="text-xs text-softform-text-secondary">Required structured files uploaded</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
              Integrity Checks
            </p>
            <p className="text-2xl font-black text-softform-teal-deep tabular-finance">
              {passedIntegrityCount}/{snapshotPreview.result?.integrityChecks.length ?? 0}
            </p>
            <p className="text-xs text-softform-text-secondary">Passed in preview response</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
              Review Signals
            </p>
            <p className="text-2xl font-black text-softform-amber-500 tabular-finance">
              {failedIntegrityCount + warningIntegrityCount}
            </p>
            <p className="text-xs text-softform-text-secondary">Failures or backend warnings</p>
          </div>
          <div className="rounded-[22px] border border-white/60 bg-white/40 p-4 space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
              Ratios Returned
            </p>
            <p className="text-2xl font-black text-softform-navy-950 tabular-finance">
              {snapshotPreview.result?.ratios ? Object.keys(snapshotPreview.result.ratios).length : 0}
            </p>
            <p className="text-xs text-softform-text-secondary">Core ratio preview metrics</p>
          </div>
        </div>

        {snapshotPreview.loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-softform-aqua-300/25 bg-softform-mist-100/40 px-4 py-3 text-xs font-semibold text-softform-text-secondary">
            <Loader2 size={14} className="animate-spin text-softform-teal-deep" />
            Building normalized snapshot preview from parsed structured files...
          </div>
        )}

        {snapshotPreview.error && (
          <div className="flex items-start gap-2 rounded-2xl border border-softform-amber-500/20 bg-softform-cream/30 px-4 py-3 text-xs text-softform-amber-500">
            <AlertCircle size={14} className="mt-0.5 shrink-0" />
            <span>{snapshotPreview.error}</span>
          </div>
        )}

        {displayedMissingRequiredStatements.length > 0 && !snapshotPreview.error && (
          <div className="rounded-2xl border border-softform-navy-950/5 bg-white/35 px-4 py-3 text-xs text-softform-text-secondary">
            <span className="font-bold text-softform-navy-950">Missing required statements:</span>{' '}
            {displayedMissingRequiredStatements.map((recordKey) => SNAPSHOT_RECORD_LABELS[recordKey] ?? recordKey).join(', ')}
          </div>
        )}

        {snapshotPreview.result && (
          <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
            <div className="rounded-[22px] border border-white/60 bg-white/40 p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-softform-teal-deep" />
                <h3 className="text-sm font-bold text-softform-navy-950">Integrity Check Preview</h3>
              </div>
              <div className="space-y-2">
                {snapshotPreview.result.integrityChecks.slice(0, 4).map((check) => (
                  <div key={check.checkName} className="rounded-xl bg-white/45 px-3 py-2 text-xs">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-bold text-softform-navy-950">{check.checkName}</span>
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
              <h3 className="text-sm font-bold text-softform-navy-950">Core Ratio Preview</h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {CORE_RATIO_KEYS.map((ratioKey) => {
                  const ratio = snapshotPreview.result?.ratios?.[ratioKey]
                  return (
                    <div key={ratioKey} className="rounded-xl bg-white/45 px-3 py-2">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-softform-text-muted">
                        {ratio?.label ?? ratioKey}
                      </p>
                      <p className="mt-1 text-lg font-black text-softform-navy-950 tabular-finance">
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
                {snapshotPreview.result.disclaimer}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* 5. Analysis Dependency Map */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Analysis Dependency Mapping</h2>
          <p className="text-xs text-softform-text-muted mt-1">
            Understanding how integrated documents feed the advisory models
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {dependencies.map((feed) => (
            <div
              key={feed.recordGroup}
              className="p-5 rounded-[22px] bg-white/40 border border-white/60 shadow-sm space-y-4 hover-lift"
            >
              <h3 className="font-bold text-softform-navy-950 text-sm leading-snug">
                {feed.recordGroup}
              </h3>
              <div className="h-[1px] bg-softform-navy-950/5" />
              <div className="space-y-2">
                <span className="text-[9px] font-bold text-softform-text-muted/90 uppercase tracking-[0.14em]">
                  Feeds Engine Outcomes
                </span>
                <ul className="space-y-2 pt-1">
                  {feed.outputs.map((out, oIdx) => (
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

      {/* 5. Demo vs Production State */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-5">
        <h2 className="text-base font-bold text-softform-navy-950">Active Workspace Environment</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Analysis Context</span>
            <span className="text-softform-teal-deep font-semibold">Demo financial analysis active</span>
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Market Indicators</span>
            <span className="text-softform-teal-deep font-semibold">Provider-backed market data active</span>
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Requirement Level</span>
            <span className="text-softform-amber-500 font-semibold">Company records required for production mode</span>
          </div>
        </div>
      </section>

      {/* 6. Link to Advisory Blueprint & Market Watch */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <h3 className="font-bold text-softform-navy-950 text-base">Explore Workspace Modules</h3>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            The Data Room is the primary source of company records. Connect records to transition from demo context to production-ready analysis in other modules.
          </p>
        </div>
        <div className="flex gap-3.5 shrink-0 w-full sm:w-auto justify-center sm:justify-end">
          <Link
            to="/platform/market-watch"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-xs font-bold text-softform-navy-950 hover:bg-white transition shadow-sm"
          >
            <TrendingUp size={14} className="text-softform-teal-deep" />
            Review Market Watch
          </Link>
          <Link
            to="/platform/advisory-blueprint"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-softform-navy-800 transition shadow-sm"
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
          Demo analysis is currently active. Connect company records to transition to production-ready analysis.
        </p>
        <p className="text-xs text-softform-text-muted">
          FinSight CFO Workspace • Powered by softform design token system.
        </p>
      </footer>
    </div>
  )
}
