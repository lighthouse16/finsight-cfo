/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  const { createWorkspace, refreshWorkspaces } = useWorkspace()

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

  return (
    <div className="flex min-h-dvh items-center justify-center px-4 py-12 softform-page">
      <motion.div
        className="w-full max-w-xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-sm font-bold text-white shadow-[0_12px_36px_rgba(8,17,31,0.28)]">
            <Sparkles size={22} />
          </div>
          <h1 className="text-2xl font-bold tracking-[-0.035em] text-softform-navy-950 sm:text-3xl">
            Create your workspace
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-softform-text-secondary">
            Set up your company's financial intelligence workspace to begin uploading
            records, running analysis, and generating advisory output.
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
                  Creating workspace…
                </>
              ) : (
                <>
                  Create Workspace
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Demo divider */}
          <div className="mt-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-softform-navy-950/8" />
            <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted">
              or explore with demo data
            </span>
            <div className="h-px flex-1 bg-softform-navy-950/8" />
          </div>

          {/* Demo CTA */}
          <button
            type="button"
            onClick={handleLoadDemo}
            disabled={isDisabled}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-softform-navy-950/10 bg-white/60 px-4 py-3 text-sm font-semibold text-softform-navy-950 shadow-sm transition-all hover:bg-white/80 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoadingDemo ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading demo workspace…
              </>
            ) : (
              <>
                <FlaskConical size={14} className="text-softform-amber-500" />
                Load Sample Company
                <span className="ml-1 rounded-full bg-softform-amber-200/60 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-softform-amber-500">
                  Synthetic data
                </span>
              </>
            )}
          </button>
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
