import { motion } from 'framer-motion'

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
  showText?: boolean
  label?: string
  textColor?: string
}

export default function ScoreRing({
  score,
  size = 88,
  strokeWidth = 8,
  showText = true,
  label,
  textColor = 'text-softform-navy-950',
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (Math.min(Math.max(score, 0), 100) / 100) * circumference

  // Color helper based on score range
  const getColor = (val: number) => {
    if (val >= 80) return '#20a99a' // var(--teal-500)
    if (val >= 50) return '#d9a83f' // var(--amber-500)
    return '#ef4444' // red-500
  }

  const color = getColor(score)

  return (
    <div className="flex flex-col items-center justify-center gap-1.5" style={{ width: size }}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="softform-score-ring">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="rgba(13, 23, 38, 0.06)"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: 'easeOut' }}
            strokeLinecap="round"
          />
        </svg>
        {showText && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-xl font-bold tracking-tight ${textColor} tabular-finance`}>
              {score}
            </span>
          </div>
        )}
      </div>
      {label && (
        <span className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted text-center">
          {label}
        </span>
      )}
    </div>
  )
}
