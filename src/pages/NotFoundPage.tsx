import { Link, useLocation } from 'react-router-dom'
import { MapPinOff } from 'lucide-react'
import PageHeader from '../components/platform/PageHeader'

export default function NotFoundPage() {
  const location = useLocation()
  const isPlatformRoute = location.pathname.startsWith('/platform')

  return (
    <div className="py-6">
      <PageHeader
        title="Page not found"
        subtitle={`The path "${location.pathname}" does not match any available workspace route.`}
      />

      <div className="softform-card rounded-[32px] p-8 sm:p-10">
        <div className="mx-auto flex max-w-lg flex-col items-center text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-[20px] bg-softform-cream/60 text-softform-amber-500/60">
            <MapPinOff size={28} strokeWidth={1.5} />
          </div>

          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-softform-text-muted">
            Route unavailable
          </p>
          <p className="mb-6 text-base leading-relaxed text-softform-text-secondary">
            This page may not exist yet or the URL may be incorrect. Use the
            sidebar navigation to reach an available workspace area.
          </p>

          <Link
            to={isPlatformRoute ? '/platform/market-watch' : '/'}
            className="inline-flex items-center justify-center rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-6 py-2.5 text-sm font-medium text-white shadow-[0_8px_24px_rgba(8,17,31,0.28)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_32px_rgba(8,17,31,0.34)]"
          >
            {isPlatformRoute ? 'Go to Market Watch' : 'Back to home'}
          </Link>
        </div>
      </div>
    </div>
  )
}
