import clsx from 'clsx'

type DataPoint = {
  label: string
  value: number // 0-100
  displayValue?: string
  colorClass?: string
}

type SoftBarChartProps = {
  data: DataPoint[]
  height?: number
  className?: string
}

export default function SoftBarChart({
  data,
  height = 8,
  className,
}: SoftBarChartProps) {
  return (
    <div className={clsx('flex flex-col gap-3', className)}>
      {data.map((point, idx) => (
        <div key={idx} className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-softform-text-secondary">
              {point.label}
            </span>
            <span className="font-semibold text-softform-navy-900">
              {point.displayValue ?? `${point.value}%`}
            </span>
          </div>
          <div
            className="w-full overflow-hidden rounded-full bg-white/40 border border-white/20 shadow-[inset_0_1px_2px_rgba(8,17,31,0.05)] backdrop-blur-[2px]"
            style={{ height: `${height}px` }}
          >
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-700 ease-out',
                point.colorClass?.includes('amber')
                  ? 'bg-[linear-gradient(90deg,rgba(217,168,63,0.6),rgba(217,168,63,0.85))]'
                  : 'bg-[linear-gradient(90deg,rgba(32,169,154,0.6),rgba(32,169,154,0.85))]',
              )}
              style={{ width: `${Math.max(0, Math.min(100, point.value))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
