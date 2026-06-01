import { Link } from 'react-router-dom'

type PlatformPlaceholderPageProps = {
  title?: string
  eyebrow?: string
  description?: string
  isNotFound?: boolean
}

const platformLinks = [
  { label: 'Market Watch', href: '/platform/market-watch' },
  { label: 'Cashflow', href: '/platform/cashflow' },
  { label: 'Credit Readiness', href: '/platform/credit-readiness' },
  { label: 'Advisor', href: '/platform/advisor' },
  { label: 'AI CFO', href: '/platform/ai-cfo' },
  { label: 'Reports', href: '/platform/reports' },
  { label: 'Data Room', href: '/platform/data-room' },
  { label: 'Settings', href: '/platform/settings' },
]

export default function PlatformPlaceholderPage({
  title = 'Platform workspace',
  eyebrow = 'Platform foundation',
  description = 'This product area is prepared for future build-out. The full workspace UI will be added when the product scope is ready.',
  isNotFound = false,
}: PlatformPlaceholderPageProps) {
  return (
    <main className="softform-page min-h-screen px-4 py-6 text-softform-text-primary sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl items-center justify-center">
        <div className="softform-shell w-full rounded-[44px] p-6 sm:p-8 lg:p-10">
          <div className="mb-10 flex flex-col gap-4 border-b border-white/70 pb-6 sm:flex-row sm:items-center sm:justify-between">
            <Link to="/" className="flex items-center gap-3 text-softform-navy-950">
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-sm font-bold text-white shadow-navy-card">
                FS
              </span>
              <span className="text-lg font-semibold">FinSight CFO</span>
            </Link>
            <Link
              to="/"
              className="softform-pill inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-medium text-softform-navy-900 transition hover:-translate-y-0.5"
            >
              Back to landing
            </Link>
          </div>

          <div className="grid gap-8 lg:grid-cols-[1fr_320px] lg:items-start">
            <div className="space-y-6">
              <div className="softform-pill inline-flex rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-softform-teal-deep">
                {isNotFound ? 'Not found' : eyebrow}
              </div>
              <div className="space-y-4">
                <h1 className="max-w-3xl text-4xl font-bold leading-tight text-softform-navy-950 sm:text-5xl">
                  {isNotFound ? 'This route is not available yet' : title}
                </h1>
                <p className="max-w-2xl text-base leading-7 text-softform-text-secondary sm:text-lg">
                  {isNotFound
                    ? 'The page you visited does not exist in the current FinSight CFO route map. Use the links below to return to a prepared platform area.'
                    : description}
                </p>
              </div>
              <div className="softform-card rounded-[28px] p-5">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-softform-text-muted">
                  Status
                </p>
                <p className="mt-2 text-softform-navy-900">
                  Placeholder only. No product workflow, backend integration, or finance logic has been added.
                </p>
              </div>
            </div>

            <nav className="softform-card rounded-[32px] p-4" aria-label="Platform placeholders">
              <p className="px-3 pb-3 text-xs font-semibold uppercase tracking-[0.2em] text-softform-text-muted">
                Platform routes
              </p>
              <div className="space-y-2">
                {platformLinks.map((link) => (
                  <Link
                    key={link.href}
                    to={link.href}
                    className="block rounded-2xl px-3 py-3 text-sm font-medium text-softform-navy-900 transition hover:bg-white/60"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </nav>
          </div>
        </div>
      </section>
    </main>
  )
}
