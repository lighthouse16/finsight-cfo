import { AlertTriangle, RotateCw } from 'lucide-react'

interface ServiceErrorStateProps {
  message?: string
  onRetry: () => void
}

export default function ServiceErrorState({
  message,
  onRetry,
}: ServiceErrorStateProps) {
  return (
    <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600 border border-red-100">
          <AlertTriangle size={24} />
        </div>
        <p className="mb-2 text-lg font-semibold text-softform-navy-950">Service Connection Issue</p>
        <p className="mb-6 text-sm text-softform-text-secondary leading-relaxed">
          {message || 'Unable to connect to the requested services.'}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
        >
          <RotateCw size={14} />
          Retry Connection
        </button>
      </div>
    </div>
  )
}
