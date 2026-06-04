import { motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  ChevronRight,
  Database,
  FileText,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react'

const navItems = ['Product', 'Intelligence', 'Solutions', 'Pricing', 'Resources']

function HeroPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.12, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      className="relative mx-auto w-full max-w-[610px] [perspective:1200px]"
    >
      <div className="absolute -inset-5 rounded-[44px] bg-[radial-gradient(circle_at_38%_32%,rgba(133,217,206,0.22),transparent_38%),radial-gradient(circle_at_76%_24%,rgba(241,207,120,0.18),transparent_34%)] blur-2xl" />

      <div className="group relative min-h-[440px] overflow-visible rounded-[38px] bg-[radial-gradient(circle_at_82%_18%,rgba(133,217,206,0.28),transparent_38%),radial-gradient(circle_at_18%_88%,rgba(246,223,157,0.28),transparent_34%),linear-gradient(145deg,rgba(255,255,255,0.72),rgba(232,244,241,0.68))] p-2 shadow-hero-shell ring-1 ring-white/70 transition-all duration-500 [transform-style:preserve-3d] hover:shadow-[rgba(18,38,53,0.18)_30px_50px_25px_-40px,rgba(8,17,31,0.12)_0_28px_34px_0px] hover:[transform:rotate3d(1,1,0,14deg)]">
        <div className="absolute inset-2 overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(0deg,rgba(255,255,255,0.32),rgba(255,255,255,0.82))] shadow-[inset_0_1px_0_rgba(255,255,255,0.95)] transition-all duration-500 [transform:translate3d(0,0,25px)] group-hover:[transform:translate3d(0,0,38px)]" />



        <div className="relative z-10 grid min-h-[440px] gap-3 p-4 transition-all duration-500 [transform:translate3d(0,0,26px)] [transform-style:preserve-3d] sm:grid-cols-[1.08fr_0.92fr] sm:p-5">
          <div className="flex min-w-0 flex-col gap-4 [transform-style:preserve-3d]">
            <div className="min-h-[230px] rounded-[24px] border border-white/72 bg-white/78 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.10)] backdrop-blur-xl transition-all delay-[100ms] duration-300 [transform:translate3d(0,0,26px)] group-hover:shadow-[rgba(15,23,42,0.18)_-8px_26px_18px_-10px] group-hover:[transform:translate3d(0,0,76px)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Cashflow Signal</p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-softform-teal-deep">Stable</p>
                  <p className="mt-1 text-sm text-slate-500">Receivables need attention</p>
                </div>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-softform-mist-100 text-softform-teal-deep shadow-[0_12px_24px_rgba(32,169,154,0.14)] transition-all delay-[400ms] duration-300 [transform:translate3d(0,0,0px)] group-hover:[transform:translate3d(0,0,118px)]">
                  <TrendingUp className="h-5 w-5" />
                </span>
              </div>

              <div className="relative mt-4 h-28 overflow-hidden rounded-2xl bg-gradient-to-b from-softform-mist-50 to-white transition-all delay-[220ms] duration-300 [transform:translate3d(0,0,0px)] group-hover:[transform:translate3d(0,0,52px)]">
                <svg viewBox="0 0 360 150" className="absolute inset-0 h-full w-full">
                  <defs>
                    <linearGradient id="cashflowFill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#85d9ce" stopOpacity="0.34" />
                      <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path d="M0 112 C42 102 58 82 94 90 C126 98 142 62 177 70 C210 78 226 112 258 78 C292 42 318 48 360 24 L360 150 L0 150 Z" fill="url(#cashflowFill)" />
                  <path d="M0 112 C42 102 58 82 94 90 C126 98 142 62 177 70 C210 78 226 112 258 78 C292 42 318 48 360 24" fill="none" stroke="#20a99a" strokeWidth="4" />
                  <circle cx="360" cy="24" r="5" fill="#0e615b" />
                </svg>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/72 bg-white/72 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.09)] backdrop-blur-xl transition-all delay-[600ms] duration-300 [transform:translate3d(0,0,26px)] group-hover:shadow-[rgba(15,23,42,0.18)_-6px_22px_18px_-12px] group-hover:[transform:translate3d(0,0,88px)]">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Uploaded Records</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-600 [transform-style:preserve-3d]">
                {[
                  ['Bank exports', Database],
                  ['Accounting files', FileText],
                  ['Invoices', FileText],
                  ['Cashflow sheets', BarChart3],
                ].map(([label, Icon], index) => {
                  const LucideIcon = Icon as typeof Database
                  return (
                    <div key={label as string} className="flex min-w-0 items-center gap-2 rounded-xl bg-white/66 px-3 py-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition-all duration-300 group-hover:[transform:translate3d(0,0,22px)]" style={{ transitionDelay: `${260 + index * 80}ms` }}>
                      <LucideIcon className="h-4 w-4 shrink-0 text-softform-teal-500" />
                      <span className="truncate">{label as string}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="flex min-w-0 flex-col gap-4 [transform-style:preserve-3d]">
            <div className="rounded-[24px] border border-white/72 bg-white/76 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.10)] backdrop-blur-xl transition-all delay-[400ms] duration-300 [transform:translate3d(0,0,40px)] [transform-style:preserve-3d] group-hover:shadow-[rgba(15,23,42,0.18)_-8px_24px_22px_-10px] group-hover:[transform:translate3d(0,0,112px)]">
              <div className="flex items-start justify-between gap-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Credit Readiness</p>
                <span className="grid h-10 w-10 shrink-0 place-content-center rounded-2xl bg-softform-ice-100 text-softform-navy-700 shadow-[0_12px_24px_rgba(28,50,75,0.12)] transition-all delay-[700ms] duration-300 [transform:translate3d(0,0,12px)] group-hover:[transform:translate3d(0,0,122px)]">
                  <ShieldCheck className="h-5 w-5" />
                </span>
              </div>
              <div className="mt-4 flex items-center gap-4 [transform-style:preserve-3d]">
                <div className="relative flex h-[82px] w-[82px] shrink-0 items-center justify-center rounded-full bg-[conic-gradient(from_220deg,#1c324b_0_32%,#20a99a_32%_72%,#e7f0f4_72%_100%)] shadow-[0_14px_28px_rgba(32,169,154,0.15)] transition-all delay-[520ms] duration-300 [transform:translate3d(0,0,10px)] group-hover:[transform:translate3d(0,0,86px)]">
                  <div className="absolute h-[54px] w-[54px] rounded-full bg-white transition-all delay-[620ms] duration-300 [transform:translate3d(0,0,8px)] group-hover:[transform:translate3d(0,0,44px)]" />
                  <span className="relative text-xl font-bold text-slate-900 transition-all delay-[720ms] duration-300 [transform:translate3d(0,0,14px)] group-hover:[transform:translate3d(0,0,112px)]">72%</span>
                </div>
                <div className="min-w-0 transition-all delay-[650ms] duration-300 [transform:translate3d(0,0,16px)] group-hover:[transform:translate3d(0,0,96px)]">
                  <p className="text-lg font-bold text-softform-navy-800">Strengthening</p>
                  <p className="mt-1 text-sm leading-snug text-slate-500">Ready for lender review</p>
                </div>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_88%_12%,rgba(32,169,154,0.22),transparent_32%),linear-gradient(145deg,#0d1726_0%,#132337_52%,#1c324b_100%)] p-4 text-white shadow-navy-card transition-all delay-[800ms] duration-300 [transform:translate3d(0,0,48px)] group-hover:shadow-[rgba(8,17,31,0.30)_-8px_30px_20px_-10px] group-hover:[transform:translate3d(0,0,132px)]">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-100">Next CFO Action</p>
                  <p className="mt-2 text-xl font-bold leading-tight">Improve collections visibility.</p>
                  <p className="mt-2 text-sm leading-relaxed text-blue-100">Reduce receivables pressure before adding new debt.</p>
                </div>
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/16 transition-all delay-500 duration-300 [transform:translate3d(0,0,8px)] group-hover:[transform:translate3d(0,0,46px)]">
                  <Zap className="h-5 w-5" />
                </span>
              </div>
              <a id="hero-action-plan-link" href="#product" className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-softform-navy-900 transition-all delay-500 duration-300 [transform:translate3d(0,0,8px)] hover:translate-y-[-1px] group-hover:[transform:translate3d(0,0,44px)]">
                View Plan
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function CinematicHero() {
  return (
    <section id="top" className="relative min-h-[100dvh] overflow-hidden bg-transparent">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_4%_6%,rgba(241,207,120,0.20),transparent_28%),radial-gradient(circle_at_82%_8%,rgba(133,217,206,0.22),transparent_34%),linear-gradient(115deg,rgba(244,250,247,0.72),rgba(231,240,244,0.48))]" />

      <header className="relative z-50 px-4 pt-4">
        <div className="softform-pill mx-auto flex h-[60px] max-w-[1340px] items-center justify-between rounded-full px-5 lg:px-7">
          <a id="header-logo-link" href="#top" className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-xs font-bold text-white shadow-[0_14px_30px_rgba(8,17,31,0.18)] ring-1 ring-white/40">FS</span>
            <span className="text-lg font-bold tracking-tight text-softform-navy-950">FinSight CFO</span>
          </a>

          <nav aria-label="Primary" className="hidden items-center gap-9 lg:flex">
            {navItems.map((item) => (
              <a key={item} id={`nav-${item.toLowerCase()}`} href={`#${item.toLowerCase()}`} className="text-sm font-semibold text-softform-text-secondary transition hover:text-softform-navy-950">
                {item}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <a id="header-login" href="/login" className="hidden text-sm font-semibold text-softform-text-secondary hover:text-softform-navy-950 sm:inline-flex">Log in</a>
            <a id="header-get-started" href="/signup" className="inline-flex items-center gap-2 rounded-full bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-5 py-2.5 text-sm font-bold text-white shadow-[0_16px_36px_rgba(8,17,31,0.20)] transition hover:-translate-y-0.5">
              Get Started
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-[1340px] px-5 pb-4 pt-6 lg:px-8 lg:pt-8">
        <div className="grid items-center gap-8 lg:grid-cols-[0.9fr_1.1fr] xl:gap-10">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.62 }} className="max-w-[640px] py-2">
            <div className="softform-pill inline-flex items-center gap-2 rounded-full px-4 py-2">
              <Sparkles className="h-4 w-4 text-softform-teal-deep" />
              <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-softform-navy-700">AI Financial Intelligence Platform</span>
            </div>

            <h1 className="mt-7 max-w-[620px] text-balance text-[42px] font-bold leading-[1.08] tracking-[-0.045em] text-softform-navy-950 sm:text-5xl lg:text-[52px] lg:leading-[1.06]">
              Financial clarity for SME <span className="text-softform-navy-800">cashflow</span>, <span className="text-softform-teal-deep">credit</span>, and <span className="text-softform-teal-500">funding decisions.</span>
            </h1>

            <p className="mt-6 max-w-[600px] text-[17px] leading-8 text-softform-text-secondary">
              FinSight CFO turns uploaded financial records into clear cashflow signals, credit-readiness insights, and CFO-grade next actions.
            </p>

            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <a id="hero-primary-cta" href="/signup" className="inline-flex min-w-[215px] items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-6 py-3.5 text-base font-bold text-white shadow-[0_18px_42px_rgba(8,17,31,0.22)] transition hover:-translate-y-0.5 active:scale-[0.98]">
                Open CFO Cockpit
                <ArrowRight className="h-5 w-5" />
              </a>
              <a id="hero-secondary-cta" href="#product" className="softform-pill inline-flex min-w-[215px] items-center justify-center gap-2 rounded-2xl px-6 py-3.5 text-base font-bold text-softform-navy-900 transition hover:-translate-y-0.5">
                Explore Product
                <ChevronRight className="h-5 w-5" />
              </a>
            </div>

          </motion.div>

          <HeroPanel />
        </div>

      </main>
    </section>
  )
}
