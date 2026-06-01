import { motion } from 'framer-motion'
import { TrendingUp, AlertCircle, ArrowRight } from 'lucide-react'
import { IntelligenceCoreVisual } from '../visual/IntelligenceCoreVisual'
import { SignalIcon3D } from '../visual/SignalIcon3D'
import { SourceTrailVisual } from '../visual/SourceTrailVisual'

export default function HeroProductScene() {
  return (
    <div className="relative w-full h-[500px] lg:h-[600px] overflow-hidden">
      {/* 3D Container with deep perspective */}
      <div
        className="relative w-full h-full preserve-3d"
        style={{ perspective: '1200px' }}
      >
        {/* Central Intelligence Core */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            className="relative"
          >
            <IntelligenceCoreVisual
              size="lg"
              variant="hero"
              showParticles={true}
              showOrbits={true}
            />
          </motion.div>
        </div>

        {/* Layered Dashboard Planes */}
        <div className="absolute inset-0 flex items-center justify-center px-4">
          <div className="relative w-full max-w-4xl h-full flex items-center justify-center">

            {/* Plane 1: Cashflow Signal - Front Left */}
            <motion.div
              initial={{ opacity: 0, x: -120, rotateY: -15 }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              transition={{ delay: 0.3, duration: 0.9, ease: 'easeOut' }}
              style={{
                transformStyle: 'preserve-3d',
                transform: 'translateZ(60px) translateX(-220px) translateY(-30px)',
              }}
              className="absolute w-64 lg:w-72 bg-white/95 backdrop-blur-md rounded-xl shadow-elevated border border-fintech-navy/10 p-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <SignalIcon3D type="positive" size="sm" intensity="medium" />
                    <span className="text-xs font-semibold text-fintech-navy/60 uppercase tracking-wide">
                      Cashflow Signal
                    </span>
                  </div>
                  <div className="w-2 h-2 bg-fintech-emerald rounded-full animate-pulse" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-fintech-navy/70">Operating Cash</span>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-fintech-emerald" />
                      <span className="text-sm font-semibold text-fintech-navy">Stable</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-fintech-navy/70">Runway</span>
                    <span className="text-sm font-semibold text-fintech-navy">8.2 months</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-fintech-navy/10">
                  <p className="text-xs text-fintech-navy/60 leading-relaxed">
                    Based on 12-month trailing records
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Plane 2: Credit Readiness - Front Right */}
            <motion.div
              initial={{ opacity: 0, x: 120, rotateY: 15 }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              transition={{ delay: 0.5, duration: 0.9, ease: 'easeOut' }}
              style={{
                transformStyle: 'preserve-3d',
                transform: 'translateZ(60px) translateX(220px) translateY(-30px)',
              }}
              className="absolute w-64 lg:w-72 bg-white/95 backdrop-blur-md rounded-xl shadow-elevated border border-fintech-navy/10 p-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <SignalIcon3D type="active" size="sm" intensity="medium" />
                    <span className="text-xs font-semibold text-fintech-navy/60 uppercase tracking-wide">
                      Credit Readiness
                    </span>
                  </div>
                  <div className="w-2 h-2 bg-fintech-cyan rounded-full animate-pulse" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-fintech-navy/70">Debt Capacity</span>
                    <span className="text-sm font-semibold text-fintech-navy">Strengthening</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <div className="flex-1 h-2 bg-fintech-navy/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: '72%' }}
                        transition={{ delay: 0.8, duration: 1.2 }}
                        className="h-full bg-gradient-to-r from-fintech-cyan to-fintech-teal"
                      />
                    </div>
                    <span className="text-xs font-semibold text-fintech-navy">72%</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-fintech-navy/10">
                  <p className="text-xs text-fintech-navy/60 leading-relaxed">
                    Subject to bank policy review
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Plane 3: Advisor Action - Back Top */}
            <motion.div
              initial={{ opacity: 0, y: -80, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: 0.7, duration: 0.9, ease: 'easeOut' }}
              style={{
                transformStyle: 'preserve-3d',
                transform: 'translateZ(-40px) translateY(-120px)',
              }}
              className="absolute w-72 lg:w-80 bg-gradient-to-br from-fintech-blue to-fintech-cyan rounded-xl shadow-deep p-4 text-white"
            >
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <ArrowRight className="w-4 h-4" />
                  <span className="text-xs font-semibold uppercase tracking-wide">
                    Advisor Action
                  </span>
                </div>
                <p className="text-sm leading-relaxed">
                  Prioritize receivables collection before adding new debt
                </p>
                <div className="pt-2 border-t border-white/20">
                  <p className="text-xs text-white/70">
                    Receivables concentration detected as primary constraint
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Plane 4: Assumptions - Back Bottom */}
            <motion.div
              initial={{ opacity: 0, y: 80, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: 0.9, duration: 0.9, ease: 'easeOut' }}
              style={{
                transformStyle: 'preserve-3d',
                transform: 'translateZ(-40px) translateY(120px)',
              }}
              className="absolute w-72 lg:w-80 bg-fintech-navy/95 backdrop-blur-md rounded-xl shadow-deep border border-fintech-cyan/20 p-4 text-white"
            >
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <SignalIcon3D type="caution" size="sm" intensity="subtle" />
                  <span className="text-xs font-semibold uppercase tracking-wide text-white/90">
                    Key Assumptions
                  </span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-2">
                    <div className="w-1 h-1 bg-fintech-cyan rounded-full" />
                    <p className="text-xs text-white/80">Revenue growth: 15% YoY</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-1 h-1 bg-fintech-teal rounded-full" />
                    <p className="text-xs text-white/80">Collection period: 45 days avg</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-1 h-1 bg-fintech-emerald rounded-full" />
                    <p className="text-xs text-white/80">Operating margin: 18%</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Receivables Alert - Side Accent (Desktop Only) */}
            <motion.div
              initial={{ opacity: 0, x: -60 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.1, duration: 0.8 }}
              style={{
                transformStyle: 'preserve-3d',
                transform: 'translateZ(40px) translateX(-180px) translateY(60px)',
              }}
              className="hidden xl:block absolute w-56 bg-fintech-amber/10 backdrop-blur-sm rounded-lg border border-fintech-amber/30 p-3"
            >
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-fintech-amber" />
                  <span className="text-xs font-semibold text-fintech-navy/80 uppercase tracking-wide">
                    Attention
                  </span>
                </div>
                <p className="text-xs text-fintech-navy/70 leading-relaxed">
                  Receivables pressure elevated - review collection process
                </p>
              </div>
            </motion.div>

          </div>
        </div>

        {/* Source Trail Rail - Bottom */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.3, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4"
        >
          <div className="bg-white/80 backdrop-blur-md rounded-lg shadow-institutional border border-fintech-navy/10 p-3">
            <SourceTrailVisual
              variant="horizontal"
              showLabels={true}
              animated={true}
              sources={['Financial Records', 'Market Data']}
            />
          </div>
        </motion.div>

        {/* Subtle floating animation for depth */}
        <motion.div
          animate={{
            y: [0, -8, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute inset-0 pointer-events-none"
        />
      </div>
    </div>
  )
}
