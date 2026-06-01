import SmoothScrollProvider from '../components/visual/SmoothScrollProvider'
import CinematicHero from '../components/landing/CinematicHero'
import FintechFooter from '../components/landing/FintechFooter'

export default function LandingPage() {
  return (
    <SmoothScrollProvider>
      <div className="softform-page min-h-screen text-softform-text-primary">
        <main>
          <CinematicHero />
        </main>
        <FintechFooter />
      </div>
    </SmoothScrollProvider>
  )
}
