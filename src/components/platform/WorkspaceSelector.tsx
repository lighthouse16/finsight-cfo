import { useEffect, useState, useRef } from 'react'
import {
  ChevronDown,
  Plus,
  Trash2,
  Check,
  Building,
  Loader2,
  X,
} from 'lucide-react'
import {
  listWorkspaces,
  createWorkspace,
  deleteWorkspace,
  CompanyWorkspace,
} from '../../features/data-room/api/dataRoomApi'

export default function WorkspaceSelector() {
  const [workspaces, setWorkspaces] = useState<CompanyWorkspace[]>([])
  const [activeId, setActiveId] = useState<string>(localStorage.getItem('active_workspace_id') || '')
  const [activeWorkspace, setActiveWorkspace] = useState<CompanyWorkspace | null>(null)
  
  const [isOpen, setIsOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  
  // New workspace form state
  const [newCompanyName, setNewCompanyName] = useState('')
  const [newCurrency, setNewCurrency] = useState('HKD')
  const [newReportingPeriod, setNewReportingPeriod] = useState('FY2025')
  const [formError, setFormError] = useState<string | null>(null)

  const dropdownRef = useRef<HTMLDivElement>(null)

  // Load workspaces
  const loadWorkspaces = async () => {
    setIsLoading(true)
    try {
      const list = await listWorkspaces()
      setWorkspaces(list)
      
      const currentActiveId = localStorage.getItem('active_workspace_id') || ''
      if (currentActiveId) {
        const found = list.find((w) => w.id === currentActiveId)
        if (found) {
          setActiveWorkspace(found)
          setActiveId(currentActiveId)
        } else {
          // Active workspace no longer exists in backend
          localStorage.removeItem('active_workspace_id')
          setActiveId('')
          setActiveWorkspace(null)
          window.dispatchEvent(new Event('workspaceChanged'))
        }
      } else if (list.length > 0) {
        // Auto select first workspace if none active
        const first = list[0]
        localStorage.setItem('active_workspace_id', first.id)
        setActiveId(first.id)
        setActiveWorkspace(first)
        window.dispatchEvent(new Event('workspaceChanged'))
      }
    } catch (err) {
      console.error('Failed to load workspaces', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadWorkspaces()
    
    // Listen for external workspace changes
    const handleWorkspaceChanged = () => {
      const nextId = localStorage.getItem('active_workspace_id') || ''
      setActiveId(nextId)
    }
    window.addEventListener('workspaceChanged', handleWorkspaceChanged)
    return () => window.removeEventListener('workspaceChanged', handleWorkspaceChanged)
  }, [])

  // Update activeWorkspace when workspaces list or activeId changes
  useEffect(() => {
    if (activeId && workspaces.length > 0) {
      const found = workspaces.find((w) => w.id === activeId)
      if (found) {
        setActiveWorkspace(found)
      } else {
        setActiveWorkspace(null)
      }
    } else {
      setActiveWorkspace(null)
    }
  }, [activeId, workspaces])

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setIsCreating(false)
        setFormError(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (id: string) => {
    localStorage.setItem('active_workspace_id', id)
    setActiveId(id)
    setIsOpen(false)
    window.dispatchEvent(new Event('workspaceChanged'))
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    const companyNameClean = newCompanyName.trim()
    if (!companyNameClean) {
      setFormError('Company name is required')
      return
    }

    try {
      setIsLoading(true)
      const newWs = await createWorkspace(companyNameClean, newCurrency, newReportingPeriod)
      
      // Refresh list
      const updatedList = await listWorkspaces()
      setWorkspaces(updatedList)
      
      // Select newly created workspace
      localStorage.setItem('active_workspace_id', newWs.id)
      setActiveId(newWs.id)
      setActiveWorkspace(newWs)
      
      // Reset form
      setNewCompanyName('')
      setNewCurrency('HKD')
      setNewReportingPeriod('FY2025')
      setIsCreating(false)
      setIsOpen(false)
      
      window.dispatchEvent(new Event('workspaceChanged'))
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create workspace')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation() // Avoid selecting workspace when clicking delete
    if (!confirm(`Are you sure you want to delete workspace "${name}"? This will cascade delete all physical files, metadata, snapshots, and audit runs.`)) {
      return
    }

    try {
      setIsLoading(true)
      await deleteWorkspace(id)
      
      // If active workspace was deleted, clear it
      if (id === activeId) {
        localStorage.removeItem('active_workspace_id')
        setActiveId('')
        setActiveWorkspace(null)
      }
      
      // Reload lists
      const list = await listWorkspaces()
      setWorkspaces(list)
      
      // If we cleared active but there are other workspaces, select the first
      if (id === activeId) {
        if (list.length > 0) {
          const first = list[0]
          localStorage.setItem('active_workspace_id', first.id)
          setActiveId(first.id)
          setActiveWorkspace(first)
        }
        window.dispatchEvent(new Event('workspaceChanged'))
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete workspace')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 rounded-xl border border-white/70 bg-white/60 px-4 py-2 text-xs font-semibold text-softform-navy-950 shadow-sm hover:bg-white transition-all duration-300 min-w-[200px] justify-between"
      >
        <div className="flex items-center gap-2 truncate">
          <Building size={14} className="text-softform-teal-deep shrink-0" />
          <span className="truncate">
            {activeWorkspace ? activeWorkspace.companyName : 'Select Workspace'}
          </span>
        </div>
        <ChevronDown size={14} className="text-softform-text-secondary shrink-0" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-2 w-72 rounded-[22px] border border-white/80 bg-white/95 p-3 shadow-[0_20px_50px_rgba(8,17,31,0.15)] backdrop-blur-xl z-50">
          {!isCreating ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-2 px-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-softform-text-muted">
                  Workspaces
                </span>
                <button
                  type="button"
                  onClick={() => setIsCreating(true)}
                  className="inline-flex items-center gap-1 text-[10px] font-bold text-softform-teal-deep hover:text-softform-teal-600 transition"
                >
                  <Plus size={10} /> Add New
                </button>
              </div>

              {isLoading && workspaces.length === 0 ? (
                <div className="flex items-center justify-center py-6 gap-2 text-xs text-softform-text-muted">
                  <Loader2 size={12} className="animate-spin" />
                  Loading...
                </div>
              ) : workspaces.length === 0 ? (
                <div className="text-center py-6 text-xs text-softform-text-muted space-y-2">
                  <p>No workspaces found.</p>
                  <button
                    type="button"
                    onClick={() => setIsCreating(true)}
                    className="inline-flex items-center gap-1 rounded-lg bg-softform-navy-900 px-3 py-1.5 text-[10px] font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
                  >
                    <Plus size={10} /> Create Workspace
                  </button>
                </div>
              ) : (
                <div className="max-h-56 overflow-y-auto space-y-1 pr-1 scrollbar-thin">
                  {workspaces.map((ws) => {
                    const isActive = ws.id === activeId
                    return (
                      <div
                        key={ws.id}
                        onClick={() => handleSelect(ws.id)}
                        className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs cursor-pointer transition-all duration-200 ${
                          isActive
                            ? 'bg-softform-mist-100/60 text-softform-navy-950 font-semibold'
                            : 'text-softform-text-secondary hover:bg-softform-mist-100/30 hover:text-softform-navy-950'
                        }`}
                      >
                        <span className="truncate pr-2">{ws.companyName}</span>
                        <div className="flex items-center gap-2 shrink-0">
                          {isActive && <Check size={12} className="text-softform-teal-deep" />}
                          <button
                            type="button"
                            onClick={(e) => handleDelete(e, ws.id, ws.companyName)}
                            className="text-softform-text-muted hover:text-red-500 opacity-0 group-hover:opacity-100 focus:opacity-100 transition duration-200"
                            title="Delete workspace"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Create Workspace Inline Form */
            <form onSubmit={handleCreate} className="space-y-3 p-1">
              <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-softform-text-muted">
                  New Company Workspace
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false)
                    setFormError(null)
                  }}
                  className="text-softform-text-muted hover:text-softform-navy-950 transition"
                >
                  <X size={12} />
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <div className="space-y-1">
                  <label htmlFor="company-name-input" className="font-semibold text-softform-navy-950">
                    Company Name
                  </label>
                  <input
                    id="company-name-input"
                    type="text"
                    placeholder="Enter company name"
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                    className="w-full rounded-xl border border-white/60 bg-white/50 px-3 py-2 text-xs text-softform-navy-950 shadow-sm focus:border-softform-teal-deep focus:bg-white focus:outline-none transition"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label htmlFor="currency-select" className="font-semibold text-softform-navy-950">
                      Currency
                    </label>
                    <select
                      id="currency-select"
                      value={newCurrency}
                      onChange={(e) => setNewCurrency(e.target.value)}
                      className="w-full rounded-xl border border-white/60 bg-white/50 px-2.5 py-2 text-xs text-softform-navy-950 shadow-sm focus:border-softform-teal-deep focus:bg-white focus:outline-none transition"
                    >
                      <option value="HKD">HKD</option>
                      <option value="USD">USD</option>
                      <option value="SGD">SGD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label htmlFor="period-select" className="font-semibold text-softform-navy-950">
                      Period
                    </label>
                    <select
                      id="period-select"
                      value={newReportingPeriod}
                      onChange={(e) => setNewReportingPeriod(e.target.value)}
                      className="w-full rounded-xl border border-white/60 bg-white/50 px-2.5 py-2 text-xs text-softform-navy-950 shadow-sm focus:border-softform-teal-deep focus:bg-white focus:outline-none transition"
                    >
                      <option value="FY2025">FY2025</option>
                      <option value="FY2026">FY2026</option>
                      <option value="FY2024">FY2024</option>
                    </select>
                  </div>
                </div>
              </div>

              {formError && (
                <p className="text-[10px] text-red-500 font-semibold">{formError}</p>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false)
                    setFormError(null)
                  }}
                  className="w-1/2 rounded-xl border border-white/60 bg-white/50 py-2 text-center text-xs font-semibold text-softform-navy-950 hover:bg-white transition shadow-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-1/2 inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 py-2 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm"
                >
                  {isLoading && <Loader2 size={10} className="animate-spin" />}
                  Create
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  )
}
