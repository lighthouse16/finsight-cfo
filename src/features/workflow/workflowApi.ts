export type WorkflowStageStatus =
  | 'preview_ready'
  | 'demo_fallback'
  | 'passed'
  | 'completed'
  | 'review'
  | 'unavailable'

export type WorkflowStage = {
  stage: number
  name: string
  status: WorkflowStageStatus
  inputs: string[]
  outputs: string[]
  summary: string
  warnings: string[]
}

export type WorkflowStageCoverage = {
  totalStages: number
  completedStages: number
  reviewStages: number
  unavailableStages: number
}

export type BochkWorkflowRun = {
  workflowId: string
  mode: string
  ranAt: string
  dataSource: string
  company: {
    companyId: string
    companyName: string
    currency: string
    reportingPeriod: string
  }
  stageCoverage: WorkflowStageCoverage
  stages: WorkflowStage[]
  disclaimer: string
}

import { API_BASE_URL } from '../../lib/apiBase'


export async function getBochkWorkflowRun(): Promise<BochkWorkflowRun> {
  const response = await fetch(`${API_BASE_URL}/api/workflow/run`, {
    signal: AbortSignal.timeout(10000),
  })

  if (!response.ok) {
    throw new Error(`BOCHK workflow API returned status ${response.status}`)
  }

  return response.json()
}
