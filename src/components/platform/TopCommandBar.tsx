import { Menu, Search } from 'lucide-react'

type TopCommandBarProps = {
  onMenuToggle: () => void
}

export default function TopCommandBar({ onMenuToggle }: TopCommandBarProps) {
  return (
    <header className="sticky top-0 z-30 px-4 pb-2 pt-4 sm:px-6">
      <div className="flex items-center gap-3 rounded-[22px] border border-white/70 bg-[linear-gradient(145deg,rgba(255,255,255,0.76),rgba(231,240,244,0.66))] px-4 py-2.5 shadow-[0_12px_40px_rgba(8,17,31,0.12),0_4px_16px_rgba(8,17,31,0.06),inset_0_1px_0_rgba(255,255,255,0.82)] backdrop-blur-[20px] sm:px-5 sm:py-3">
        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={onMenuToggle}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-softform-text-secondary transition hover:bg-white/50 hover:text-softform-navy-900 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>

        {/* Workspace label */}
        <div className="hidden min-w-0 shrink-0 items-center gap-2.5 sm:flex">
          <span className="text-sm font-semibold text-softform-navy-950">
            FinSight Workspace
          </span>
        </div>

        {/* Search placeholder */}
        <div className="relative mx-auto hidden max-w-sm flex-1 md:block">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-softform-text-muted"
          />
          <input
            type="text"
            placeholder="Search workspace…"
            disabled
            className="w-full rounded-xl border border-white/50 bg-white/40 py-2 pl-9 pr-4 text-sm text-softform-text-primary placeholder:text-softform-text-muted/60 focus-visible:outline-none disabled:cursor-default"
          />
        </div>

        {/* Avatar placeholder */}
        <div
          className="ml-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-[11px] font-bold text-white/90"
          aria-label="User menu placeholder"
        >
          U
        </div>
      </div>
    </header>
  )
}
