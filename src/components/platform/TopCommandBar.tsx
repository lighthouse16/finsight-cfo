/* eslint-disable react-hooks/exhaustive-deps, @typescript-eslint/no-explicit-any */
import { useState, useEffect, useRef } from 'react'
import { Menu, Search, Bell, ChevronDown, Plus, Building2, Check, Loader2 } from 'lucide-react'
import { API_BASE_URL } from '../../lib/apiBase'

interface Workspace {
  id: string
  companyName: string
  createdAt: string
  metadata: Record<string, any>
}

type TopCommandBarProps = {
  onMenuToggle: () => void
}

export default function TopCommandBar({ onMenuToggle }: TopCommandBarProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newCompanyName, setNewCompanyName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
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

  const fetchWorkspaces = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/workspaces`)
      if (res.ok) {
        const data: Workspace[] = await res.json()
        setWorkspaces(data)

        if (data.length === 0) {
          // Auto-create default workspace if none exist
          await handleAutoCreateDefault()
          return
        }

        const savedId = localStorage.getItem('active_workspace_id')
        const active = data.find((w) => w.id === savedId) || data[0]
        if (active) {
          if (savedId !== active.id) {
            localStorage.setItem('active_workspace_id', active.id)
            // Dispatch custom event to notify other parts of the app
            window.dispatchEvent(new Event('workspaceChanged'))
          }
          setActiveWorkspace(active)
        }
      }
    } catch (err) {
      console.error('Failed to fetch workspaces', err)
    }
  }

  const handleAutoCreateDefault = async () => {
    try {
      const formData = new FormData()
      formData.append('companyName', 'Finsight Enterprise')
      const res = await fetch(`${API_BASE_URL}/api/workspaces`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const newWs: Workspace = await res.json()
        localStorage.setItem('active_workspace_id', newWs.id)
        window.dispatchEvent(new Event('workspaceChanged'))
        fetchWorkspaces()
      }
    } catch (err) {
      console.error('Failed to auto-create default workspace', err)
    }
  }

  useEffect(() => {
    fetchWorkspaces()
    
    // Listen to storage/workspace changes from other components
    const handleWorkspaceChanged = () => {
      const savedId = localStorage.getItem('active_workspace_id')
      if (savedId && savedId !== activeWorkspace?.id) {
        fetchWorkspaces()
      }
    }
    window.addEventListener('workspaceChanged', handleWorkspaceChanged)
    return () => {
      window.removeEventListener('workspaceChanged', handleWorkspaceChanged)
    }
  }, [activeWorkspace?.id])

  const handleSelectWorkspace = (workspaceId: string) => {
    localStorage.setItem('active_workspace_id', workspaceId)
    setIsDropdownOpen(false)
    window.dispatchEvent(new Event('workspaceChanged'))
    // Force a complete reload to refresh all page context cleanly
    window.location.reload()
  }

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    const name = newCompanyName.trim()
    if (!name) return

    setIsCreating(true)
    try {
      const formData = new FormData()
      formData.append('companyName', name)
      const res = await fetch(`${API_BASE_URL}/api/workspaces`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const newWs: Workspace = await res.json()
        localStorage.setItem('active_workspace_id', newWs.id)
        setNewCompanyName('')
        setIsCreateOpen(false)
        setIsDropdownOpen(false)
        window.dispatchEvent(new Event('workspaceChanged'))
        window.location.reload()
      } else {
        const errData = await res.json()
        alert(`Failed to create workspace: ${errData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error creating workspace', err)
      alert('Error connecting to backend')
    } finally {
      setIsCreating(false)
    }
  }

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

        {/* Workspace Selector Dropdown */}
        <div className="relative shrink-0 select-none z-50">
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

          {isDropdownOpen && (
            <>
              {/* Overlay to close */}
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => {
                  setIsDropdownOpen(false)
                  setIsCreateOpen(false)
                }} 
              />
              
              <div className="absolute left-0 mt-2 z-50 w-64 origin-top-left rounded-2xl border border-white/80 bg-white/95 p-2.5 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-md transition-all duration-200">
                <div className="px-2 pb-1.5 pt-1 text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
                  Select Workspace
                </div>
                
                <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-0.5">
                  {workspaces.map((w) => (
                    <button
                      key={w.id}
                      onClick={() => handleSelectWorkspace(w.id)}
                      className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-left text-xs transition-colors ${
                        activeWorkspace?.id === w.id
                          ? 'bg-softform-navy-900 text-white font-medium'
                          : 'text-softform-navy-950 hover:bg-black/5'
                      }`}
                    >
                      <span className="truncate">{w.companyName}</span>
                      {activeWorkspace?.id === w.id && <Check size={14} className="shrink-0" />}
                    </button>
                  ))}
                </div>

                <div className="my-1.5 border-t border-softform-navy-950/5" />

                {!isCreateOpen ? (
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(true)}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-xs font-semibold text-softform-teal-600 hover:bg-softform-teal-50/50 hover:text-softform-teal-700 transition-colors"
                  >
                    <Plus size={14} />
                    New Company Workspace
                  </button>
                ) : (
                  <form onSubmit={handleCreateWorkspace} className="space-y-2 p-1 pt-0.5">
                    <input
                      type="text"
                      placeholder="Company Name"
                      value={newCompanyName}
                      onChange={(e) => setNewCompanyName(e.target.value)}
                      required
                      className="w-full rounded-xl border border-softform-navy-950/10 bg-white px-2.5 py-1.5 text-xs text-softform-navy-950 placeholder:text-softform-navy-950/30 focus:border-softform-teal-500 focus:outline-none"
                    />
                    <div className="flex gap-1.5">
                      <button
                        type="submit"
                        disabled={isCreating}
                        className="flex flex-1 items-center justify-center gap-1 rounded-xl bg-softform-teal-600 py-1.5 text-xs font-semibold text-white hover:bg-softform-teal-700 disabled:opacity-50"
                      >
                        {isCreating ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          'Create'
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsCreateOpen(false)}
                        className="rounded-xl border border-softform-navy-950/10 px-2.5 py-1.5 text-xs font-semibold text-softform-navy-700 hover:bg-black/5"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
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
            <div className="absolute right-0 mt-2 z-50 w-48 origin-top-right rounded-2xl border border-white/80 bg-white/95 p-2 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-md transition-all duration-200">
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
