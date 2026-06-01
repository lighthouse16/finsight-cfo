import { motion } from 'framer-motion'
import { TrendingUp, AlertCircle, CheckCircle2, ArrowRight, FileText, BarChart3 } from 'lucide-react'

export default function ProductPreview() {
  return (
    <section id="product" className="py-20 lg:py-32 relative overflow-hidden">
      <div className="absolute inset-x-4 inset-y-8 rounded-[56px] bg-[radial-gradient(circle_at_88%_12%,rgba(32,169,154,0.22),transparent_32%),linear-gradient(145deg,#0d1726_0%,#132337_52%,#1c324b_100%)] shadow-navy-card" />
      <div className="absolute inset-0 opacity-[0.04]" style={{
        backgroundImage: `linear-gradient(to right, #85d9ce 1px, transparent 1px),
                         linear-gradient(to bottom, #85d9ce 1px, transparent 1px)`,
        backgroundSize: '4rem 4rem'
      }} />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white/10 rounded-full border border-white/10 mb-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]">
            <BarChart3 className="w-4 h-4 text-softform-aqua-300" />
            <span className="text-sm font-medium text-white">
              Platform
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
            CFO Intelligence{' '}
            <span className="text-softform-aqua-300">Cockpit</span>
          </h2>

          <p className="text-lg text-white/70 leading-relaxed">
            A unified view of cashflow signals, credit readiness, and CFO-grade recommendations
          </p>
        </motion.div>

        {/* Product cockpit */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-5xl mx-auto"
        >
          <div className="softform-shell rounded-[42px] overflow-hidden depth-layer-2 hover-lift">
            {/* Cockpit header */}
            <div className="bg-[linear-gradient(145deg,rgba(255,255,255,0.74),rgba(231,240,244,0.64))] px-6 py-4 border-b border-white/70">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-softform-teal-500 rounded-full animate-pulse" />
                  <span className="text-softform-navy-950 font-semibold">Financial Intelligence Dashboard</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-softform-text-secondary text-sm">Last updated: Today</span>
                </div>
              </div>
            </div>

            {/* Cockpit content */}
            <div className="p-6 lg:p-8 space-y-6">
              {/* Executive summary */}
              <div className="grid md:grid-cols-3 gap-4">
                <div className="softform-card rounded-[26px] p-5 hover-lift">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-fintech-navy/60 uppercase tracking-wide">
                      Cashflow Signal
                    </span>
                    <TrendingUp className="w-5 h-5 text-fintech-emerald" />
                  </div>
                  <p className="text-2xl font-bold text-fintech-navy mb-1">Stable</p>
                  <p className="text-xs text-fintech-navy/60">with receivables pressure</p>
                </div>

                <div className="softform-card rounded-[26px] p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-fintech-navy/60 uppercase tracking-wide">
                      Credit Readiness
                    </span>
                    <CheckCircle2 className="w-5 h-5 text-fintech-cyan" />
                  </div>
                  <p className="text-2xl font-bold text-fintech-navy mb-1">Strengthening</p>
                  <p className="text-xs text-fintech-navy/60">Documentation gap detected</p>
                </div>

                <div className="softform-card rounded-[26px] p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-fintech-navy/60 uppercase tracking-wide">
                      Receivables Pressure
                    </span>
                    <AlertCircle className="w-5 h-5 text-fintech-amber" />
                  </div>
                  <p className="text-2xl font-bold text-fintech-navy mb-1">Elevated</p>
                  <p className="text-xs text-fintech-navy/60">45-day collection period</p>
                </div>
              </div>

              {/* Advisor action */}
              <div className="softform-navy-card rounded-[28px] p-6 text-white">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold uppercase tracking-wide mb-2">
                      Advisor Action
                    </h3>
                    <p className="text-lg font-medium leading-relaxed">
                      Prioritize collections before adding new debt
                    </p>
                  </div>
                </div>
              </div>

              {/* CFO Insight */}
              <div className="softform-navy-card rounded-[28px] p-6 text-white">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-white/10 rounded-2xl flex items-center justify-center">
                    <span className="text-sm font-bold">AI</span>
                  </div>
                  <div className="flex-1 space-y-3">
                    <h3 className="text-sm font-semibold uppercase tracking-wide">
                      CFO Insight
                    </h3>
                    <p className="text-base leading-relaxed text-white/90">
                      Receivables concentration is the first constraint to resolve. Current
                      collection period of 45 days creates working capital pressure that limits
                      debt capacity.
                    </p>
                    <div className="pt-3 border-t border-white/10">
                      <div className="flex items-center space-x-2 text-white/60 text-sm">
                        <FileText className="w-4 h-4" />
                        <span>Source trail: Records → Signal → Recommendation</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Assumptions */}
              <div className="softform-card rounded-[28px] p-6">
                <h3 className="text-sm font-semibold text-fintech-navy/60 uppercase tracking-wide mb-4">
                  Assumptions
                </h3>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-fintech-cyan rounded-full mt-2 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-fintech-navy">Revenue growth: 15% YoY</p>
                      <p className="text-xs text-fintech-navy/60 mt-1">Based on 12-month trend</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-fintech-teal rounded-full mt-2 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-fintech-navy">Collection period: 45 days</p>
                      <p className="text-xs text-fintech-navy/60 mt-1">Average from receivables data</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-fintech-emerald rounded-full mt-2 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-fintech-navy">Working capital ratio: 1.8x</p>
                      <p className="text-xs text-fintech-navy/60 mt-1">Current assets / current liabilities</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-fintech-blue rounded-full mt-2 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-fintech-navy">Debt service coverage: 2.1x</p>
                      <p className="text-xs text-fintech-navy/60 mt-1">Operating income / debt obligations</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Funding readiness */}
              <div className="softform-card rounded-[28px] p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-fintech-navy/60 uppercase tracking-wide">
                    Funding Readiness
                  </h3>
                  <span className="text-2xl font-bold text-fintech-navy">65%</span>
                </div>
                <div className="h-3 bg-fintech-navy/10 rounded-full overflow-hidden mb-3">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: '65%' }}
                    viewport={{ once: true }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full bg-gradient-to-r from-softform-teal-deep to-softform-teal-500"
                  />
                </div>
                <p className="text-sm text-fintech-navy/70">
                  Next action: Improve collections visibility before increasing debt exposure
                </p>
              </div>
            </div>
          </div>
        </motion.div>


      </div>
    </section>
  )
}
