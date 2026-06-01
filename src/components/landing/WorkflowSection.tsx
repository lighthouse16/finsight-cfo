import { motion } from 'framer-motion'
import { Upload, Search, Target, Zap } from 'lucide-react'

export default function WorkflowSection() {
  const steps = [
    {
      icon: Upload,
      title: 'Upload records',
      description: 'Bank exports, accounting files, and financial statements',
      color: 'from-softform-navy-800 to-softform-teal-500',
    },
    {
      icon: Search,
      title: 'Detect cashflow signals',
      description: 'Revenue patterns, receivables pressure, and working capital trends',
      color: 'from-softform-teal-500 to-softform-aqua-300',
    },
    {
      icon: Target,
      title: 'Understand credit readiness',
      description: 'Funding capacity, documentation gaps, and risk signals',
      color: 'from-softform-teal-deep to-softform-emerald-soft',
    },
    {
      icon: Zap,
      title: 'Act with CFO-grade recommendations',
      description: 'Prioritized next actions with source trails and assumptions',
      color: 'from-softform-emerald-soft to-softform-navy-800',
    },
  ]

  return (
    <section id="workflow" className="softform-section py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-12"
        >
          <div className="softform-pill inline-flex items-center space-x-2 rounded-full px-4 py-2 mb-6">
            <Zap className="w-4 h-4 text-softform-teal-deep" />
            <span className="text-sm font-medium text-softform-navy-900">
              How It Works
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-softform-navy-950 mb-4 leading-tight">
            From records to{' '}
            <span className="text-softform-teal-deep">recommendations</span>
          </h2>

          <p className="text-lg text-softform-text-secondary leading-relaxed">
            A connected journey from uploaded financial records to CFO-grade next actions
          </p>
        </motion.div>

        {/* Workflow steps */}
        <div className="relative">
          {/* Subtle connection line - desktop only */}
          <div className="hidden lg:block absolute top-[56px] left-[10%] right-[10%] h-px bg-gradient-to-r from-transparent via-softform-teal-500/24 to-transparent" />

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
            {steps.map((step, index) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="relative h-full"
              >
                {/* Step card */}
                <div className="softform-card relative h-full min-h-[240px] rounded-[30px] p-6 transition-all hover:-translate-y-1 hover:shadow-floating-panel flex flex-col">
                  {/* Step number */}
                  <div className="absolute -top-3 -left-3 w-8 h-8 bg-softform-navy-900 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-navy-card">
                    {index + 1}
                  </div>

                  {/* Icon */}
                  <div className={`w-16 h-16 bg-gradient-to-br ${step.color} rounded-2xl flex items-center justify-center mb-4 flex-shrink-0 shadow-[0_16px_34px_rgba(18,38,53,0.14)]`}>
                    <step.icon className="w-8 h-8 text-white" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 flex flex-col">
                    <h3 className="text-lg font-bold text-softform-navy-950 mb-2">
                      {step.title}
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

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-12 text-center"
        >
          <p className="text-softform-text-secondary mb-6">
            Built for finance teams preparing stronger funding conversations
          </p>
          <a
            href="#signup"
            className="inline-flex items-center space-x-2 px-6 py-3 bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-white rounded-2xl font-medium shadow-[0_18px_42px_rgba(8,17,31,0.20)] hover:-translate-y-0.5 transition-all"
          >
            <span>Get Started</span>
            <Zap className="w-4 h-4" />
          </a>
        </motion.div>
      </div>
    </section>
  )
}
