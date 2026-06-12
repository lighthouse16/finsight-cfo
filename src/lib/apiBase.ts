/* eslint-disable @typescript-eslint/no-explicit-any */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export function getWorkspaceHeaders(existingHeaders: Record<string, string> = {}): Record<string, string> {
  const activeWorkspaceId = localStorage.getItem('active_workspace_id')
  const accessToken = localStorage.getItem('access_token')
  const headers = { ...existingHeaders }
  if (activeWorkspaceId) {
    headers['x-workspace-id'] = activeWorkspaceId
  }
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }
  return headers
}

export async function handleApiResponse(response: Response): Promise<any> {
  if (response.ok) {
    return response.json()
  }

  // Handle structured error cases
  if (response.status === 404 || response.status === 422 || response.status === 503) {
    try {
      const errBody = await response.json()
      const detail = errBody.detail
      if (detail && typeof detail === 'object') {
        const code = detail.code
        const source = detail.source
        
        if (
          source === 'workspace' || 
          source === 'provider' ||
          code === 'ACTIVE_SNAPSHOT_NOT_FOUND' || 
          code === 'WORKSPACE_DATA_NOT_FOUND' || 
          code === 'INSUFFICIENT_WORKSPACE_DATA' ||
          code === 'CONSENT_PROVIDER_UNAVAILABLE' ||
          code === 'UPSTREAM_UNAVAILABLE'
        ) {
          return {
            status: 'insufficient_data',
            missingRequirements: detail.missingRequirements || [detail.message || 'Active workspace snapshot is missing or unconfigured.'],
            nextActions: detail.nextActions || ['Go to the Data Room to upload files.'],
          }
        }
      }
    } catch (e) {
      // JSON parsing or structure verification failed; fall back to generic error
    }
  }

  throw new Error(`API returned status ${response.status}`)
}

