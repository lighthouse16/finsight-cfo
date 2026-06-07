import type {
  DataRoomParsedRecordSet,
  DataRoomParseResponse,
  DataRoomUploadResponse,
} from '../types'

const DATA_ROOM_PREVIEW_STORAGE_KEY = 'finsight:data-room:preview-session:v1'

export interface DataRoomPreviewStorageState {
  parsedRecordSetsByKey: Record<string, DataRoomParsedRecordSet>
  uploadResultsByKey: Record<string, DataRoomUploadResponse>
  parseResultsByKey: Record<string, DataRoomParseResponse>
  updatedAt: string | null
}

const emptyState = (): DataRoomPreviewStorageState => ({
  parsedRecordSetsByKey: {},
  uploadResultsByKey: {},
  parseResultsByKey: {},
  updatedAt: null,
})

const canUseLocalStorage = () => {
  try {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
  } catch {
    return false
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

export function loadDataRoomPreviewState(): DataRoomPreviewStorageState {
  if (!canUseLocalStorage()) return emptyState()

  try {
    const rawValue = window.localStorage.getItem(DATA_ROOM_PREVIEW_STORAGE_KEY)
    if (!rawValue) return emptyState()

    const parsed = JSON.parse(rawValue) as unknown
    if (!isRecord(parsed)) return emptyState()

    return {
      parsedRecordSetsByKey: isRecord(parsed.parsedRecordSetsByKey)
        ? (parsed.parsedRecordSetsByKey as Record<string, DataRoomParsedRecordSet>)
        : {},
      uploadResultsByKey: isRecord(parsed.uploadResultsByKey)
        ? (parsed.uploadResultsByKey as Record<string, DataRoomUploadResponse>)
        : {},
      parseResultsByKey: isRecord(parsed.parseResultsByKey)
        ? (parsed.parseResultsByKey as Record<string, DataRoomParseResponse>)
        : {},
      updatedAt: typeof parsed.updatedAt === 'string' ? parsed.updatedAt : null,
    }
  } catch {
    return emptyState()
  }
}

export function saveDataRoomPreviewState(state: Omit<DataRoomPreviewStorageState, 'updatedAt'>) {
  if (!canUseLocalStorage()) return

  try {
    const stateToSave: DataRoomPreviewStorageState = {
      ...state,
      updatedAt: new Date().toISOString(),
    }
    window.localStorage.setItem(DATA_ROOM_PREVIEW_STORAGE_KEY, JSON.stringify(stateToSave))
  } catch {
    // Ignore localStorage quota/security failures; preview still works in memory.
  }
}

export function clearDataRoomPreviewState() {
  if (!canUseLocalStorage()) return

  try {
    window.localStorage.removeItem(DATA_ROOM_PREVIEW_STORAGE_KEY)
  } catch {
    // Ignore localStorage security failures.
  }
}
