import { API_BASE_URL, getWorkspaceHeaders } from '../../../lib/apiBase'

export interface ReportCitation {
  title: string
  snippet: string
  documentId?: string | null
  chunkIndex?: number | null
  relevanceScore?: number | null
  sourceMode?: string
}

export interface AdvisorReportSection {
  title: string
  content: string
  citations: ReportCitation[]
}

export interface AdvisorReadyReportPayload {
  reportType: string
  workspaceId: string
  generatedAt: string
  title: string
  companySnapshot: Record<string, unknown>
  dataQuality: Record<string, unknown>
  sections: AdvisorReportSection[]
  sourceProvenance: string
  disclaimers: string[]
  aiMode: string
  limitations: string[]
}

export interface AdvisorReportResponse {
  reportId?: string | null
  jobId?: string | null
  payload: AdvisorReadyReportPayload
}

export interface AdvisorReportRequest {
  objective?: string | null
}

export async function generateAdvisorReport(
  workspaceId: string,
  request: AdvisorReportRequest = {}
): Promise<AdvisorReportResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getWorkspaceHeaders({ 'x-workspace-id': workspaceId }),
  }

  const res = await fetch(`${API_BASE_URL}/api/advisory/report`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      objective: request.objective ?? undefined,
    }),
  })

  if (!res.ok) {
    const errBody = await res.json().catch(() => null)
    const detail = errBody?.detail
    throw new Error(
      typeof detail === 'string'
        ? detail
        : detail?.message ?? `Report generation failed (HTTP ${res.status})`,
    )
  }

  return res.json() as Promise<AdvisorReportResponse>
}
