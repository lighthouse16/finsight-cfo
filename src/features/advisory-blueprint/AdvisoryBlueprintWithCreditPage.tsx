import AdvisoryBlueprintPage from './AdvisoryBlueprintPage'
import CreditReadinessInlineSummary from './components/CreditReadinessInlineSummary'

export default function AdvisoryBlueprintWithCreditPage() {
  return (
    <div className="space-y-8">
      <CreditReadinessInlineSummary />
      <AdvisoryBlueprintPage />
    </div>
  )
}
