import { API_BASE_URL, getWorkspaceHeaders } from '../../../lib/apiBase'

export type ReportJobProgress = {
  percent?: number | null
  stage?: string | null
  message?: string | null
}

export type ReportJob = {
  id: string
  workspaceId: string
  organizationId?: string | null
  jobType: string
  status: string
  inputPayload?: Record<string, unknown> | null
  resultPayload?: Record<string, unknown> | null
  errorMessage?: string | null
  metadata?: {
    progress?: ReportJobProgress | null
    [key: string]: unknown
  } | null
  createdAt?: string | null
  startedAt?: string | null
  completedAt?: string | null
}

export class ReportJobsApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ReportJobsApiError'
    this.status = status
  }
}

type CreateReportJobInput = {
  reportType: string
  reportPayload?: Record<string, unknown>
  metadata?: Record<string, unknown>
  storageUri?: string
  maxAttempts?: number
}

function getErrorMessage(status: number, detail: unknown) {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (
    status === 501
  ) {
    return 'Job persistence is not available in current local mode.'
  }

  return `Job API returned status ${status}.`
}

async function parseJobResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>
  }

  let detail: unknown = null

  try {
    const body = await response.json()
    detail = body?.detail ?? null
  } catch {
    detail = null
  }

  throw new ReportJobsApiError(getErrorMessage(response.status, detail), response.status)
}

export async function listWorkspaceJobs(workspaceId: string): Promise<ReportJob[]> {
  const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/jobs`, {
    headers: getWorkspaceHeaders(),
  })

  const jobs = await parseJobResponse<ReportJob[]>(response)

  return [...jobs].sort((left, right) => {
    const leftTime = left.createdAt ? Date.parse(left.createdAt) : 0
    const rightTime = right.createdAt ? Date.parse(right.createdAt) : 0
    return rightTime - leftTime
  })
}

export async function getWorkspaceJob(workspaceId: string, jobId: string): Promise<ReportJob> {
  const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/jobs/${jobId}`, {
    headers: getWorkspaceHeaders(),
  })

  return parseJobResponse<ReportJob>(response)
}

export async function createReportGenerationJob(
  workspaceId: string,
  input: CreateReportJobInput,
): Promise<ReportJob> {
  const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/jobs/report-generation`, {
    method: 'POST',
    headers: getWorkspaceHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify(input),
  })

  return parseJobResponse<ReportJob>(response)
}
