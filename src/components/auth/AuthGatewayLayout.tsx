import type { ReactNode } from 'react'

interface AuthGatewayLayoutProps {
  children: ReactNode
}

export default function AuthGatewayLayout({ children }: AuthGatewayLayoutProps) {
  return (
    <main className="softform-page relative flex min-h-dvh overflow-hidden text-softform-text-primary">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="softform-ambient left-[12%] top-[10%] h-72 w-72 bg-softform-teal-300/18" />
        <div className="softform-ambient bottom-[4%] right-[12%] h-80 w-80 bg-softform-amber-300/14" />
        <div className="absolute left-1/2 top-[14%] h-px w-[min(520px,70vw)] -translate-x-1/2 bg-gradient-to-r from-transparent via-softform-teal-500/20 to-transparent" />
      </div>

      <header className="absolute left-0 right-0 top-0 z-20 flex items-center justify-center px-5 py-4 sm:px-8">
        <div className="flex items-center gap-3" aria-label="FinSight CFO">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-xs font-bold text-white shadow-[0_14px_30px_rgba(8,17,31,0.18)] ring-1 ring-white/40">
            FS
          </span>
          <span className="text-base font-bold tracking-tight text-softform-navy-950 sm:text-lg">FinSight CFO</span>
        </div>
      </header>

      <section className="relative z-10 flex min-h-dvh w-full items-center justify-center px-5 py-16 sm:px-6">
        {children}
      </section>
    </main>
  )
}
