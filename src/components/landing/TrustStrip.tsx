import { Shield, FileText, TrendingUp, Users } from 'lucide-react'
import { motion } from 'framer-motion'

export default function TrustStrip() {
  const markers = [
    {
      icon: Users,
      label: 'Built for SME finance teams',
    },
    {
      icon: FileText,
      label: 'Explainable financial insights',
    },
    {
      icon: TrendingUp,
      label: 'Upload-first workflow',
    },
    {
      icon: Shield,
      label: 'Funding-readiness focused',
    },
  ]

  return (
    <section className="softform-section py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="softform-panel grid grid-cols-1 gap-5 rounded-[32px] p-4 sm:grid-cols-2 lg:grid-cols-4 lg:p-5">
          {markers.map((marker, index) => (
            <motion.div
              key={marker.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center space-x-3 rounded-2xl px-3 py-3 transition hover:-translate-y-0.5 hover:bg-white/40"
            >
              <div className="flex-shrink-0 w-10 h-10 bg-softform-mist-100 rounded-2xl flex items-center justify-center shadow-[inset_0_1px_0_rgba(255,255,255,0.82)]">
                <marker.icon className="w-5 h-5 text-softform-teal-deep" />
              </div>
              <p className="text-sm font-medium text-softform-navy-800">
                {marker.label}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
