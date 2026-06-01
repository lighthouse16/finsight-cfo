import { motion } from 'framer-motion'
import { Shield, Lock, Eye, FileCheck } from 'lucide-react'

export default function SecuritySection() {
  const features = [
    {
      icon: Shield,
      title: 'Secure data handling',
      description: 'Designed with secure data handling principles in mind',
    },
    {
      icon: Lock,
      title: 'No secrets in frontend',
      description: 'Client-side code contains no API keys or sensitive credentials',
    },
    {
      icon: Eye,
      title: 'Transparent processing',
      description: 'Clear visibility into how financial records are analyzed',
    },
    {
      icon: FileCheck,
      title: 'Future-ready architecture',
      description: 'Built to support auth, audit logs, and role-based access',
    },
  ]

  return (
    <section id="security" className="softform-section py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="softform-pill inline-flex items-center space-x-2 rounded-full px-4 py-2 mb-6">
            <Shield className="w-4 h-4 text-softform-teal-deep" />
            <span className="text-sm font-medium text-softform-navy-900">
              Security & Data Handling
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-softform-navy-950 mb-6 leading-tight">
            Built with{' '}
            <span className="text-softform-teal-deep">secure data handling</span>{' '}
            in mind
          </h2>

          <p className="text-lg text-softform-text-secondary leading-relaxed">
            FinSight CFO is designed with security and data handling principles
            as foundational requirements
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="softform-card rounded-[30px] p-6 text-center transition-all hover:-translate-y-1 hover:shadow-floating-panel"
            >
              <div className="w-16 h-16 bg-softform-mist-100 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.82)]">
                <feature.icon className="w-8 h-8 text-softform-navy-700" />
              </div>
              <h3 className="text-lg font-bold text-softform-navy-950 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-softform-text-secondary leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>


      </div>
    </section>
  )
}
