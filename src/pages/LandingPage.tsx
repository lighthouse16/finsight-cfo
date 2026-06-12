import SmoothScrollProvider from '../components/visual/SmoothScrollProvider'
import CinematicHero from '../components/landing/CinematicHero'
import TrustStrip from '../components/landing/TrustStrip'
import ProblemSection from '../components/landing/ProblemSection'
import ProductPreview from '../components/landing/ProductPreview'
import IntelligenceModules from '../components/landing/IntelligenceModules'
import ExplainabilitySection from '../components/landing/ExplainabilitySection'
import WorkflowSection from '../components/landing/WorkflowSection'
import SecuritySection from '../components/landing/SecuritySection'
import WaitlistCTA from '../components/landing/WaitlistCTA'
import FintechFooter from '../components/landing/FintechFooter'

export default function LandingPage() {
  return (
    <SmoothScrollProvider>
      <div className="softform-page min-h-screen text-softform-text-primary">
        <main>
          <CinematicHero />
          <TrustStrip />
          <ProblemSection />
          <ProductPreview />
          <IntelligenceModules />
          <ExplainabilitySection />
          <WorkflowSection />
          <SecuritySection />
          <WaitlistCTA />
        </main>
        <FintechFooter />
      </div>
    </SmoothScrollProvider>
  )
}
