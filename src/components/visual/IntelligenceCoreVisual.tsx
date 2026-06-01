import { motion } from 'framer-motion';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { useMousePosition } from '../../hooks/useMousePosition';

interface IntelligenceCoreVisualProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'hero' | 'compact' | 'minimal';
  showParticles?: boolean;
  showOrbits?: boolean;
  className?: string;
}

/**
 * Intelligence Core Visual Component
 * The central 3D visualization representing the CFO Intelligence engine
 * Features rotating core, orbiting data tokens, and particle streams
 */
export function IntelligenceCoreVisual({
  size = 'md',
  variant = 'hero',
  showParticles = true,
  showOrbits = true,
  className = '',
}: IntelligenceCoreVisualProps) {
  const prefersReducedMotion = useReducedMotion();
  const mousePosition = useMousePosition();

  const sizeMap = {
    sm: { container: 200, core: 60, orbit1: 120, orbit2: 160 },
    md: { container: 320, core: 80, orbit1: 180, orbit2: 260 },
    lg: { container: 480, core: 120, orbit1: 280, orbit2: 400 },
  };

  const sizes = sizeMap[size];
  const shouldAnimate = !prefersReducedMotion;

  // Parallax effect based on mouse position
  const parallaxX = shouldAnimate ? mousePosition.normalizedX * 10 : 0;
  const parallaxY = shouldAnimate ? mousePosition.normalizedY * 10 : 0;

  // Data tokens that orbit the core
  const dataTokens = [
    { label: 'Revenue', icon: '💰', color: 'var(--color-signal-emerald)' },
    { label: 'Expenses', icon: '📊', color: 'var(--color-signal-cyan)' },
    { label: 'Cashflow', icon: '💧', color: 'var(--color-signal-teal)' },
    { label: 'Debt', icon: '📈', color: 'var(--color-signal-amber)' },
  ];

  return (
    <div
      className={`relative flex items-center justify-center ${className}`}
      style={{
        width: sizes.container,
        height: sizes.container,
        perspective: 'var(--perspective-mid)',
      }}
    >
      {/* Background glow */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: 'radial-gradient(circle, var(--color-signal-cyan)15 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
        animate={
          shouldAnimate
            ? {
                scale: [1, 1.1, 1],
                opacity: [0.3, 0.5, 0.3],
              }
            : {}
        }
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Outer orbit ring */}
      {showOrbits && variant !== 'minimal' && (
        <motion.div
          className="absolute preserve-3d"
          style={{
            width: sizes.orbit2,
            height: sizes.orbit2,
            x: parallaxX * 0.5,
            y: parallaxY * 0.5,
          }}
        >
          <motion.div
            className="w-full h-full rounded-full border border-fintech-cyan/20"
            style={{
              transform: 'rotateX(75deg)',
            }}
            animate={
              shouldAnimate
                ? {
                    rotateZ: 360,
                  }
                : {}
            }
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </motion.div>
      )}

      {/* Inner orbit ring */}
      {showOrbits && variant !== 'minimal' && (
        <motion.div
          className="absolute preserve-3d"
          style={{
            width: sizes.orbit1,
            height: sizes.orbit1,
            x: parallaxX * 0.3,
            y: parallaxY * 0.3,
          }}
        >
          <motion.div
            className="w-full h-full rounded-full border-2 border-fintech-teal/30"
            style={{
              transform: 'rotateX(75deg) rotateZ(45deg)',
            }}
            animate={
              shouldAnimate
                ? {
                    rotateZ: -360,
                  }
                : {}
            }
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </motion.div>
      )}

      {/* Central core */}
      <motion.div
        className="relative z-10 preserve-3d"
        style={{
          width: sizes.core,
          height: sizes.core,
          x: parallaxX,
          y: parallaxY,
        }}
      >
        {/* Core sphere */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background:
              'linear-gradient(135deg, var(--color-signal-cyan), var(--color-signal-teal))',
            boxShadow: 'var(--glow-signal-strong)',
          }}
          animate={
            shouldAnimate
              ? {
                  rotateY: 360,
                }
              : {}
          }
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'linear',
          }}
        />

        {/* Core grid overlay */}
        <div
          className="absolute inset-0 rounded-full opacity-30"
          style={{
            background: `
              repeating-linear-gradient(
                0deg,
                transparent,
                transparent 8px,
                var(--color-navy-900) 8px,
                var(--color-navy-900) 9px
              ),
              repeating-linear-gradient(
                90deg,
                transparent,
                transparent 8px,
                var(--color-navy-900) 8px,
                var(--color-navy-900) 9px
              )
            `,
          }}
        />

        {/* Core highlight */}
        <div
          className="absolute rounded-full"
          style={{
            width: sizes.core * 0.3,
            height: sizes.core * 0.3,
            top: '20%',
            left: '30%',
            background: 'rgba(255, 255, 255, 0.4)',
            filter: 'blur(8px)',
          }}
        />

        {/* Core center icon */}
        <div className="absolute inset-0 flex items-center justify-center text-white text-2xl font-bold">
          AI
        </div>
      </motion.div>

      {/* Orbiting data tokens */}
      {showOrbits && variant === 'hero' && (
        <>
          {dataTokens.map((token, index) => {
            const angle = (index * 360) / dataTokens.length;
            const orbitRadius = sizes.orbit1 / 2;

            return (
              <motion.div
                key={token.label}
                className="absolute preserve-3d"
                style={{
                  width: sizes.orbit1,
                  height: sizes.orbit1,
                  x: parallaxX * 0.2,
                  y: parallaxY * 0.2,
                }}
                animate={
                  shouldAnimate
                    ? {
                        rotateZ: 360,
                      }
                    : {}
                }
                transition={{
                  duration: 12,
                  repeat: Infinity,
                  ease: 'linear',
                  delay: index * 0.5,
                }}
              >
                <motion.div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                  style={{
                    transform: `rotate(${angle}deg) translateX(${orbitRadius}px)`,
                  }}
                >
                  <motion.div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-lg backdrop-blur-sm"
                    style={{
                      background: `linear-gradient(135deg, ${token.color}30, ${token.color}20)`,
                      border: `1px solid ${token.color}40`,
                      boxShadow: `0 0 16px ${token.color}20`,
                      transform: `rotate(-${angle}deg)`,
                    }}
                    whileHover={{ scale: 1.1 }}
                  >
                    {token.icon}
                  </motion.div>
                </motion.div>
              </motion.div>
            );
          })}
        </>
      )}

      {/* Particle streams */}
      {showParticles && variant === 'hero' && shouldAnimate && (
        <>
          {[0, 1, 2, 3].map((index) => (
            <motion.div
              key={`particle-${index}`}
              className="absolute w-1 h-1 rounded-full"
              style={{
                background: 'var(--color-signal-cyan)',
                boxShadow: '0 0 8px var(--color-signal-cyan)',
                left: '50%',
                top: '50%',
              }}
              animate={{
                x: [0, Math.cos((index * Math.PI) / 2) * 150],
                y: [0, Math.sin((index * Math.PI) / 2) * 150],
                opacity: [0, 1, 0],
                scale: [0, 1, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: index * 0.5,
                ease: 'easeOut',
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}

/**
 * Compact Intelligence Badge
 * Smaller version for use in cards and inline contexts
 */
export function IntelligenceBadge({
  label = 'AI',
  variant = 'cyan',
  className = '',
}: {
  label?: string;
  variant?: 'cyan' | 'teal' | 'emerald';
  className?: string;
}) {
  const colorMap = {
    cyan: 'var(--color-signal-cyan)',
    teal: 'var(--color-signal-teal)',
    emerald: 'var(--color-signal-emerald)',
  };

  const color = colorMap[variant];

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${className}`}
      style={{
        background: `linear-gradient(135deg, ${color}20, ${color}10)`,
        border: `1px solid ${color}30`,
        color: color,
      }}
    >
      <div
        className="w-1.5 h-1.5 rounded-full"
        style={{
          background: color,
          boxShadow: `0 0 6px ${color}`,
        }}
      />
      {label}
    </div>
  );
}
