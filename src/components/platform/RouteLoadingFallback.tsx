type RouteLoadingFallbackProps = {
  copy?: string
}

export default function RouteLoadingFallback({
  copy = 'Preparing workspace...',
}: RouteLoadingFallbackProps) {
  return (
    <div
      className="softform-card my-4 flex min-h-[320px] items-center justify-center overflow-hidden rounded-[32px] p-8 text-center"
      role="status"
      aria-live="polite"
    >
      <div className="relative flex flex-col items-center gap-5">
        <div className="absolute inset-0 -z-10 rounded-full bg-softform-teal-500/10 blur-3xl" />
        <div className="flex h-16 w-16 items-center justify-center rounded-full border border-white/70 bg-white/65 shadow-soft-inner">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-softform-aqua-300 via-softform-teal-500 to-softform-teal-deep animate-pulse shadow-[0_12px_30px_rgba(14,97,91,0.20)]" />
        </div>
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-softform-text-muted">
            Loading route
          </p>
          <p className="text-lg font-semibold text-softform-navy-950">{copy}</p>
        </div>
      </div>
    </div>
  )
}
