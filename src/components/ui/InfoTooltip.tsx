import { Info } from 'lucide-react'
import { useId } from 'react'

type InfoTooltipProps = {
  label: string
  content: string
}

export default function InfoTooltip({ label, content }: InfoTooltipProps) {
  const tooltipId = useId()

  return (
    <span className="group relative inline-flex align-middle">
      <button
        type="button"
        aria-label={label}
        aria-describedby={tooltipId}
        className="mt-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/70 bg-white/55 text-softform-text-muted shadow-[0_6px_18px_rgba(8,17,31,0.07)] backdrop-blur-xl transition-all duration-200 hover:-translate-y-0.5 hover:border-white hover:bg-white/80 hover:text-softform-navy-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-softform-teal-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent"
      >
        <Info className="h-3 w-3" aria-hidden="true" strokeWidth={2.2} />
      </button>
      <span
        id={tooltipId}
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 w-max max-w-[calc(100vw-2rem)] -translate-x-1/2 whitespace-nowrap rounded-2xl border border-white/70 bg-white/82 px-3.5 py-2 text-left text-xs font-semibold leading-normal text-softform-navy-950 opacity-0 shadow-floating-panel backdrop-blur-xl transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100 sm:left-0 sm:translate-x-0"
      >
        {content}
      </span>
    </span>
  )
}
