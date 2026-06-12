/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import {
  listWorkspaces,
  createWorkspace as apiCreateWorkspace,
  type CompanyWorkspace,
} from '../features/data-room/api/dataRoomApi'
import { fetchBackendConfig, type BackendConfig } from '../lib/workspaceRunHelpers'

export interface WorkspaceContextValue {
  /** All workspaces for the current user/org */
  workspaces: CompanyWorkspace[]
  /** The currently active workspace */
  activeWorkspace: CompanyWorkspace | null
  /** Whether workspace data is being loaded */
  isLoading: boolean
  /** Backend configuration (AI status, app mode, etc.) */
  backendConfig: BackendConfig | null
  /** Select a workspace by ID */
  selectWorkspace: (id: string) => void
  /** Create a new workspace and select it */
  createWorkspace: (
    companyName: string,
    currency?: string,
    reportingPeriod?: string,
    metadata?: Record<string, string>,
  ) => Promise<CompanyWorkspace>
  /** Reload workspace list from backend */
  refreshWorkspaces: () => Promise<void>
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return ctx
}

interface WorkspaceProviderProps {
  children: ReactNode
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const [workspaces, setWorkspaces] = useState<CompanyWorkspace[]>([])
  const [activeWorkspace, setActiveWorkspace] = useState<CompanyWorkspace | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [backendConfig, setBackendConfig] = useState<BackendConfig | null>(null)

  const syncActiveFromList = useCallback(
    (list: CompanyWorkspace[]) => {
      const savedId = localStorage.getItem('active_workspace_id')
      if (savedId) {
        const found = list.find((w) => w.id === savedId)
        if (found) {
          setActiveWorkspace(found)
          return
        }
        // Saved workspace no longer exists — clear it
        localStorage.removeItem('active_workspace_id')
      }

      // Auto-select first workspace if list is non-empty and nothing was saved
      if (list.length > 0) {
        const first = list[0]
        localStorage.setItem('active_workspace_id', first.id)
        setActiveWorkspace(first)
        window.dispatchEvent(new Event('workspaceChanged'))
      } else {
        setActiveWorkspace(null)
      }
    },
    [],
  )

  const refreshWorkspaces = useCallback(async () => {
    setIsLoading(true)
    try {
      const list = await listWorkspaces()
      setWorkspaces(list)
      syncActiveFromList(list)
    } catch (err) {
      console.error('Failed to load workspaces', err)
      setWorkspaces([])
      setActiveWorkspace(null)
    } finally {
      setIsLoading(false)
    }
  }, [syncActiveFromList])

  const selectWorkspace = useCallback(
    (id: string) => {
      localStorage.setItem('active_workspace_id', id)
      const found = workspaces.find((w) => w.id === id)
      if (found) {
        setActiveWorkspace(found)
      }
      window.dispatchEvent(new Event('workspaceChanged'))
    },
    [workspaces],
  )

  const createWorkspaceHandler = useCallback(
    async (
      companyName: string,
      currency?: string,
      reportingPeriod?: string,
      metadata?: Record<string, string>,
    ): Promise<CompanyWorkspace> => {
      const newWs = await apiCreateWorkspace(companyName, currency, reportingPeriod, metadata)
      // Refresh list
      const updatedList = await listWorkspaces()
      setWorkspaces(updatedList)
      // Select newly created workspace
      localStorage.setItem('active_workspace_id', newWs.id)
      setActiveWorkspace(newWs)
      window.dispatchEvent(new Event('workspaceChanged'))
      return newWs
    },
    [],
  )

  // Load on mount
  useEffect(() => {
    refreshWorkspaces()
    fetchBackendConfig().then(setBackendConfig)
  }, [refreshWorkspaces])

  // Listen for external workspace changes (from other components)
  useEffect(() => {
    const handleChange = () => {
      const nextId = localStorage.getItem('active_workspace_id') || ''
      if (nextId !== activeWorkspace?.id) {
        refreshWorkspaces()
      }
    }
    window.addEventListener('workspaceChanged', handleChange)
    return () => window.removeEventListener('workspaceChanged', handleChange)
  }, [activeWorkspace?.id, refreshWorkspaces])

  const value: WorkspaceContextValue = {
    workspaces,
    activeWorkspace,
    isLoading,
    backendConfig,
    selectWorkspace,
    createWorkspace: createWorkspaceHandler,
    refreshWorkspaces,
  }

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  )
}
