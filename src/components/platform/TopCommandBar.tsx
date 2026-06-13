import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Search, Bell, ChevronDown, Plus, Building2, Check, Loader2, FlaskConical } from 'lucide-react'
import { useWorkspace } from '../../context/workspaceContext'
import { API_BASE_URL } from '../../lib/apiBase'

type TopCommandBarProps = {
  onMenuToggle: () => void
}

export default function TopCommandBar({ onMenuToggle }: TopCommandBarProps) {
  const navigate = useNavigate()
  const { workspaces, activeWorkspace, selectWorkspace, refreshWorkspaces } = useWorkspace()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoadingDemo, setIsLoadingDemo] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const userRole = localStorage.getItem('active_user_role') || 'User'
  const userMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('active_user_role')
    localStorage.removeItem('active_workspace_id')
    window.location.href = '/'
  }

  const handleSelectWorkspace = (workspaceId: string) => {
    selectWorkspace(workspaceId)
    setIsDropdownOpen(false)
  }

  const handleLoadDemo = async () => {
    setIsLoadingDemo(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/workspaces/reset-sample`, {
        method: 'POST',
      })
      if (!res.ok) {
        throw new Error('Failed to load demo workspace')
      }
      localStorage.setItem('active_workspace_id', 'workspace_sample_novus')
      window.dispatchEvent(new Event('workspaceChanged'))
      await refreshWorkspaces()
      setIsDropdownOpen(false)
      navigate('/platform/overview')
    } catch (err) {
      console.error('Error resetting sample workspace:', err)
      alert('Failed to load demo workspace')
    } finally {
      setIsLoadingDemo(false)
    }
  }

  // De-duplicate workspaces by ID
  const uniqueWorkspaces = workspaces.filter(
    (ws, idx, self) => self.findIndex((w) => w.id === ws.id) === idx
  )

  // Demo workspace helper
  const demoWorkspace = uniqueWorkspaces.find((w) => w.id === 'workspace_sample_novus')

  // Real workspaces (non-demo)
  const realWorkspaces = uniqueWorkspaces.filter((w) => w.id !== 'workspace_sample_novus')

  // Filter out duplicate "Finsight Enterprise" display names
  const seenNames = new Set<string>()
  const processedReal = realWorkspaces.filter((w) => {
    const normName = w.companyName.toLowerCase().trim()
    if (normName === 'finsight enterprise' && seenNames.has(normName)) {
      return false
    }
    seenNames.add(normName)
    return true
  })

  // Sort real workspaces by creation date (newest first)
  const sortedReal = [...processedReal].sort(
    (a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()
  )

  return (
    <header className="sticky top-0 z-30 px-4 pb-2 pt-4 sm:px-6">
      <div className="flex items-center gap-3 rounded-[22px] border border-white/70 bg-[linear-gradient(145deg,rgba(255,255,255,0.76),rgba(231,240,244,0.66))] px-4 py-2.5 shadow-[0_12px_40px_rgba(8,17,31,0.12),0_4px_16px_rgba(8,17,31,0.06),inset_0_1px_0_rgba(255,255,255,0.82)] backdrop-blur-[20px] sm:px-5 sm:py-3">
        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={onMenuToggle}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-softform-text-secondary transition hover:bg-white/50 hover:text-softform-navy-900 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>

        {/* Workspace Selector */}
        <div className="relative shrink-0 select-none z-50 flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 rounded-xl border border-white/60 bg-white/40 px-3 py-1.5 text-xs font-semibold text-softform-navy-950 transition hover:bg-white/60 hover:shadow-sm focus:outline-none"
          >
            <Building2 size={14} className="text-softform-navy-700" />
            <span className="max-w-[120px] truncate">
              {activeWorkspace ? activeWorkspace.companyName : 'Loading Workspace...'}
            </span>
            <ChevronDown size={14} className={`text-softform-navy-500 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {activeWorkspace?.id === 'workspace_sample_novus' && (
            <span className="inline-flex items-center rounded-full bg-softform-amber-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-softform-amber-700 border border-softform-amber-200/50 shadow-sm animate-pulse">
              Synthetic Demo Data
            </span>
          )}

          {isDropdownOpen && (
            <>
              {/* Overlay to close */}
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => {
                  setIsDropdownOpen(false)
                }} 
              />
              
              <div className="absolute left-0 top-full mt-2 z-50 w-72 origin-top-left rounded-2xl border border-white/80 bg-white/95 p-3 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-md transition-all duration-200 space-y-3">
                {/* Active Workspace Section */}
                {activeWorkspace && (
                  <div className="space-y-1">
                    <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
                      Active Workspace
                    </div>
                    <div className="flex w-full items-center justify-between rounded-xl bg-softform-navy-900 px-3 py-2 text-left text-xs text-white font-medium shadow-sm">
                      <span className="truncate">{activeWorkspace.companyName}</span>
                      <Check size={14} className="shrink-0 text-softform-teal-400" />
                    </div>
                  </div>
                )}

                {/* Real Workspaces Section */}
                {sortedReal.length > 0 && (
                  <div className="space-y-1">
                    <div className="px-2 pt-1 text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
                      Company workspaces
                    </div>
                    <div className="max-h-36 overflow-y-auto custom-scrollbar space-y-0.5">
                      {sortedReal.map((w) => {
                        const isActive = activeWorkspace?.id === w.id
                        if (isActive) return null // Already shown at top
                        return (
                          <button
                            key={w.id}
                            type="button"
                            onClick={() => handleSelectWorkspace(w.id)}
                            className="flex w-full items-center justify-between rounded-xl px-2.5 py-1.5 text-left text-xs text-softform-navy-950 hover:bg-black/5 transition-colors"
                          >
                            <span className="truncate">{w.companyName}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Demo Workspace Section */}
                {demoWorkspace && activeWorkspace?.id !== demoWorkspace.id && (
                  <div className="space-y-1">
                    <div className="px-2 pt-1 text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
                      Demo workspace
                    </div>
                    <button
                      type="button"
                      onClick={() => handleSelectWorkspace(demoWorkspace.id)}
                      className="flex w-full items-center justify-between rounded-xl px-2.5 py-1.5 text-left text-xs text-softform-navy-950 hover:bg-black/5 transition-colors"
                    >
                      <span className="truncate">{demoWorkspace.companyName}</span>
                      <span className="shrink-0 rounded-full bg-softform-amber-100 px-2 py-0.2 text-[8px] font-bold uppercase tracking-wider text-softform-amber-700 border border-softform-amber-200/50 scale-90">
                        Synthetic Demo Data
                      </span>
                    </button>
                  </div>
                )}

                <div className="border-t border-softform-navy-950/5 my-1" />

                {/* Actions Section */}
                <div className="space-y-0.5">
                  <button
                    type="button"
                    onClick={() => {
                      setIsDropdownOpen(false)
                      navigate('/create-workspace?flow=scratch')
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-xs font-semibold text-softform-teal-600 hover:bg-softform-teal-50/50 hover:text-softform-teal-700 transition-colors"
                  >
                    <Plus size={14} />
                    Start from scratch
                  </button>

                  <button
                    type="button"
                    onClick={handleLoadDemo}
                    disabled={isLoadingDemo}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-xs font-semibold text-softform-amber-600 hover:bg-softform-amber-50/50 hover:text-softform-amber-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoadingDemo ? (
                      <Loader2 size={14} className="animate-spin text-softform-amber-600" />
                    ) : (
                      <FlaskConical size={14} />
                    )}
                    Explore with mock data
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Search placeholder */}
        <div className="group relative mx-auto hidden max-w-sm flex-1 md:block">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-softform-text-muted opacity-60"
          />
          <input
            id="workspace-search"
            name="workspace-search"
            type="text"
            placeholder="Search workspace…"
            disabled
            aria-label="Search workspace"
            className="w-full rounded-xl border border-white/50 bg-white/40 py-2 pl-9 pr-4 text-sm text-softform-text-primary placeholder:text-softform-text-muted/60 opacity-60 focus-visible:outline-none disabled:cursor-default"
          />
          <span
            role="tooltip"
            className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-softform-navy-950 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-white opacity-0 shadow-md transition-opacity duration-200 group-hover:opacity-100"
          >
            Search coming soon
          </span>
        </div>

        {/* Notification bell */}
        <div className="group relative ml-auto sm:ml-0">
          <button
            type="button"
            disabled
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/50 bg-white/30 text-softform-text-muted opacity-60 transition hover:bg-white/50 hover:text-softform-navy-950 disabled:cursor-default"
            aria-label="Notifications"
          >
            <Bell size={16} />
          </button>
          <span
            role="tooltip"
            className="pointer-events-none absolute right-0 top-full z-50 mt-2 whitespace-nowrap rounded-lg bg-softform-navy-950 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-white opacity-0 shadow-md transition-opacity duration-200 group-hover:opacity-100"
          >
            Notifications coming soon
          </span>
        </div>

        {/* Avatar / User Menu */}
        <div className="relative shrink-0" ref={userMenuRef}>
          <button
            type="button"
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex h-9 items-center gap-2 rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] pl-2 pr-3 text-[11px] font-bold text-white/90 shadow-sm ring-2 ring-white/80 transition hover:ring-softform-teal-500/50"
            aria-label="User menu"
            aria-expanded={isUserMenuOpen}
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10 uppercase">
              {userRole.charAt(0)}
            </div>
            <span className="hidden sm:inline-block max-w-[80px] truncate capitalize font-medium text-white/80 tracking-wide">
              {userRole}
            </span>
          </button>
          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-softform-emerald-soft ring-2 ring-white" aria-hidden="true" />
          
          {isUserMenuOpen && (
            <div className="absolute right-0 top-full mt-2 z-50 w-48 origin-top-right rounded-2xl border border-white/80 bg-white/95 p-2 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-md transition-all duration-200">
              <div className="px-3 pb-2 pt-2 border-b border-softform-navy-950/10 mb-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">Logged in as</div>
                <div className="text-sm font-semibold text-softform-navy-950 truncate capitalize">{userRole}</div>
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center justify-start rounded-xl px-3 py-2 text-left text-xs font-semibold text-red-600 hover:bg-red-50 transition-colors"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
