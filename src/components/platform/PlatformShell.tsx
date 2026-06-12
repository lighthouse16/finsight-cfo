import { useState, useCallback, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import SidebarNav from './SidebarNav'
import TopCommandBar from './TopCommandBar'
import { motion, AnimatePresence } from 'framer-motion'
import { WorkspaceProvider, useWorkspace } from '../../context/workspaceContext'
import CreateWorkspacePage from '../../pages/CreateWorkspacePage'
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

function PlatformShellContent() {
  const location = useLocation()
  const { workspaces, isLoading } = useWorkspace()
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

  if (workspaces.length === 0) {
    return <CreateWorkspacePage />
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
