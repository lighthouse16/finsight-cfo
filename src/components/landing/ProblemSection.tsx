import { motion } from 'framer-motion'
import { FileSpreadsheet, AlertTriangle, HelpCircle, TrendingDown } from 'lucide-react'

export default function ProblemSection() {
  const painPoints = [
    {
      icon: FileSpreadsheet,
      title: 'Fragmented financial records',
      description: 'Bank exports, accounting files, and spreadsheets live in different places',
    },
    {
      icon: HelpCircle,
      title: 'Unclear funding readiness',
      description: 'Funding conversations happen before the business is ready',
    },
    {
      icon: TrendingDown,
      title: 'Metrics without actions',
      description: 'Dashboards show numbers, but not what to do next',
    },
    {
      icon: AlertTriangle,
      title: 'No source trail',
      description: 'Generic AI tools do not show assumptions or where insights come from',
    },
  ]

  return (
    <section className="softform-section py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Problem narrative */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="space-y-6"
          >
            <div className="softform-pill inline-flex items-center space-x-2 rounded-full px-4 py-2">
              <AlertTriangle className="w-4 h-4 text-softform-amber-500" />
              <span className="text-sm font-medium text-softform-navy-900">
                The Challenge
              </span>
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-softform-navy-950 leading-tight">
              Financial visibility is{' '}
              <span className="text-softform-amber-500">fragmented</span>
            </h2>

            <p className="text-lg text-softform-text-secondary leading-relaxed">
              SME finance teams face a common challenge: financial records are scattered
              across bank exports, accounting software, and spreadsheets. When funding
              conversations arise, it's unclear whether the business is ready.
            </p>

            <p className="text-lg text-softform-text-secondary leading-relaxed">
              Generic dashboards show metrics, but not next actions. AI tools provide
              answers, but not the assumptions or source trail behind them.
            </p>

            <div className="pt-4">
              <div className="softform-card rounded-[28px] p-6">
                <p className="text-base text-softform-navy-800 leading-relaxed italic">
                  "We had the data, but we didn't know if we were ready for a funding
                  conversation. We needed clarity, not just more charts."
                </p>
                <p className="mt-3 text-sm text-softform-text-muted">
                  — Finance lead at a growing SME
                </p>
              </div>
            </div>
          </motion.div>

          {/* Right: Pain points grid */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="grid sm:grid-cols-2 gap-6"
          >
            {painPoints.map((point, index) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="softform-card group rounded-[30px] p-6 transition-all hover:-translate-y-1 hover:shadow-floating-panel"
              >
                <div className="space-y-3">
                  <div className="w-12 h-12 bg-softform-mist-100 rounded-2xl flex items-center justify-center group-hover:bg-white/70 transition-colors shadow-[inset_0_1px_0_rgba(255,255,255,0.82)]">
                    <point.icon className="w-6 h-6 text-softform-navy-700" />
                  </div>

                  <h3 className="text-base font-semibold text-softform-navy-950">
                    {point.title}
                  </h3>

                  <p className="text-sm text-softform-text-secondary leading-relaxed">
                    {point.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  )
}
