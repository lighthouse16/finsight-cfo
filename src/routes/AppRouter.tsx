import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  FolderOpen,
  HeartPulse,
  ShieldCheck,
  Landmark,
  BarChart3,
  BotMessageSquare,
  FileText,
  Settings,
} from 'lucide-react'
import { type ElementType } from 'react'
import LandingPage from '../pages/LandingPage'
import LoginPage from '../pages/LoginPage'
import SignupPage from '../pages/SignupPage'
import PlatformPlaceholderPage from '../pages/PlatformPlaceholderPage'
import NotFoundPage from '../pages/NotFoundPage'
import PlatformShell from '../components/platform/PlatformShell'
import MarketWatchPage from '../features/market-watch/MarketWatchPage'

type PlatformRoute = {
  path: string
  title: string
  subtitle: string
  icon: ElementType
  modulePurpose: string
}

const platformRoutes: PlatformRoute[] = [
  {
    path: 'overview',
    title: 'Overview',
    subtitle:
      'Your CFO command center for financial health, market pressure, credit readiness, and next actions.',
    icon: LayoutDashboard,
    modulePurpose:
      'The Overview module will consolidate key indicators from across your workspace into a single decision-ready view.',
  },
  {
    path: 'market-watch',
    title: 'Market Watch',
    subtitle:
      'Track rates, FX, sector benchmarks, and market pressure signals that may affect cashflow and funding decisions.',
    icon: TrendingUp,
    modulePurpose:
      'Market Watch will surface rate movements, sector benchmarks, and external pressure signals relevant to your funding and cashflow planning.',
  },
  {
    path: 'data-room',
    title: 'Data Room',
    subtitle:
      'Upload, organize, and review the financial records that power your CFO workspace.',
    icon: FolderOpen,
    modulePurpose:
      'The Data Room will provide a secure workspace for uploading, organizing, and reviewing the financial records that drive your analysis.',
  },
  {
    path: 'financial-health',
    title: 'Financial Health',
    subtitle:
      'Understand liquidity, leverage, coverage, receivables, and cashflow quality.',
    icon: HeartPulse,
    modulePurpose:
      'Financial Health will present liquidity, leverage, coverage, and cashflow quality indicators derived from your uploaded records.',
  },
  {
    path: 'credit-readiness',
    title: 'Credit Readiness',
    subtitle:
      'See how your financial profile may appear before lender conversations.',
    icon: ShieldCheck,
    modulePurpose:
      'Credit Readiness will help you understand how your financial profile may be perceived in lender conversations, based on available records.',
  },
  {
    path: 'funding-strategy',
    title: 'Funding Strategy',
    subtitle:
      'Compare timing, channels, approval fit, loan structure, and stress scenarios.',
    icon: Landmark,
    modulePurpose:
      'Funding Strategy will help compare timing, channels, structure options, and stress scenarios to support funding decisions.',
  },
  {
    path: 'valuation',
    title: 'Valuation',
    subtitle:
      'Build an indicative valuation view from financial forecasts, market inputs, and conservative assumptions.',
    icon: BarChart3,
    modulePurpose:
      'The Valuation module will support indicative valuation views built from financial forecasts, market inputs, and conservative assumptions.',
  },
  {
    path: 'ai-cfo',
    title: 'AI CFO',
    subtitle:
      'Ask questions across your financial records, market context, and funding strategy.',
    icon: BotMessageSquare,
    modulePurpose:
      'AI CFO will provide a conversational interface to explore questions across your financial records, market context, and funding strategy.',
  },
  {
    path: 'reports',
    title: 'Reports',
    subtitle:
      'Generate CFO snapshots, funding-readiness summaries, and lender-facing reports.',
    icon: FileText,
    modulePurpose:
      'Reports will generate CFO snapshots, funding-readiness summaries, and lender-facing documents from your workspace data.',
  },
  {
    path: 'settings',
    title: 'Settings',
    subtitle:
      'Manage workspace preferences, data sources, and product configuration.',
    icon: Settings,
    modulePurpose:
      'Settings will allow you to manage workspace preferences, data source connections, and product configuration.',
  },
]

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page — untouched */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Login page */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Signup page */}
        <Route path="/signup" element={<SignupPage />} />

        {/* Platform shell with nested routes */}
        <Route path="/platform" element={<PlatformShell />}>
          <Route index element={<Navigate to="market-watch" replace />} />
          {platformRoutes.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={
                route.path === 'market-watch' ? (
                  <MarketWatchPage />
                ) : (
                  <PlatformPlaceholderPage
                    title={route.title}
                    subtitle={route.subtitle}
                    icon={route.icon}
                    modulePurpose={route.modulePurpose}
                  />
                )
              }
            />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Route>

        {/* Global not-found fallback — standalone wrapper */}
        <Route
          path="*"
          element={
            <div className="softform-page flex min-h-dvh items-center justify-center px-4 text-softform-text-primary">
              <div className="w-full max-w-2xl">
                <NotFoundPage />
              </div>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
