import { useState, useCallback, useEffect } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Building2, Database, Loader2, Sparkles } from 'lucide-react'
import SidebarNav from './SidebarNav'
import TopCommandBar from './TopCommandBar'
import { motion, AnimatePresence } from 'framer-motion'
import { WorkspaceProvider, useWorkspace } from '../../context/workspaceContext'
import PageLoadingSkeleton from './PageLoadingSkeleton'

const SIDEBAR_COLLAPSED_KEY = 'finsight-sidebar-collapsed'

function readCollapsedFromStorage(): boolean {
  try {
    const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    return stored === 'true'
  } catch {
    return false
  }
}

function writeCollapsedToStorage(value: boolean): void {
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(value))
  } catch {
    // localStorage unavailable — fail silently
  }
}

function WorkspaceEntryChoice() {
  const navigate = useNavigate()
  const { exploreWithMockData } = useWorkspace()
  const [isLoadingDemo, setIsLoadingDemo] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExploreWithMockData = async () => {
    setError(null)
    setIsLoadingDemo(true)
    try {
      await exploreWithMockData()
      navigate('/platform/overview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sample workspace is not available in this environment.')
    } finally {
      setIsLoadingDemo(false)
    }
  }

  return (
    <main className="softform-page flex min-h-dvh items-center justify-center px-4 py-12">
      <motion.section
        className="w-full max-w-5xl"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="mx-auto mb-8 max-w-3xl text-center">
          <span className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/64 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.16em] text-softform-teal-deep shadow-pressed backdrop-blur">
            <Sparkles size={14} />
            Choose your entry path
          </span>
          <h1 className="text-3xl font-black tracking-[-0.045em] text-softform-navy-950 sm:text-5xl">
            Start clean or tour FinSight CFO with a sample company.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-softform-text-secondary sm:text-base">
            Keep real company workspaces separate from synthetic demo data so every workspace has a clear purpose.
          </p>
        </div>

        {error && (
          <div className="mx-auto mb-5 max-w-2xl rounded-2xl bg-red-50/70 px-4 py-3 text-sm font-semibold text-red-700 ring-1 ring-red-200/70">
            {error}
          </div>
        )}

        <div className="grid gap-5 md:grid-cols-2">
          <button
            id="workspace-entry-start-scratch"
            type="button"
            onClick={() => navigate('/platform/create-workspace')}
            className="group softform-panel relative overflow-hidden rounded-[34px] p-7 text-left shadow-floating-panel transition duration-300 hover:-translate-y-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-softform-teal-500"
          >
            <div className="absolute right-0 top-0 h-40 w-40 -translate-y-10 translate-x-10 rounded-full bg-softform-teal-500/10 blur-2xl" />
            <div className="relative flex h-full flex-col">
              <div className="mb-7 flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-white shadow-[0_16px_42px_rgba(8,17,31,0.24)]">
                <Building2 size={24} />
              </div>
              <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-softform-text-muted">Path A</p>
              <h2 className="text-2xl font-black tracking-[-0.035em] text-softform-navy-950">Start from scratch</h2>
              <p className="mt-3 text-sm leading-6 text-softform-text-secondary">
                Create a clean workspace and upload your own company records.
              </p>
              <div className="mt-8 flex items-center gap-2 text-sm font-bold text-softform-navy-950">
                Create clean workspace
                <ArrowRight size={16} className="transition group-hover:translate-x-1" />
              </div>
            </div>
          </button>

          <button
            id="workspace-entry-explore-mock-data"
            type="button"
            onClick={handleExploreWithMockData}
            disabled={isLoadingDemo}
            className="group relative overflow-hidden rounded-[34px] bg-[radial-gradient(circle_at_88%_12%,rgba(32,169,154,0.22),transparent_32%),linear-gradient(145deg,#0d1726_0%,#132337_52%,#1c324b_100%)] p-7 text-left text-white shadow-navy-card transition duration-300 hover:-translate-y-1 disabled:cursor-not-allowed disabled:opacity-75 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-softform-amber-300"
          >
            <div className="absolute -right-8 top-6 h-44 w-44 rounded-full bg-softform-amber-300/16 blur-2xl" />
            <div className="relative flex h-full flex-col">
              <div className="mb-7 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/16 bg-white/10 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.16)]">
                <Database size={24} />
              </div>
              <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-white/52">Path B</p>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-black tracking-[-0.035em]">Explore with mock data</h2>
                <span className="rounded-full bg-softform-amber-200/18 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.13em] text-softform-amber-200 ring-1 ring-softform-amber-200/24">
                  Synthetic Demo Data
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-white/72">
                Sample company: Novus Retail Solutions Ltd. Use synthetic sample data to review the full product flow quickly.
              </p>
              <div className="mt-8 flex items-center gap-2 text-sm font-bold text-white">
                {isLoadingDemo ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Loading sample company…
                  </>
                ) : (
                  <>
                    Open sample company
                    <ArrowRight size={16} className="transition group-hover:translate-x-1" />
                  </>
                )}
              </div>
            </div>
          </button>
        </div>
      </motion.section>
    </main>
  )
}

function PlatformShellContent() {
  const location = useLocation()
  const { activeWorkspace, isLoading } = useWorkspace()
  // Mobile drawer state
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Desktop collapsed state — owned here, persisted to localStorage
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(
    readCollapsedFromStorage,
  )

  // Sync collapsed state to localStorage whenever it changes
  useEffect(() => {
    writeCollapsedToStorage(sidebarCollapsed)
  }, [sidebarCollapsed])

  const handleMenuToggle = useCallback(() => {
    setSidebarOpen((prev) => !prev)
  }, [])

  const handleSidebarClose = useCallback(() => {
    setSidebarOpen(false)
  }, [])

  const handleCollapseToggle = useCallback(() => {
    setSidebarCollapsed((prev) => !prev)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-dvh bg-[var(--softform-page-bg)] px-6 py-8 softform-page">
        <PageLoadingSkeleton layout="overview" />
      </div>
    )
  }

  if (!activeWorkspace && location.pathname !== '/platform/create-workspace') {
    return <WorkspaceEntryChoice />
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-[var(--softform-page-bg)] bg-fixed">
      {/* Sidebar */}
      <SidebarNav
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
        collapsed={sidebarCollapsed}
        onToggleCollapse={handleCollapseToggle}
      />

      {/* Main content area — flexes naturally to fill remaining width */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <TopCommandBar onMenuToggle={handleMenuToggle} />

        <div className="flex-1 overflow-y-auto px-6 py-6 lg:px-10 xl:px-12 pb-16 softform-page">
          <div className="mx-auto max-w-7xl">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: 'easeInOut' }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  )
}

export default function PlatformShell() {
  return (
    <WorkspaceProvider>
      <PlatformShellContent />
    </WorkspaceProvider>
  )
}
