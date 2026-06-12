/* eslint-disable @typescript-eslint/no-explicit-any */
import { API_BASE_URL, getWorkspaceHeaders } from '../../../lib/apiBase'

export interface UploadedFileRecord {
  id: string
  workspaceId: string
  recordKey: string
  fileName: string
  fileType: string
  fileSizeBytes: number
  status: string
  uploadedAt: string
  filePath: string
}

export interface WorkspaceSnapshotResponse {
  status: 'success' | 'insufficient_data'
  snapshot?: any
  missingRequirements?: string[]
  nextActions?: string[]
  warnings?: string[]
}

export interface CompanyWorkspace {
  id: string
  companyName: string
  createdAt: string
  metadata?: any
}

export async function fetchWorkspaceFiles(workspaceId: string): Promise<UploadedFileRecord[]> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/files`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch workspace files: ${res.statusText}`)
  }
  return res.json()
}

export async function uploadWorkspaceFile(
  workspaceId: string,
  recordKey: string,
  file: File
): Promise<UploadedFileRecord> {
  const formData = new FormData()
  formData.append('recordKey', recordKey)
  formData.append('file', file)

  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/files`, {
    method: 'POST',
    headers: getWorkspaceHeaders(),
    body: formData,
  })
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(detail)
  }
  return res.json()
}

export async function buildWorkspaceSnapshot(
  workspaceId: string,
  currency?: string,
  reportingPeriod?: string
): Promise<WorkspaceSnapshotResponse> {
  const params = new URLSearchParams()
  if (currency) params.append('currency', currency)
  if (reportingPeriod) params.append('reportingPeriod', reportingPeriod)

  const queryString = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/snapshot/build${queryString}`, {
    method: 'POST',
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(detail)
  }
  return res.json()
}

export async function fetchActiveWorkspaceSnapshot(workspaceId: string): Promise<WorkspaceSnapshotResponse> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/snapshot/active`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch active snapshot: ${res.statusText}`)
  }
  return res.json()
}

export async function createWorkspace(
  companyName: string,
  currency?: string,
  reportingPeriod?: string
): Promise<CompanyWorkspace> {
  const formData = new FormData()
  formData.append('companyName', companyName)
  if (currency) formData.append('currency', currency)
  if (reportingPeriod) formData.append('reportingPeriod', reportingPeriod)

  const res = await fetch(`${API_BASE_URL}/api/workspaces`, {
    method: 'POST',
    headers: getWorkspaceHeaders(),
    body: formData,
  })
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(detail)
  }
  return res.json()
}

export async function listWorkspaces(): Promise<CompanyWorkspace[]> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to list workspaces: ${res.statusText}`)
  }
  return res.json()
}

export async function getWorkspace(workspaceId: string): Promise<CompanyWorkspace> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to get workspace: ${res.statusText}`)
  }
  return res.json()
}

export async function deleteWorkspace(workspaceId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}`, {
    method: 'DELETE',
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(detail)
  }
  return res.json()
}

export async function deleteWorkspaceFile(
  workspaceId: string,
  fileId: string
): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/files/${fileId}`, {
    method: 'DELETE',
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(detail)
  }
  return res.json()
}

export async function fetchWorkspaceRuns(workspaceId: string, type?: string): Promise<any[]> {
  const query = type ? `?type=${type}` : ''
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/runs${query}`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch workspace runs: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchLatestRun(workspaceId: string, type: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/runs/latest?type=${type}`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch latest run: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchRun(workspaceId: string, runId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/runs/${runId}`, {
    headers: getWorkspaceHeaders(),
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch run: ${res.statusText}`)
  }
  return res.json()
}
