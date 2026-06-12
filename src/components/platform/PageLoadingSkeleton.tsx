import SkeletonLoader from './SkeletonLoader'

interface PageLoadingSkeletonProps {
  layout?: 'standard' | 'dashboard' | 'valuation' | 'health' | 'credit' | 'funding' | 'overview'
  metricCount?: number
  sectionCount?: number
  metricCols?: number
}

export default function PageLoadingSkeleton({
  layout = 'standard',
  metricCount = 4,
  sectionCount = 2,
  metricCols,
}: PageLoadingSkeletonProps) {
  if (layout === 'health') {
    return (
      <div className="space-y-8 pb-12">
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>
        <SkeletonLoader variant="card" className="min-h-[200px]" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SkeletonLoader variant="metric" count={8} />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[300px]" />
          <SkeletonLoader variant="card" className="min-h-[300px]" />
        </div>
      </div>
    )
  }

  if (layout === 'credit') {
    return (
      <div className="space-y-8 pb-12">
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>
        <SkeletonLoader variant="card" className="min-h-[200px]" />
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[250px]" />
          <SkeletonLoader variant="card" className="min-h-[250px]" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <SkeletonLoader variant="metric" count={6} />
        </div>
      </div>
    )
  }

  if (layout === 'funding') {
    return (
      <div className="space-y-8 pb-12">
        <div className="space-y-3">
          <SkeletonLoader variant="text" />
        </div>
        <SkeletonLoader variant="card" className="min-h-[200px]" />
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonLoader variant="card" className="min-h-[250px]" />
          <SkeletonLoader variant="card" className="min-h-[250px]" />
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <SkeletonLoader variant="metric" count={3} />
        </div>
      </div>
    )
  }

  // Standard / overview / valuation layout
  const colsClass = metricCols
    ? `grid gap-4 md:grid-cols-2 xl:grid-cols-${metricCols}`
    : 'grid gap-4 md:grid-cols-2 xl:grid-cols-4'

  const sectionHeight = layout === 'overview' ? 'min-h-[300px]' : 'min-h-[250px]'

  return (
    <div className="space-y-8 pb-12">
      <div className="space-y-3">
        <SkeletonLoader variant="text" />
      </div>
      <SkeletonLoader variant="card" className="min-h-[200px]" />

      {metricCount > 0 && (
        <div className={colsClass}>
          <SkeletonLoader variant="metric" count={metricCount} />
        </div>
      )}

      {sectionCount > 0 && (
        <div className="grid gap-6 lg:grid-cols-2">
          {Array.from({ length: sectionCount }).map((_, idx) => (
            <SkeletonLoader key={idx} variant="card" className={sectionHeight} />
          ))}
        </div>
      )}
    </div>
  )
}
