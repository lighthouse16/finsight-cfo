import { type ElementType } from 'react'
import { Layers } from 'lucide-react'

type EmptyModuleStateProps = {
  icon?: ElementType
  moduleName: string
  description: string
}

export default function EmptyModuleState({
  icon: Icon = Layers,
  moduleName,
  description,
}: EmptyModuleStateProps) {
  return (
    <div className="softform-panel relative overflow-hidden rounded-[32px] p-8 sm:p-10 shadow-floating-panel bg-gradient-to-br from-white/95 via-softform-mist-50/70 to-softform-ice-100/50 border border-white">
      {/* Ambient glow backgrounds */}
      <div className="absolute -top-12 -left-12 w-48 h-48 bg-softform-aqua-300/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-softform-amber-300/10 rounded-full blur-3xl pointer-events-none" />

      <div className="mx-auto flex max-w-lg flex-col items-center text-center relative z-10">
        {/* Icon container */}
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-[20px] bg-softform-mist-100/80 text-softform-teal-deep/60 animate-pulse ring-4 ring-softform-aqua-300/10 shadow-soft-inner">
          <Icon size={28} strokeWidth={1.5} />
        </div>

        {/* Module description */}
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-softform-text-muted">
          {moduleName}
        </p>
        <p className="mb-6 text-base leading-relaxed text-softform-text-secondary">
          {description}
        </p>

        {/* Readiness message */}
        <div className="rounded-2xl bg-white/40 px-5 py-3 backdrop-blur-sm">
          <p className="text-sm leading-relaxed text-softform-text-muted">
            This workspace module will connect once product data integration is
            in place. No configuration is needed at this stage.
          </p>
        </div>
      </div>
    </div>
  )
}
