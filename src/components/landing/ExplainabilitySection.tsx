import { motion } from 'framer-motion'
import { FileText, ArrowRight, Target, CheckCircle2 } from 'lucide-react'

export default function ExplainabilitySection() {
  const trail = [
    {
      icon: FileText,
      label: 'Financial Records',
      description: 'Bank exports, accounting files, statements',
      color: 'fintech-blue',
    },
    {
      icon: Target,
      label: 'Assumptions',
      description: 'Revenue growth, collection period, benchmarks',
      color: 'fintech-cyan',
    },
    {
      icon: CheckCircle2,
      label: 'Signal',
      description: 'Cashflow stable, receivables pressure elevated',
      color: 'fintech-teal',
    },
    {
      icon: ArrowRight,
      label: 'Recommendation',
      description: 'Prioritize collections before adding debt',
      color: 'fintech-emerald',
    },
  ]

  return (
    <section id="explainability" className="softform-section py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-12"
        >
          <div className="softform-pill inline-flex items-center space-x-2 rounded-full px-4 py-2 mb-6">
            <CheckCircle2 className="w-4 h-4 text-softform-teal-deep" />
            <span className="text-sm font-medium text-softform-navy-900">
              Explainability
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-softform-navy-950 mb-4 leading-tight">
            From records to recommendations,{' '}
            <span className="text-softform-teal-deep">with a source trail</span>
          </h2>

          <p className="text-lg text-softform-text-secondary leading-relaxed">
            Every insight shows where it came from and what assumptions it relies on
          </p>
        </motion.div>

        {/* Source trail visualization */}
        <div className="max-w-6xl mx-auto mb-12 px-4">
          <div className="relative">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-12">
              {trail.map((step, index) => (
                <motion.div
                  key={step.label}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.15 }}
                  className="relative h-full"
                >
                  <div className="softform-card relative h-full min-h-[200px] rounded-[30px] p-6 transition-all hover:-translate-y-1 hover:shadow-floating-panel flex flex-col">
                    {/* Icon */}
                    <div className="w-12 h-12 bg-softform-mist-100 rounded-2xl flex items-center justify-center mb-4 flex-shrink-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.82)]">
                      <step.icon className="w-6 h-6 text-softform-teal-deep" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 flex flex-col">
                      <h3 className="text-base font-bold text-softform-navy-950 mb-2">
                        {step.label}
                      </h3>
                      <p className="text-sm text-softform-text-secondary leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>


      </div>
    </section>
  )
}
