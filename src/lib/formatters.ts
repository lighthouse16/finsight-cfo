export function formatHKD(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  if (Math.abs(value) >= 1_000_000) return `HKD ${(value / 1_000_000).toFixed(2)}M`
  return `HKD ${value.toLocaleString()}`
}

export function formatPercent(value?: number | null, digits = 2): string {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(digits)}%`
}

export function formatBand(value?: string | null): string {
  if (!value) return 'Unavailable'
  return value.replace(/_/g, ' ')
}

export function formatNumber(value?: number | null, digits = 2): string {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return value.toFixed(digits)
}

export function formatMultiple(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'
  return `${value.toFixed(2)}x`
}

export function bandVariant(value?: string | null): 'signal' | 'caution' | 'neutral' {
  if (!value) return 'neutral'
  const normalized = value.toLowerCase().trim()
  
  if ([
    'strong', 'adequate', 'clear', 'low', 'ready_context', 'bank_review_ready', 
    'working_capital_priority', 'trade_cycle_priority', 'safe', 'pass', 'strong_fit'
  ].includes(normalized)) {
    return 'signal'
  }
  if ([
    'watch', 'constrained', 'elevated', 'stressed', 'high', 'needs_review', 
    'not_ready', 'risk_context_priority', 'warning', 'fail', 'grey', 'distress'
  ].includes(normalized)) {
    return 'caution'
  }
  return 'neutral'
}

export const variantForBand = bandVariant
