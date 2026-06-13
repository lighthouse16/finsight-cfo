import { API_BASE_URL, getWorkspaceHeaders } from '../../../lib/apiBase'

export interface AdvisoryChatSource {
  title: string
  snippet?: string | null
  documentId?: string
  chunkIndex?: number | null
}

export interface AdvisoryChatResponse {
  aiMode: string
  answer: string
  sources: AdvisoryChatSource[]
  disclaimer: string
  warnings: string[]
}

export interface AdvisoryChatRequest {
  question: string
  workspaceId?: string | null
}

export async function postChatQuestion(
  request: AdvisoryChatRequest,
): Promise<AdvisoryChatResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getWorkspaceHeaders(),
  }

  const res = await fetch(`${API_BASE_URL}/api/advisory/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      question: request.question,
      workspace_id: request.workspaceId ?? undefined,
    }),
  })

  if (!res.ok) {
    const errBody = await res.json().catch(() => null)
    const detail = errBody?.detail
    throw new Error(
      typeof detail === 'string'
        ? detail
        : detail?.message ?? `Chat request failed (HTTP ${res.status})`,
    )
  }

  return res.json() as Promise<AdvisoryChatResponse>
}
