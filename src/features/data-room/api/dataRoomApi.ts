import { dataRoomRecords, dependencyFeeds } from '../data/dataRoomSeed'
import type { DataRoomResponse, DataRoomUploadResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

const getSeedFallback = (): DataRoomResponse => {
  const totalRequired = dataRoomRecords.filter((record) => record.status !== 'optional').length
  const connectedRequired = dataRoomRecords.filter(
    (record) => record.status === 'demo_available' || record.status === 'connected'
  ).length
  const missingRequired = dataRoomRecords.filter((record) => record.status === 'missing').length
  const readinessPercentage = totalRequired
    ? Math.round((connectedRequired / totalRequired) * 100)
    : 0

  return {
    records: dataRoomRecords,
    dependencies: dependencyFeeds,
    summary: {
      totalRequired,
      connectedRequired,
      missingRequired,
      readinessPercentage,
      dataMode: 'seed_only',
    },
  }
}

export async function fetchDataRoomReadiness(): Promise<DataRoomResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/data-room/demo-readiness`)

    if (!response.ok) {
      throw new Error(`Data Room readiness request failed: ${response.status}`)
    }

    return (await response.json()) as DataRoomResponse
  } catch (error) {
    console.warn('Using local Data Room readiness fallback.', error)
    return getSeedFallback()
  }
}

export async function uploadDataRoomMetadata(
  recordKey: string,
  file: File,
): Promise<DataRoomUploadResponse> {
  const formData = new FormData()
  formData.append('recordKey', recordKey)
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/data-room/demo-upload-metadata`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.json().then((d) => d.detail ?? response.statusText).catch(() => response.statusText)
    throw new Error(detail)
  }

  return (await response.json()) as DataRoomUploadResponse
}
