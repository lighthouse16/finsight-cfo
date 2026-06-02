import { type ElementType } from 'react'
import { Layers } from 'lucide-react'
import PageHeader from '../components/platform/PageHeader'
import EmptyModuleState from '../components/platform/EmptyModuleState'

type PlatformPlaceholderPageProps = {
  title: string
  subtitle: string
  icon?: ElementType
  modulePurpose?: string
}

export default function PlatformPlaceholderPage({
  title,
  subtitle,
  icon = Layers,
  modulePurpose,
}: PlatformPlaceholderPageProps) {
  return (
    <div className="py-6">
      <PageHeader title={title} subtitle={subtitle} />
      <EmptyModuleState
        icon={icon}
        moduleName={title}
        description={
          modulePurpose ??
          `The ${title} module is prepared for future product integration. Its workspace interface will be available once the relevant data connections and product logic are in place.`
        }
      />
    </div>
  )
}
