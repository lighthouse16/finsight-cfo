import { motion } from 'framer-motion'
import { TrendingUp, Target, MessageSquare, FileText, BarChart3 } from 'lucide-react'

export default function IntelligenceModules() {
  const modules = [
    {
      icon: BarChart3,
      title: 'Cashflow Cockpit',
      audience: 'Finance teams',
      question: 'Is our cashflow stable enough for growth?',
      description: 'Revenue patterns, receivables pressure, working capital trends, and seasonal signals',
      color: 'from-fintech-blue to-fintech-cyan',
    },
    {
      icon: Target,
      title: 'Credit Readiness',
      audience: 'CFOs and founders',
      question: 'Are we ready for a funding conversation?',
      description: 'Debt capacity, documentation gaps, risk signals, and funding readiness score',
      color: 'from-fintech-cyan to-fintech-teal',
    },
    {
      icon: TrendingUp,
      title: 'Advisor Recommendations',
      audience: 'Leadership teams',
      question: 'What should we prioritize next?',
      description: 'CFO-grade next actions with source trails, assumptions, and impact estimates',
      color: 'from-fintech-teal to-fintech-emerald',
    },
    {
      icon: MessageSquare,
      title: 'AI CFO Assistant',
      audience: 'Finance stakeholders',
      question: 'Why is this recommendation important?',
      description: 'Explainable insights with provenance trails and assumption visibility',
      color: 'from-fintech-emerald to-fintech-blue',
    },
    {
      icon: FileText,
      title: 'Funding Report',
      audience: 'Investor relations',
      question: 'How do we present our financial position?',
      description: 'Bank-review-ready summaries with clear signals and documented assumptions',
      color: 'from-fintech-blue to-fintech-navy',
    },
  ]

  return (
    <section id="intelligence" className="softform-section py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="softform-pill inline-flex items-center space-x-2 rounded-full px-4 py-2 mb-6">
            <BarChart3 className="w-4 h-4 text-softform-teal-deep" />
            <span className="text-sm font-medium text-softform-navy-900">
              Intelligence Modules
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-softform-navy-950 mb-6 leading-tight">
            Financial intelligence for every{' '}
            <span className="text-softform-teal-deep">stakeholder</span>
          </h2>

          <p className="text-lg text-softform-text-secondary leading-relaxed">
            Modular insights designed for different questions and decision-makers
          </p>
        </motion.div>

        {/* Modules grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {modules.map((module, index) => (
            <motion.div
              key={module.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="softform-card group relative rounded-[32px] p-8 transition-all hover:-translate-y-1 hover:shadow-floating-panel"
            >
              {/* Icon */}
              <div className={`w-16 h-16 bg-gradient-to-br ${module.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-105 transition-transform shadow-[0_16px_34px_rgba(18,38,53,0.14)]`}>
                <module.icon className="w-8 h-8 text-white" />
              </div>

              {/* Content */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-softform-navy-950 mb-2">
                    {module.title}
                  </h3>
                  <p className="text-sm text-softform-text-muted font-medium">
                    {module.audience}
                  </p>
                </div>

                <div className="p-4 bg-white/62 rounded-2xl border border-white/70 shadow-[inset_0_1px_0_rgba(255,255,255,0.82)]">
                  <p className="text-sm text-softform-navy-800 italic leading-relaxed">
                    "{module.question}"
                  </p>
                </div>

                <p className="text-sm text-softform-text-secondary leading-relaxed">
                  {module.description}
                </p>
              </div>

              {/* Hover indicator */}
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-3 h-3 bg-softform-teal-500 rounded-full animate-pulse" />
              </div>

              {/* Abstract visualization */}
              <div className="mt-6 pt-6 border-t border-white/70">
                <div className="flex items-end space-x-2 h-12">
                  {[40, 65, 45, 80, 55].map((height, i) => (
                    <motion.div
                      key={i}
                      initial={{ height: 0 }}
                      whileInView={{ height: `${height}%` }}
                      viewport={{ once: true }}
                      transition={{ delay: index * 0.1 + i * 0.05 }}
                      className={`flex-1 bg-gradient-to-t ${module.color} rounded-t-xl opacity-20 group-hover:opacity-34 transition-opacity`}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-16 text-center"
        >
          <p className="text-softform-text-secondary mb-6">
            Each module provides explainable insights with source trails and assumptions
          </p>
          <a
            href="#explainability"
            className="inline-flex items-center space-x-2 text-softform-navy-900 font-medium hover:text-softform-teal-deep transition-colors"
          >
            <span>Learn about explainability</span>
            <TrendingUp className="w-4 h-4" />
          </a>
        </motion.div>
      </div>
    </section>
  )
}
