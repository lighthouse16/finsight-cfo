import { motion } from 'framer-motion';
import { useReducedMotion } from '../../hooks/useReducedMotion';

interface SignalIcon3DProps {
  type?: 'positive' | 'neutral' | 'caution' | 'active';
  size?: 'sm' | 'md' | 'lg';
  intensity?: 'subtle' | 'medium' | 'strong';
  animated?: boolean;
  className?: string;
}

/**
 * 3D Signal Icon Component
 * Represents intelligence signals with depth, glow, and animation
 * Used across the platform to indicate AI-generated insights
 */
export function SignalIcon3D({
  type = 'active',
  size = 'md',
  intensity = 'medium',
  animated = true,
  className = '',
}: SignalIcon3DProps) {
  const prefersReducedMotion = useReducedMotion();

  // Color mapping based on signal type
  const colorMap = {
    positive: {
      primary: 'var(--color-signal-emerald)',
      glow: 'var(--glow-emerald)',
      border: 'rgba(16, 185, 129, 0.3)',
    },
    neutral: {
      primary: 'var(--color-signal-cyan)',
      glow: 'var(--glow-signal)',
      border: 'rgba(6, 182, 212, 0.3)',
    },
    caution: {
      primary: 'var(--color-signal-amber)',
      glow: 'var(--glow-amber)',
      border: 'rgba(245, 158, 11, 0.3)',
    },
    active: {
      primary: 'var(--color-signal-teal)',
      glow: 'var(--glow-signal)',
      border: 'rgba(20, 184, 166, 0.3)',
    },
  };

  // Size mapping
  const sizeMap = {
    sm: { container: 32, core: 12, ring1: 20, ring2: 28 },
    md: { container: 48, core: 16, ring1: 28, ring2: 40 },
    lg: { container: 64, core: 20, ring1: 36, ring2: 52 },
  };

  // Intensity mapping for glow
  const intensityMap = {
    subtle: 0.15,
    medium: 0.25,
    strong: 0.4,
  };

  const colors = colorMap[type];
  const sizes = sizeMap[size];
  const glowOpacity = intensityMap[intensity];

  // Animation variants
  const pulseVariants = {
    initial: { scale: 1, opacity: 0.8 },
    animate: {
      scale: [1, 1.1, 1],
      opacity: [0.8, 1, 0.8],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  const rotateVariants = {
    initial: { rotateZ: 0 },
    animate: {
      rotateZ: 360,
      transition: {
        duration: 8,
        repeat: Infinity,
        ease: 'linear',
      },
    },
  };

  const shouldAnimate = animated && !prefersReducedMotion;

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{
        width: sizes.container,
        height: sizes.container,
      }}
    >
      {/* Outer glow layer */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: `radial-gradient(circle, ${colors.primary} 0%, transparent 70%)`,
          opacity: glowOpacity,
          filter: 'blur(12px)',
        }}
        variants={shouldAnimate ? pulseVariants : undefined}
        initial="initial"
        animate={shouldAnimate ? 'animate' : undefined}
      />

      {/* Outer ring */}
      <motion.div
        className="absolute preserve-3d"
        style={{
          width: sizes.ring2,
          height: sizes.ring2,
        }}
        variants={shouldAnimate ? rotateVariants : undefined}
        initial="initial"
        animate={shouldAnimate ? 'animate' : undefined}
      >
        <div
          className="w-full h-full rounded-full border-2"
          style={{
            borderColor: colors.border,
            transform: 'rotateX(60deg)',
          }}
        />
      </motion.div>

      {/* Middle ring */}
      <motion.div
        className="absolute preserve-3d"
        style={{
          width: sizes.ring1,
          height: sizes.ring1,
        }}
        variants={shouldAnimate ? rotateVariants : undefined}
        initial="initial"
        animate={shouldAnimate ? 'animate' : undefined}
        transition={{ delay: 0.5 }}
      >
        <div
          className="w-full h-full rounded-full border-2"
          style={{
            borderColor: colors.border,
            transform: 'rotateX(60deg) rotateZ(45deg)',
          }}
        />
      </motion.div>

      {/* Core sphere */}
      <motion.div
        className="relative z-10 rounded-full"
        style={{
          width: sizes.core,
          height: sizes.core,
          background: `linear-gradient(135deg, ${colors.primary}, ${colors.primary}dd)`,
          boxShadow: colors.glow,
        }}
        variants={shouldAnimate ? pulseVariants : undefined}
        initial="initial"
        animate={shouldAnimate ? 'animate' : undefined}
      />

      {/* Inner highlight */}
      <div
        className="absolute z-20 rounded-full"
        style={{
          width: sizes.core * 0.4,
          height: sizes.core * 0.4,
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -70%)',
          background: 'rgba(255, 255, 255, 0.6)',
          filter: 'blur(2px)',
        }}
      />
    </div>
  );
}

/**
 * Signal Pulse Component
 * Animated pulse effect for active signals
 */
export function SignalPulse({
  color = 'var(--color-signal-cyan)',
  size = 'md',
  className = '',
}: {
  color?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  const sizeMap = {
    sm: 24,
    md: 32,
    lg: 48,
  };

  const pulseSize = sizeMap[size];

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: pulseSize, height: pulseSize }}
    >
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className="absolute inset-0 rounded-full border-2"
          style={{
            borderColor: color,
          }}
          initial={{ scale: 0.8, opacity: 0.8 }}
          animate={
            !prefersReducedMotion
              ? {
                  scale: [0.8, 1.5],
                  opacity: [0.8, 0],
                }
              : {}
          }
          transition={{
            duration: 2,
            repeat: Infinity,
            delay: index * 0.4,
            ease: 'easeOut',
          }}
        />
      ))}
      <div
        className="w-2 h-2 rounded-full"
        style={{
          background: color,
          boxShadow: `0 0 12px ${color}`,
        }}
      />
    </div>
  );
}
