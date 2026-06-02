import { NavLink } from 'react-router-dom'
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
  X,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowLeft,
} from 'lucide-react'
import clsx from 'clsx'
import { type ElementType } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

type NavItem = {
  label: string
  path: string
  icon: ElementType
}

const navItems: NavItem[] = [
  { label: 'Overview',         path: '/platform/overview',         icon: LayoutDashboard  },
  { label: 'Market Watch',     path: '/platform/market-watch',     icon: TrendingUp       },
  { label: 'Data Room',        path: '/platform/data-room',        icon: FolderOpen       },
  { label: 'Financial Health', path: '/platform/financial-health', icon: HeartPulse       },
  { label: 'Credit Readiness', path: '/platform/credit-readiness', icon: ShieldCheck      },
  { label: 'Funding Strategy', path: '/platform/funding-strategy', icon: Landmark         },
  { label: 'Valuation',        path: '/platform/valuation',        icon: BarChart3        },
  { label: 'AI CFO',           path: '/platform/ai-cfo',           icon: BotMessageSquare },
  { label: 'Reports',          path: '/platform/reports',          icon: FileText         },
  { label: 'Settings',         path: '/platform/settings',         icon: Settings         },
]

type SidebarNavProps = {
  isOpen: boolean
  onClose: () => void
  /** Desktop-only collapsed state. Mobile always shows full sidebar as a drawer. */
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function SidebarNav({
  isOpen,
  onClose,
  collapsed,
  onToggleCollapse,
}: SidebarNavProps) {
  const reducedMotion = useReducedMotion()

  return (
    <>
      {/* Mobile backdrop — only shown when drawer is open on small screens */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-softform-navy-950/20 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/*
        Aside sizing strategy:
        - Mobile: always 272px wide, transforms off-screen when closed
        - Desktop (lg+): 272px expanded | 88px collapsed
        Width drives the flex layout — main content expands automatically.
        Transition applies only to width on desktop to avoid fighting the
        mobile transform transition.
      */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col',
          'w-[272px]',
          // Desktop width override
          collapsed ? 'lg:w-[88px]' : 'lg:w-[272px]',
          // Desktop width transition (respects reduced motion)
          !reducedMotion && 'lg:transition-[width] lg:duration-300 lg:ease-out',
          // Mobile: slide in/out; desktop: always in-flow, no transform
          'transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'lg:relative lg:z-auto lg:translate-x-0',
        )}
      >
        {/* Floating capsule — 12px inset margin */}
        <div className="m-3 flex flex-1 flex-col overflow-hidden rounded-[28px] border border-white/70 bg-[linear-gradient(145deg,rgba(255,255,255,0.74),rgba(232,244,241,0.66))] shadow-[0_28px_86px_rgba(8,17,31,0.18),0_12px_30px_rgba(8,17,31,0.08),inset_0_1px_0_rgba(255,255,255,0.82)] backdrop-blur-[22px]">

          {/* ── Header ─────────────────────────────────────────── */}
          <div
            className={clsx(
              'flex shrink-0 items-center border-b border-white/50',
              // Mobile always shows full header; desktop switches on collapsed
              collapsed
                ? 'gap-3 px-5 pb-5 pt-6 lg:justify-center lg:gap-0 lg:px-3 lg:py-5'
                : 'gap-3 px-5 pb-5 pt-6',
            )}
          >
            {/* FS logo mark */}
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-xs font-bold text-white shadow-[0_8px_24px_rgba(8,17,31,0.28)]"
              aria-hidden="true"
            >
              FS
            </span>

            {/* Product name — visible on mobile always; hidden on desktop when collapsed */}
            <span
              className={clsx(
                'truncate text-[15px] font-semibold text-softform-navy-950',
                collapsed ? 'lg:hidden' : '',
              )}
            >
              FinSight CFO
            </span>

            {/* Mobile-only close button */}
            <button
              type="button"
              onClick={onClose}
              className="ml-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-softform-text-muted transition hover:bg-white/50 hover:text-softform-navy-900 lg:hidden"
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
          </div>

          {/* ── Navigation ─────────────────────────────────────── */}
          <nav
            className={clsx(
              'flex-1 overflow-y-auto py-4',
              // Mobile always has full padding; desktop narrowed when collapsed
              collapsed ? 'px-3 lg:px-2' : 'px-3',
            )}
            aria-label="Platform navigation"
          >
            <ul className="space-y-1">
              {navItems.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    onClick={onClose}
                    // Accessible name for icon-only mode on desktop
                    title={item.label}
                    aria-label={item.label}
                    className={({ isActive }) =>
                      clsx(
                        'group flex items-center rounded-2xl text-[13.5px] font-medium transition-all duration-200',
                        // Mobile always expanded; desktop switches on collapsed
                        collapsed
                          ? 'gap-3 px-3.5 py-2.5 lg:justify-center lg:gap-0 lg:px-2 lg:py-3'
                          : 'gap-3 px-3.5 py-2.5',
                        isActive
                          ? 'bg-white/70 text-softform-navy-950 shadow-[0_4px_16px_rgba(8,17,31,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]'
                          : 'text-softform-text-secondary hover:bg-white/40 hover:text-softform-navy-900',
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <item.icon
                          size={18}
                          strokeWidth={isActive ? 2 : 1.5}
                          className={clsx(
                            'shrink-0 transition-colors',
                            isActive
                              ? 'text-softform-teal-deep'
                              : 'text-softform-text-muted group-hover:text-softform-text-secondary',
                          )}
                        />
                        {/* Label: always visible on mobile; hidden on desktop when collapsed */}
                        <span
                          className={clsx(
                            'truncate',
                            collapsed ? 'lg:hidden' : '',
                          )}
                        >
                          {item.label}
                        </span>
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* ── Footer ─────────────────────────────────────────── */}
          <div
            className={clsx(
              'border-t border-white/50',
              // Mobile always expanded layout; desktop switches on collapsed
              collapsed
                ? 'flex flex-col gap-2 px-5 py-4 lg:items-center lg:px-2 lg:py-3'
                : 'flex items-center px-5 py-4',
            )}
          >
            {/* Back to landing */}
            <NavLink
              to="/"
              title="Back to landing"
              aria-label="Back to landing"
              className={clsx(
                'flex items-center text-xs font-medium text-softform-text-muted transition hover:text-softform-navy-900',
                collapsed
                  ? 'gap-2 lg:justify-center'
                  : 'gap-2',
              )}
            >
              {/* Dot bullet — shown when expanded */}
              <span
                className={clsx(
                  'inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-softform-aqua-300',
                  collapsed ? 'lg:hidden' : '',
                )}
              />
              {/* ArrowLeft icon — shown when collapsed on desktop */}
              <ArrowLeft
                size={14}
                className={clsx('shrink-0', collapsed ? 'hidden lg:block' : 'hidden')}
              />
              <span className={clsx(collapsed ? 'lg:hidden' : '')}>
                Back to landing
              </span>
            </NavLink>

            {/* Desktop collapse/expand toggle — never shown on mobile */}
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              className={clsx(
                'hidden lg:flex',
                'h-8 w-8 shrink-0 items-center justify-center rounded-xl',
                'border border-white/50 bg-white/30 text-softform-text-muted',
                'shadow-[0_2px_8px_rgba(8,17,31,0.06),inset_0_1px_0_rgba(255,255,255,0.7)]',
                'backdrop-blur-sm',
                'transition-all duration-200',
                'hover:bg-white/60 hover:text-softform-navy-900 hover:shadow-[0_4px_12px_rgba(8,17,31,0.10)]',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-softform-teal-500/40',
                collapsed ? '' : 'ml-auto',
              )}
            >
              {collapsed
                ? <PanelLeftOpen  size={15} strokeWidth={1.75} />
                : <PanelLeftClose size={15} strokeWidth={1.75} />
              }
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
