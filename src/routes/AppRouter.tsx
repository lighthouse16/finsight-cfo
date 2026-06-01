import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'
import PlatformPlaceholderPage from '../pages/PlatformPlaceholderPage'

const platformRoutes = [
  {
    path: 'market-watch',
    title: 'Market Watch',
    description: 'Market Watch is reserved for a future product build. This route is ready, but the real interface has not been implemented yet.',
  },
  {
    path: 'cashflow',
    title: 'Cashflow',
    description: 'Cashflow workspace routing is prepared for future product screens. No cashflow logic has been added in this structure pass.',
  },
  {
    path: 'credit-readiness',
    title: 'Credit Readiness',
    description: 'Credit Readiness routing is prepared for a future workspace. No credit scoring, eligibility, or finance logic has been added.',
  },
  {
    path: 'advisor',
    title: 'Advisor',
    description: 'Advisor routing is prepared for future recommendation workflows. No advisory logic has been added.',
  },
  {
    path: 'ai-cfo',
    title: 'AI CFO',
    description: 'AI CFO routing is prepared for future workspace UI. No AI workflow or backend integration has been added.',
  },
  {
    path: 'reports',
    title: 'Reports',
    description: 'Reports routing is prepared for future report screens. No reporting logic has been added.',
  },
  {
    path: 'data-room',
    title: 'Data Room',
    description: 'Data Room routing is prepared for future document workflows. No upload or storage logic has been added.',
  },
  {
    path: 'settings',
    title: 'Settings',
    description: 'Settings routing is prepared for future account and workspace preferences. No settings logic has been added.',
  },
]

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/platform" element={<Navigate to="/platform/market-watch" replace />} />
        {platformRoutes.map((route) => (
          <Route
            key={route.path}
            path={`/platform/${route.path}`}
            element={
              <PlatformPlaceholderPage
                eyebrow="Prepared route"
                title={route.title}
                description={route.description}
              />
            }
          />
        ))}
        <Route path="*" element={<PlatformPlaceholderPage isNotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
