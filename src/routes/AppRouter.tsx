import { lazy, Suspense, type ElementType } from 'react'
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
  ScrollText,
} from 'lucide-react'
import PlatformShell from '../components/platform/PlatformShell'
import RouteLoadingFallback from '../components/platform/RouteLoadingFallback'

const LandingPage = lazy(() => import('../pages/LandingPage'))
const LoginPage = lazy(() => import('../pages/LoginPage'))
const SignupPage = lazy(() => import('../pages/SignupPage'))
const PlatformPlaceholderPage = lazy(
  () => import('../pages/PlatformPlaceholderPage'),
)
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'))
const MarketWatchPage = lazy(
  () => import('../features/market-watch/MarketWatchPage'),
)
const AdvisoryBlueprintPage = lazy(
  () => import('../features/advisory-blueprint/AdvisoryBlueprintWithCreditPage'),
)
const FinancialHealthPage = lazy(
  () => import('../features/financial-health/FinancialHealthPage'),
)
const CreditReadinessPage = lazy(
  () => import('../features/credit-readiness/CreditReadinessPage'),
)
const FundingStrategyPage = lazy(
  () => import('../features/funding-strategy/FundingStrategyPage'),
)
const DataRoomPage = lazy(() => import('../features/data-room/DataRoomPage'))

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
      'Financial Health presents liquidity, leverage, coverage, receivables, projection, and valuation diagnostics from the active financial snapshot.',
  },
  {
    path: 'credit-readiness',
    title: 'Credit Readiness',
    subtitle:
      'See how your financial profile may appear before lender conversations.',
    icon: ShieldCheck,
    modulePurpose:
      'Credit Readiness helps you understand how your financial profile may be perceived in lender conversations, using the explainable PD proxy scorecard.',
  },
  {
    path: 'funding-strategy',
    title: 'Funding Strategy',
    subtitle:
      'Compare timing, channels, approval fit, loan structure, and stress scenarios.',
    icon: Landmark,
    modulePurpose:
      'Funding Strategy compares channel ranking, candidate facility structures, readiness context, and cross-border funding signals.',
  },
  {
    path: 'advisory-blueprint',
    title: 'Advisory Blueprint',
    subtitle:
      'Context-only financing readiness brief based on demo financial analysis.',
    icon: ScrollText,
    modulePurpose:
      'Advisory Blueprint consolidates financial analysis, precheck, risk score, stress testing, and facility structuring into an advisor-ready brief.',
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

function withShellFallback(element: JSX.Element, copy?: string) {
  return (
    <Suspense fallback={<RouteLoadingFallback copy={copy} />}>
      {element}
    </Suspense>
  )
}

function withPageFallback(element: JSX.Element, copy?: string) {
  return (
    <Suspense
      fallback={
        <div className="softform-page flex min-h-dvh items-center justify-center px-4 text-softform-text-primary">
          <div className="w-full max-w-2xl">
            <RouteLoadingFallback copy={copy} />
          </div>
        </div>
      }
    >
      {element}
    </Suspense>
  )
}

function renderPlatformRoute(route: PlatformRoute) {
  if (route.path === 'market-watch') {
    return withShellFallback(
      <MarketWatchPage />,
      'Loading market intelligence...',
    )
  }

  if (route.path === 'financial-health') {
    return withShellFallback(
      <FinancialHealthPage />,
      'Loading financial health...',
    )
  }

  if (route.path === 'credit-readiness') {
    return withShellFallback(
      <CreditReadinessPage />,
      'Loading credit readiness...',
    )
  }

  if (route.path === 'funding-strategy') {
    return withShellFallback(
      <FundingStrategyPage />,
      'Loading funding strategy...',
    )
  }

  if (route.path === 'advisory-blueprint') {
    return withShellFallback(
      <AdvisoryBlueprintPage />,
      'Loading advisory workspace...',
    )
  }

  if (route.path === 'data-room') {
    return withShellFallback(<DataRoomPage />, 'Loading data room...')
  }

  return withShellFallback(
    <PlatformPlaceholderPage
      title={route.title}
      subtitle={route.subtitle}
      icon={route.icon}
      modulePurpose={route.modulePurpose}
    />,
  )
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page — untouched */}
        <Route
          path="/"
          element={withPageFallback(<LandingPage />, 'Loading FinSight CFO...')}
        />

        {/* Login page */}
        <Route
          path="/login"
          element={withPageFallback(<LoginPage />, 'Loading secure sign in...')}
        />

        {/* Signup page */}
        <Route
          path="/signup"
          element={withPageFallback(<SignupPage />, 'Loading workspace setup...')}
        />

        {/* Platform shell with nested routes */}
        <Route path="/platform" element={<PlatformShell />}>
          <Route index element={<Navigate to="market-watch" replace />} />
          {platformRoutes.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={renderPlatformRoute(route)}
            />
          ))}
          <Route
            path="*"
            element={withShellFallback(<NotFoundPage />, 'Loading route...')}
          />
        </Route>

        {/* Global not-found fallback — standalone wrapper */}
        <Route
          path="*"
          element={withPageFallback(<NotFoundPage />, 'Loading route...')}
        />
      </Routes>
    </BrowserRouter>
  )
}
