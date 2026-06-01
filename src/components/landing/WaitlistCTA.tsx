import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, CheckCircle2, ArrowRight } from 'lucide-react'

export default function WaitlistCTA() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Local-only form - no backend call
    if (email) {
      setSubmitted(true)
      setEmail('')
    }
  }

  return (
    <section id="signup" className="py-20 lg:py-32 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-x-4 inset-y-8 rounded-[56px] bg-[radial-gradient(circle_at_88%_12%,rgba(32,169,154,0.22),transparent_32%),linear-gradient(145deg,#0d1726_0%,#132337_52%,#1c324b_100%)] shadow-navy-card" />

      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.1, 0.2, 0.1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-softform-aqua-300/16 rounded-full blur-3xl"
      />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white/10 rounded-full border border-white/10 mb-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]">
            <div className="w-2 h-2 bg-softform-aqua-300 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-white">
              Join Early Access
            </span>
          </div>

          {/* Headline */}
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
            Join Early Access
          </h2>

          <p className="text-lg text-white/70 mb-4 leading-relaxed max-w-2xl mx-auto">
            Get updates as FinSight CFO moves toward private beta.
          </p>

          <p className="text-base text-white/60 mb-12 leading-relaxed max-w-2xl mx-auto">
            Built for finance teams preparing stronger funding conversations.
          </p>

          {/* Form or Success State */}
          {!submitted ? (
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              onSubmit={handleSubmit}
              className="max-w-md mx-auto"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-softform-aqua-300 to-softform-amber-200 rounded-[24px] blur opacity-20" />

                <div className="relative bg-white/10 backdrop-blur-sm rounded-[24px] p-2 border border-white/12 shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <div className="flex-1 relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Enter your email"
                        required
                        className="w-full pl-12 pr-4 py-3 bg-white/12 border border-white/12 rounded-2xl text-white placeholder-white/45 focus:outline-none focus:ring-2 focus:ring-softform-aqua-300 focus:border-transparent"
                      />
                    </div>
                    <button
                      type="submit"
                      className="group px-6 py-3 bg-white text-softform-navy-900 rounded-2xl font-semibold hover:-translate-y-0.5 transition-all flex items-center justify-center space-x-2"
                    >
                      <span>Join Waitlist</span>
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>
              </div>

              <p className="mt-6 text-sm text-white/50">
                Join the waitlist to receive updates on private beta access.
              </p>
            </motion.form>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="max-w-md mx-auto"
            >
              <div className="bg-white/10 backdrop-blur-sm rounded-[28px] p-8 border border-white/12 shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]">
                <div className="flex flex-col items-center space-y-4">
                  <div className="w-16 h-16 bg-softform-teal-500/20 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-8 h-8 text-softform-aqua-300" />
                  </div>
                  <h3 className="text-xl font-bold text-white">
                    You're on the waitlist!
                  </h3>
                  <p className="text-white/70 text-center">
                    We'll notify you as FinSight CFO moves toward private beta.
                    Thank you for your interest.
                  </p>
                  <button
                    onClick={() => setSubmitted(false)}
                    className="text-softform-aqua-300 hover:text-white transition-colors text-sm font-medium"
                  >
                    Submit another email
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Trust markers */}
          <div className="mt-16 pt-16 border-t border-white/10">
            <div className="grid sm:grid-cols-3 gap-8 text-center">
              <div>
                <p className="text-2xl font-bold text-white mb-2">Upload-first</p>
                <p className="text-sm text-white/60">Financial records workflow</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-2">Explainable</p>
                <p className="text-sm text-white/60">Source trails and assumptions</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-2">CFO-grade</p>
                <p className="text-sm text-white/60">Actionable recommendations</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
