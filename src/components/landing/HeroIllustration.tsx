import { motion } from 'framer-motion'
import { TrendingUp, DollarSign, PieChart, BarChart3 } from 'lucide-react'

export default function HeroIllustration() {
  return (
    <div className="relative w-full h-[450px] flex items-center justify-center perspective-mid preserve-3d">
      {/* Ambient glow background */}
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute w-96 h-96 bg-gradient-to-r from-fintech-cyan/30 via-fintech-teal/30 to-fintech-emerald/30 rounded-full blur-3xl"
        />
      </div>

      {/* Main dashboard mockup */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="relative w-full max-w-xl"
      >
        {/* Dashboard container with glassmorphism and 3D depth */}
        <div className="relative bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl p-6 overflow-hidden preserve-3d depth-layer-2">
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-fintech-cyan/5 via-transparent to-fintech-emerald/5" />

          {/* Content */}
          <div className="relative space-y-6">
            {/* Header metrics */}
            <div className="grid grid-cols-3 gap-4">
              {/* Metric 1 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gradient-to-br from-fintech-cyan/20 to-fintech-cyan/5 backdrop-blur-sm rounded-xl p-4 border border-fintech-cyan/30"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 bg-fintech-cyan/20 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-4 h-4 text-fintech-cyan" />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Cashflow</p>
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="text-lg font-bold text-white"
                  >
                    +24%
                  </motion.p>
                </div>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '75%' }}
                  transition={{ delay: 0.6, duration: 1 }}
                  className="h-1 bg-gradient-to-r from-fintech-cyan to-fintech-teal rounded-full mt-2"
                />
              </motion.div>

              {/* Metric 2 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gradient-to-br from-fintech-teal/20 to-fintech-teal/5 backdrop-blur-sm rounded-xl p-4 border border-fintech-teal/30"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 bg-fintech-teal/20 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-4 h-4 text-fintech-teal" />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Credit</p>
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="text-lg font-bold text-white"
                  >
                    Strong
                  </motion.p>
                </div>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '85%' }}
                  transition={{ delay: 0.7, duration: 1 }}
                  className="h-1 bg-gradient-to-r from-fintech-teal to-fintech-emerald rounded-full mt-2"
                />
              </motion.div>

              {/* Metric 3 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-gradient-to-br from-fintech-emerald/20 to-fintech-emerald/5 backdrop-blur-sm rounded-xl p-4 border border-fintech-emerald/30"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 bg-fintech-emerald/20 rounded-lg flex items-center justify-center">
                    <PieChart className="w-4 h-4 text-fintech-emerald" />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Ready</p>
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6 }}
                    className="text-lg font-bold text-white"
                  >
                    65%
                  </motion.p>
                </div>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '65%' }}
                  transition={{ delay: 0.8, duration: 1 }}
                  className="h-1 bg-gradient-to-r from-fintech-emerald to-fintech-cyan rounded-full mt-2"
                />
              </motion.div>
            </div>

            {/* Main chart area */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-fintech-cyan" />
                  <span className="text-sm font-semibold text-white">Financial Intelligence</span>
                </div>
                <div className="flex items-center space-x-2">
                  <motion.div
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-2 h-2 bg-fintech-emerald rounded-full"
                  />
                  <span className="text-xs text-white/60">Live</span>
                </div>
              </div>

              {/* Animated chart bars */}
              <div className="flex items-end justify-between h-32 space-x-2">
                {[65, 78, 45, 89, 72, 95, 68, 82].map((height, index) => (
                  <motion.div
                    key={index}
                    initial={{ height: 0 }}
                    animate={{ height: `${height}%` }}
                    transition={{
                      delay: 0.7 + index * 0.1,
                      duration: 0.8,
                      ease: 'easeOut',
                    }}
                    className="flex-1 bg-gradient-to-t from-fintech-cyan via-fintech-teal to-fintech-emerald rounded-t-lg relative group"
                  >
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1.5 + index * 0.1 }}
                      className="absolute -top-6 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <span className="text-xs text-white font-semibold">{height}</span>
                    </motion.div>
                  </motion.div>
                ))}
              </div>

              {/* Chart labels */}
              <div className="flex justify-between mt-3">
                {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'].map((month, index) => (
                  <motion.span
                    key={month}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.5 + index * 0.05 }}
                    className="text-xs text-white/40 flex-1 text-center"
                  >
                    {month}
                  </motion.span>
                ))}
              </div>
            </motion.div>

            {/* Bottom insight card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="bg-gradient-to-r from-fintech-cyan/10 to-fintech-emerald/10 backdrop-blur-sm rounded-xl p-4 border border-white/10"
            >
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-fintech-cyan/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-fintech-cyan">AI</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white mb-1">CFO Recommendation</p>
                  <p className="text-xs text-white/70 leading-relaxed">
                    Strong cashflow trajectory. Consider accelerating receivables collection to optimize working capital.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Floating particles */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{
                opacity: [0, 0.6, 0],
                y: [0, -100],
                x: [0, (i % 2 === 0 ? 1 : -1) * 30],
              }}
              transition={{
                duration: 3 + i * 0.5,
                repeat: Infinity,
                delay: i * 0.8,
              }}
              className="absolute bottom-0 w-1 h-1 bg-fintech-cyan rounded-full"
              style={{
                left: `${20 + i * 12}%`,
              }}
            />
          ))}
        </div>

        {/* Glow effect behind dashboard */}
        <div className="absolute inset-0 bg-gradient-to-br from-fintech-cyan/20 via-fintech-teal/20 to-fintech-emerald/20 rounded-3xl blur-2xl -z-10 scale-105" />
      </motion.div>
    </div>
  )
}
