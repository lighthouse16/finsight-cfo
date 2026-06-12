import { useEffect, useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { API_BASE_URL } from '../../lib/apiBase'

export default function GlobalRuntimeWarning() {
  const [warnings, setWarnings] = useState<string[]>([])

  useEffect(() => {
    async function checkBackendConfig() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/config`)
        if (response.ok) {
          const config = await response.json()
          const newWarnings: string[] = []
          
          if (config.auth_mode === 'local') {
            newWarnings.push('Backend is using local/mock authentication.')
          }
          if (config.app_mode === 'development' || config.allow_demo_fallback) {
            newWarnings.push('Running in development mode with demo logic.')
          }
          if (config.persistence_backend === 'local') {
            newWarnings.push('Storage and DB are using local ephemeral files.')
          }
          if (!config.ai_configured) {
            newWarnings.push('AI Provider is not configured (missing keys).')
          }
          
          setWarnings(newWarnings)
        }
      } catch (err) {
        // Ignore fetch errors for the warning banner
      }
    }
    checkBackendConfig()
  }, [])

  if (warnings.length === 0) return null

  return (
    <div className="bg-yellow-50 px-4 py-2 text-sm font-medium text-yellow-800 border-b border-yellow-200 flex items-center justify-center gap-2 relative z-50">
      <AlertCircle className="w-4 h-4 shrink-0" />
      <div className="flex gap-4">
        {warnings.map((w, i) => (
          <span key={i}>{w}</span>
        ))}
      </div>
    </div>
  )
}
