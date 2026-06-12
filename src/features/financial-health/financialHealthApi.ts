/* eslint-disable @typescript-eslint/no-explicit-any */
import { API_BASE_URL, getWorkspaceHeaders, handleApiResponse } from '../../lib/apiBase'


export async function getFinancialHealthAnalysis(): Promise<any> {
  const workspaceId = localStorage.getItem('active_workspace_id')
  if (workspaceId) {
    try {
      const workspaceRes = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/financial-analysis`, {
        headers: getWorkspaceHeaders(),
        signal: AbortSignal.timeout(5000),
      })
      if (workspaceRes.ok) {
        return workspaceRes.json()
      }
    } catch (error) {
      console.warn('Workspace financial analysis unavailable; checking fallback.', error)
    }
  }

  try {
    const previewRes = await fetch(`${API_BASE_URL}/api/financials/preview-analysis`, {
      headers: getWorkspaceHeaders(),
      signal: AbortSignal.timeout(5000),
    })

    if (previewRes.ok) {
      return previewRes.json()
    }

    if (previewRes.status === 422) {
      return handleApiResponse(previewRes)
    }
  } catch (error) {
    console.warn('Preview financial analysis unavailable; trying persistent snapshot.', error)
  }

  const demoRes = await fetch(`${API_BASE_URL}/api/financials/demo-analysis`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })

  return handleApiResponse(demoRes)
}

