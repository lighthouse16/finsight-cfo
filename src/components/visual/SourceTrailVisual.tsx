import { motion } from 'framer-motion';
import { useReducedMotion } from '../../hooks/useReducedMotion';

interface SourceTrailVisualProps {
  sources?: string[];
  variant?: 'horizontal' | 'vertical' | 'radial';
  animated?: boolean;
  showLabels?: boolean;
  className?: string;
}

/**
 * Source Trail Visual Component
 * Shows the data lineage: financial records → assumptions → signal → action
 * Represents the intelligence pipeline with animated flow
 */
export function SourceTrailVisual({
  sources: _sources = ['Financial Records', 'Market Data', 'Industry Benchmarks'],
  variant = 'horizontal',
  animated = true,
  showLabels = true,
  className = '',
}: SourceTrailVisualProps) {
  const prefersReducedMotion = useReducedMotion();
  const shouldAnimate = animated && !prefersReducedMotion;

  const stages = [
    { label: 'Records', icon: '📊', color: 'var(--color-base-400)' },
    { label: 'Assumptions', icon: '🔍', color: 'var(--color-signal-cyan)' },
    { label: 'Signal', icon: '⚡', color: 'var(--color-signal-teal)' },
    { label: 'Action', icon: '✓', color: 'var(--color-signal-emerald)' },
  ];

  if (variant === 'horizontal') {
    return (
      <div className={`flex items-center gap-4 ${className}`}>
        {stages.map((stage, index) => (
          <div key={stage.label} className="flex items-center gap-4">
            {/* Stage node */}
            <motion.div
              className="relative flex flex-col items-center gap-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* Icon container */}
              <div
                className="relative w-12 h-12 rounded-full flex items-center justify-center text-lg"
                style={{
                  background: `linear-gradient(135deg, ${stage.color}20, ${stage.color}10)`,
                  border: `2px solid ${stage.color}40`,
                  boxShadow: `0 0 20px ${stage.color}20`,
                }}
              >
                {stage.icon}

                {/* Pulse effect */}
                {shouldAnimate && (
                  <motion.div
                    className="absolute inset-0 rounded-full"
                    style={{
                      border: `2px solid ${stage.color}`,
                    }}
                    initial={{ scale: 1, opacity: 0.6 }}
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.6, 0, 0.6],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      delay: index * 0.3,
                    }}
                  />
                )}
              </div>

              {/* Label */}
              {showLabels && (
                <span
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: stage.color }}
                >
                  {stage.label}
                </span>
              )}
            </motion.div>

            {/* Connector arrow */}
            {index < stages.length - 1 && (
              <div className="relative flex items-center">
                <svg
                  width="40"
                  height="2"
                  className="overflow-visible"
                >
                  <motion.line
                    x1="0"
                    y1="1"
                    x2="40"
                    y2="1"
                    stroke={stage.color}
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    initial={{ pathLength: 0 }}
                    animate={shouldAnimate ? { pathLength: 1 } : { pathLength: 1 }}
                    transition={{
                      duration: 1,
                      delay: index * 0.2,
                      repeat: shouldAnimate ? Infinity : 0,
                      repeatDelay: 2,
                    }}
                  />
                </svg>

                {/* Flow particles */}
                {shouldAnimate && (
                  <motion.div
                    className="absolute w-1.5 h-1.5 rounded-full"
                    style={{
                      background: stage.color,
                      boxShadow: `0 0 8px ${stage.color}`,
                    }}
                    initial={{ x: 0, opacity: 0 }}
                    animate={{
                      x: [0, 40],
                      opacity: [0, 1, 1, 0],
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      delay: index * 0.3,
                      ease: 'easeInOut',
                    }}
                  />
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'vertical') {
    return (
      <div className={`flex flex-col gap-4 ${className}`}>
        {stages.map((stage, index) => (
          <div key={stage.label} className="flex flex-col items-center gap-4">
            {/* Stage node */}
            <motion.div
              className="relative flex items-center gap-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* Icon container */}
              <div
                className="relative w-10 h-10 rounded-full flex items-center justify-center text-base"
                style={{
                  background: `linear-gradient(135deg, ${stage.color}20, ${stage.color}10)`,
                  border: `2px solid ${stage.color}40`,
                  boxShadow: `0 0 16px ${stage.color}20`,
                }}
              >
                {stage.icon}
              </div>

              {/* Label */}
              {showLabels && (
                <span
                  className="text-sm font-medium"
                  style={{ color: stage.color }}
                >
                  {stage.label}
                </span>
              )}
            </motion.div>

            {/* Connector line */}
            {index < stages.length - 1 && (
              <div className="relative w-0.5 h-8" style={{ background: `${stage.color}40` }}>
                {shouldAnimate && (
                  <motion.div
                    className="absolute w-1.5 h-1.5 rounded-full left-1/2 -translate-x-1/2"
                    style={{
                      background: stage.color,
                      boxShadow: `0 0 8px ${stage.color}`,
                    }}
                    initial={{ y: 0, opacity: 0 }}
                    animate={{
                      y: [0, 32],
                      opacity: [0, 1, 1, 0],
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      delay: index * 0.3,
                      ease: 'easeInOut',
                    }}
                  />
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  // Radial variant
  return (
    <div className={`relative ${className}`} style={{ width: 240, height: 240 }}>
      {/* Center core */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center text-2xl"
          style={{
            background: 'linear-gradient(135deg, var(--color-signal-cyan)30, var(--color-signal-teal)30)',
            border: '2px solid var(--color-signal-cyan)60',
            boxShadow: 'var(--glow-signal)',
          }}
        >
          🎯
        </div>
      </div>

      {/* Orbiting stages */}
      {stages.map((stage, index) => {
        const angle = (index * 360) / stages.length;
        const radius = 90;
        const x = Math.cos((angle * Math.PI) / 180) * radius;
        const y = Math.sin((angle * Math.PI) / 180) * radius;

        return (
          <motion.div
            key={stage.label}
            className="absolute top-1/2 left-1/2"
            style={{
              x: x - 20,
              y: y - 20,
            }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.15 }}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-sm"
              style={{
                background: `linear-gradient(135deg, ${stage.color}20, ${stage.color}10)`,
                border: `2px solid ${stage.color}40`,
                boxShadow: `0 0 16px ${stage.color}20`,
              }}
            >
              {stage.icon}
            </div>

            {/* Connection line to center */}
            <svg
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
              style={{ width: 200, height: 200 }}
            >
              <motion.line
                x1="100"
                y1="100"
                x2={100 + x}
                y2={100 + y}
                stroke={stage.color}
                strokeWidth="1"
                strokeDasharray="2 2"
                opacity="0.3"
                initial={{ pathLength: 0 }}
                animate={shouldAnimate ? { pathLength: 1 } : { pathLength: 1 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
              />
            </svg>
          </motion.div>
        );
      })}
    </div>
  );
}
