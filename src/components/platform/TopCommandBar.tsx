import { Menu, Search, Bell } from 'lucide-react'

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
        <div className="group relative mx-auto hidden max-w-sm flex-1 md:block">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-softform-text-muted opacity-60"
          />
          <input
            id="workspace-search"
            name="workspace-search"
            type="text"
            placeholder="Search workspace…"
            disabled
            aria-label="Search workspace"
            className="w-full rounded-xl border border-white/50 bg-white/40 py-2 pl-9 pr-4 text-sm text-softform-text-primary placeholder:text-softform-text-muted/60 opacity-60 focus-visible:outline-none disabled:cursor-default"
          />
          <span
            role="tooltip"
            className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-softform-navy-950 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-white opacity-0 shadow-md transition-opacity duration-200 group-hover:opacity-100"
          >
            Search coming soon
          </span>
        </div>

        {/* Notification bell */}
        <div className="group relative ml-auto sm:ml-0">
          <button
            type="button"
            disabled
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/50 bg-white/30 text-softform-text-muted opacity-60 transition hover:bg-white/50 hover:text-softform-navy-950 disabled:cursor-default"
            aria-label="Notifications"
          >
            <Bell size={16} />
          </button>
          <span
            role="tooltip"
            className="pointer-events-none absolute right-0 top-full z-50 mt-2 whitespace-nowrap rounded-lg bg-softform-navy-950 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-white opacity-0 shadow-md transition-opacity duration-200 group-hover:opacity-100"
          >
            Notifications coming soon
          </span>
        </div>

        {/* Avatar placeholder */}
        <div className="relative shrink-0">
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-[11px] font-bold text-white/90 shadow-sm ring-2 ring-white/80 transition hover:ring-softform-teal-500/50"
            aria-label="User menu placeholder"
          >
            U
          </button>
          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-softform-emerald-soft ring-2 ring-white" aria-hidden="true" />
        </div>
      </div>
    </header>
  )
}
