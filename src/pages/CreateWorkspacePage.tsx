/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Building2,
  Globe,
  DollarSign,
  Calendar,
  MapPin,
  Loader2,
  ArrowRight,
  Sparkles,
  FlaskConical,
  ArrowLeft,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { useWorkspace } from '../context/workspaceContext'
import { API_BASE_URL } from '../lib/apiBase'

const INDUSTRY_OPTIONS = [
  { value: '', label: 'Select industry…' },
  { value: 'technology', label: 'Technology & SaaS' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail & E-Commerce' },
  { value: 'professional_services', label: 'Professional Services' },
  { value: 'logistics', label: 'Logistics & Trade' },
  { value: 'food_beverage', label: 'Food & Beverage' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'real_estate', label: 'Real Estate & Property' },
  { value: 'financial_services', label: 'Financial Services' },
  { value: 'construction', label: 'Construction & Engineering' },
  { value: 'other', label: 'Other' },
]

const CURRENCY_OPTIONS = [
  { value: 'HKD', label: 'HKD — Hong Kong Dollar' },
  { value: 'USD', label: 'USD — US Dollar' },
  { value: 'SGD', label: 'SGD — Singapore Dollar' },
  { value: 'CNY', label: 'CNY — Chinese Yuan' },
  { value: 'EUR', label: 'EUR — Euro' },
  { value: 'GBP', label: 'GBP — British Pound' },
]

const PERIOD_OPTIONS = [
  { value: 'FY2025', label: 'FY 2025' },
  { value: 'FY2026', label: 'FY 2026' },
  { value: 'FY2024', label: 'FY 2024' },
  { value: 'FY2023', label: 'FY 2023' },
]

const REGION_OPTIONS = [
  { value: '', label: 'Select region…' },
  { value: 'hong_kong', label: 'Hong Kong' },
  { value: 'greater_bay_area', label: 'Greater Bay Area (GBA)' },
  { value: 'southeast_asia', label: 'Southeast Asia' },
  { value: 'north_america', label: 'North America' },
  { value: 'europe', label: 'Europe' },
  { value: 'global', label: 'Global / Multi-region' },
]

export default function CreateWorkspacePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { createWorkspace, refreshWorkspaces } = useWorkspace()

  const initialFlow = searchParams.get('flow')
  const [viewMode, setViewMode] = useState<'choice' | 'scratch'>(
    initialFlow === 'scratch' ? 'scratch' : 'choice'
  )

  const [companyName, setCompanyName] = useState('')
  const [industry, setIndustry] = useState('')
  const [currency, setCurrency] = useState('HKD')
  const [reportingPeriod, setReportingPeriod] = useState('FY2025')
  const [region, setRegion] = useState('')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingDemo, setIsLoadingDemo] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    const name = companyName.trim()
    if (!name) {
      setFormError('Company name is required.')
      return
    }

    setIsSubmitting(true)
    try {
      await createWorkspace(name, currency, reportingPeriod, {
        industry,
        region,
      })
      navigate('/platform/overview')
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create workspace. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLoadDemo = async () => {
    setFormError(null)
    setIsLoadingDemo(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/workspaces/reset-sample`, {
        method: 'POST',
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Failed to load demo' }))
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : data.detail?.message || 'Failed to load demo workspace',
        )
      }
      // Select the demo workspace
      localStorage.setItem('active_workspace_id', 'workspace_sample_novus')
      window.dispatchEvent(new Event('workspaceChanged'))
      await refreshWorkspaces()
      navigate('/platform/overview')
    } catch (err: any) {
      setFormError(err?.message || 'Demo workspace is not available in this environment.')
    } finally {
      setIsLoadingDemo(false)
    }
  }

  const isDisabled = isSubmitting || isLoadingDemo

  if (viewMode === 'choice') {
    return (
      <div className="flex min-h-dvh items-center justify-center px-4 py-12 bg-[var(--softform-page-bg)] softform-page">
        <motion.div
          className="w-full max-w-4xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* Header */}
          <div className="mb-12 text-center space-y-3">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-sm font-bold text-white shadow-[0_12px_36px_rgba(8,17,31,0.28)]">
              <Sparkles size={22} className="text-softform-teal-400" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-softform-navy-950 sm:text-4xl">
              Welcome to FinSight CFO
            </h1>
            <p className="mx-auto max-w-lg text-sm text-softform-text-secondary">
              Select how you would like to initialize your workspace to begin analyzing financial performance.
            </p>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card A: Start from Scratch */}
            <div className="softform-panel rounded-[32px] p-8 shadow-floating-panel hover:shadow-floating-panel-hover transition-all duration-300 flex flex-col justify-between border border-white/80 bg-white/70 backdrop-blur-md relative overflow-hidden group min-h-[300px]">
              <div className="absolute top-0 right-0 w-32 h-32 bg-softform-teal-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-softform-teal-500/10 transition-colors" />
              <div className="space-y-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-softform-teal-50 text-softform-teal-deep shadow-sm">
                  <Building2 size={20} />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl font-bold text-softform-navy-950">
                    Start from scratch
                  </h2>
                  <p className="text-sm leading-relaxed text-softform-text-secondary">
                    Create a clean workspace and upload your own company records.
                  </p>
                </div>
              </div>
              <div className="mt-8">
                <button
                  type="button"
                  onClick={() => setViewMode('scratch')}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-4 py-3.5 text-sm font-bold text-white shadow-[0_12px_30px_rgba(8,17,31,0.18)] hover:-translate-y-0.5 transition-all duration-200"
                >
                  Create company workspace
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>

            {/* Card B: Explore with Mock Data */}
            <div className="softform-panel rounded-[32px] p-8 shadow-floating-panel hover:shadow-floating-panel-hover transition-all duration-300 flex flex-col justify-between border border-white/80 bg-white/70 backdrop-blur-md relative overflow-hidden group min-h-[300px]">
              <div className="absolute top-0 right-0 w-32 h-32 bg-softform-amber-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-softform-amber-500/10 transition-colors" />
              <div className="space-y-6">
                <div className="flex justify-between items-start">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-softform-amber-50 text-softform-amber-500 shadow-sm">
                    <FlaskConical size={20} />
                  </div>
                  <span className="rounded-full bg-softform-amber-100 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-softform-amber-700 border border-softform-amber-200/50">
                    Synthetic Demo Data
                  </span>
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl font-bold text-softform-navy-950">
                    Explore with mock data
                  </h2>
                  <p className="text-sm leading-relaxed text-softform-text-secondary">
                    Use synthetic sample data to review the full product flow quickly.
                  </p>
                  <p className="text-xs text-softform-text-muted">
                    Sample company: Novus Retail Solutions Ltd
                  </p>
                </div>
              </div>
              <div className="mt-8">
                <button
                  type="button"
                  onClick={handleLoadDemo}
                  disabled={isLoadingDemo}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl border border-softform-navy-950/10 bg-white/80 px-4 py-3.5 text-sm font-semibold text-softform-navy-950 shadow-sm hover:bg-white transition-all hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isLoadingDemo ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-softform-navy-950" />
                      Opening sample company…
                    </>
                  ) : (
                    <>
                      Open sample company
                      <ArrowRight size={16} className="text-softform-text-secondary" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {formError && (
            <div className="mt-6 mx-auto max-w-md rounded-xl bg-red-50/60 px-4 py-2.5 text-center text-xs font-semibold text-red-600 ring-1 ring-red-200/50">
              {formError}
            </div>
          )}
        </motion.div>
      </div>
    )
  }

  return (
    <div className="flex min-h-dvh items-center justify-center px-4 py-12 bg-[var(--softform-page-bg)] softform-page">
      <motion.div
        className="w-full max-w-xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Header */}
        <div className="mb-8 text-center relative">
          <button
            type="button"
            onClick={() => setViewMode('choice')}
            className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-xs font-semibold text-softform-text-secondary hover:text-softform-navy-950 transition-colors"
          >
            <ArrowLeft size={14} />
            Back to choices
          </button>
          
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-sm font-bold text-white shadow-[0_12px_36px_rgba(8,17,31,0.28)]">
            <Sparkles size={22} />
          </div>
          <h1 className="text-2xl font-bold tracking-[-0.035em] text-softform-navy-950 sm:text-3xl">
            Start from scratch
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-softform-text-secondary">
            Create a clean workspace and upload your own company records.
          </p>
        </div>

        {/* Form Card */}
        <div className="softform-panel rounded-[32px] p-6 shadow-floating-panel sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Company Name */}
            <div className="space-y-1.5">
              <label
                htmlFor="onboard-company-name"
                className="flex items-center gap-2 text-sm font-bold text-softform-navy-950"
              >
                <Building2 size={14} className="text-softform-teal-deep" />
                Company Name
              </label>
              <input
                id="onboard-company-name"
                type="text"
                placeholder="e.g. Apex Industrial Holdings Ltd"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                disabled={isDisabled}
                className="w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset ring-softform-navy-950/10 transition-all placeholder:text-softform-text-muted/50 focus:ring-2 focus:ring-inset focus:ring-softform-teal-500 focus:shadow-[0_0_15px_rgba(32,169,154,0.15)] sm:text-sm disabled:opacity-60"
              />
            </div>

            {/* Industry + Region row */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label
                  htmlFor="onboard-industry"
                  className="flex items-center gap-2 text-sm font-bold text-softform-navy-950"
                >
                  <Globe size={14} className="text-softform-teal-deep" />
                  Industry
                </label>
                <select
                  id="onboard-industry"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  disabled={isDisabled}
                  className="w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset ring-softform-navy-950/10 transition-all focus:ring-2 focus:ring-inset focus:ring-softform-teal-500 sm:text-sm disabled:opacity-60"
                >
                  {INDUSTRY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="onboard-region"
                  className="flex items-center gap-2 text-sm font-bold text-softform-navy-950"
                >
                  <MapPin size={14} className="text-softform-teal-deep" />
                  Region
                </label>
                <select
                  id="onboard-region"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  disabled={isDisabled}
                  className="w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset ring-softform-navy-950/10 transition-all focus:ring-2 focus:ring-inset focus:ring-softform-teal-500 sm:text-sm disabled:opacity-60"
                >
                  {REGION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Currency + Period row */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label
                  htmlFor="onboard-currency"
                  className="flex items-center gap-2 text-sm font-bold text-softform-navy-950"
                >
                  <DollarSign size={14} className="text-softform-teal-deep" />
                  Currency
                </label>
                <select
                  id="onboard-currency"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  disabled={isDisabled}
                  className="w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset ring-softform-navy-950/10 transition-all focus:ring-2 focus:ring-inset focus:ring-softform-teal-500 sm:text-sm disabled:opacity-60"
                >
                  {CURRENCY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="onboard-period"
                  className="flex items-center gap-2 text-sm font-bold text-softform-navy-950"
                >
                  <Calendar size={14} className="text-softform-teal-deep" />
                  Reporting Period
                </label>
                <select
                  id="onboard-period"
                  value={reportingPeriod}
                  onChange={(e) => setReportingPeriod(e.target.value)}
                  disabled={isDisabled}
                  className="w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset ring-softform-navy-950/10 transition-all focus:ring-2 focus:ring-inset focus:ring-softform-teal-500 sm:text-sm disabled:opacity-60"
                >
                  {PERIOD_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Error */}
            {formError && (
              <div className="rounded-xl bg-red-50/60 px-4 py-2.5 text-xs font-semibold text-red-600 ring-1 ring-red-200/50">
                {formError}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isDisabled}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-4 py-3.5 text-sm font-bold text-white shadow-[0_18px_42px_rgba(8,17,31,0.22)] transition-all hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-softform-teal-500 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating clean workspace…
                </>
              ) : (
                <>
                  Create company workspace
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer note */}
        <p className="mt-6 text-center text-xs leading-relaxed text-softform-text-muted">
          Your workspace stores uploaded financial records, calculated analytics,
          and advisory output. All data is isolated to your organization.
        </p>
      </motion.div>
    </div>
  )
}
