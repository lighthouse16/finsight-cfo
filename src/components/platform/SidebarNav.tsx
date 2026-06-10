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
  ScrollText,
} from 'lucide-react'
import clsx from 'clsx'
import { type ElementType, useState, useRef, useEffect } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

import { motion } from 'framer-motion'

type NavItem = {
  label: string
  path: string
  icon: ElementType
}

type NavGroup = {
  label: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Workspace',
    items: [
      { label: 'Overview',  path: '/platform/overview',   icon: LayoutDashboard },
      { label: 'Data Room', path: '/platform/data-room',  icon: FolderOpen      },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'Market Watch',     path: '/platform/market-watch',     icon: TrendingUp  },
      { label: 'Financial Health', path: '/platform/financial-health', icon: HeartPulse  },
      { label: 'Credit Readiness', path: '/platform/credit-readiness', icon: ShieldCheck },
    ],
  },
  {
    label: 'Funding',
    items: [
      { label: 'Funding Strategy',   path: '/platform/funding-strategy',   icon: Landmark },
      { label: 'Advisory Blueprint', path: '/platform/advisory-blueprint', icon: ScrollText },
      { label: 'Valuation',          path: '/platform/valuation',          icon: BarChart3 },
    ],
  },
  {
    label: 'Assistant & Output',
    items: [
      { label: 'AI CFO',   path: '/platform/ai-cfo',   icon: BotMessageSquare },
      { label: 'Reports',  path: '/platform/reports',  icon: FileText         },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Settings', path: '/platform/settings', icon: Settings },
    ],
  },
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
  const [isScrolling, setIsScrolling] = useState(false)
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleScroll = () => {
    setIsScrolling(true)
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current)
    }
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false)
    }, 800)
  }

  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [])

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-softform-navy-950/20 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/*
        Aside sizing:
        - Mobile: always 272px, transforms off-screen when closed
        - Desktop lg+: 272px expanded | 88px collapsed
        Main content area flexes to fill remaining width automatically.
      */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col',
          'w-[272px]',
          collapsed ? 'lg:w-[88px]' : 'lg:w-[272px]',
          !reducedMotion && 'lg:transition-[width] lg:duration-300 lg:ease-out',
          'transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'lg:relative lg:z-auto lg:translate-x-0',
        )}
      >
        {/* Floating capsule */}
        <div className="m-3 flex flex-1 flex-col overflow-hidden rounded-[28px] border border-white/70 bg-[linear-gradient(145deg,rgba(255,255,255,0.74),rgba(232,244,241,0.66))] shadow-[0_28px_86px_rgba(8,17,31,0.18),0_12px_30px_rgba(8,17,31,0.08),inset_0_1px_0_rgba(255,255,255,0.82)] backdrop-blur-[22px]">

          {/* ── Header ──────────────────────────────────────────── */}
          <div
            className={clsx(
              'flex shrink-0 items-center border-b border-white/50',
              collapsed
                ? 'gap-3 px-5 pb-5 pt-6 lg:justify-center lg:gap-0 lg:px-3 lg:py-5'
                : 'gap-3 px-5 pb-5 pt-6',
            )}
          >
            {/* Logo mark — links to workspace home */}
            <NavLink
              to="/platform/overview"
              aria-label="FinSight CFO workspace home"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] text-xs font-bold text-white shadow-[0_8px_24px_rgba(8,17,31,0.28)] transition hover:opacity-90"
            >
              FS
            </NavLink>

            {/* Product name */}
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

          {/* ── Navigation ──────────────────────────────────────── */}
          <nav
            onScroll={handleScroll}
            className={clsx(
              'flex-1 overflow-y-auto overflow-x-hidden py-3 platform-sidebar-scroll',
              isScrolling && 'is-scrolling',
              collapsed ? 'px-3 lg:px-2' : 'px-3',
            )}
            aria-label="Platform navigation"
          >
            {navGroups.map((group, groupIndex) => (
              <div
                key={group.label}
                className={clsx(groupIndex > 0 && 'mt-3.5')}
              >
                {/* Group separator line — visible in both states, label only when expanded */}
                {groupIndex > 0 && (
                  <div
                    className={clsx(
                      'mb-2 mt-1',
                      // Expanded: faint line + label; collapsed desktop: just a faint line
                      collapsed
                        ? 'mx-2 border-t border-white/40 lg:mx-1'
                        : 'mx-1 border-t border-white/40',
                    )}
                    role="separator"
                  />
                )}

                {/* Group label — hidden on desktop when collapsed */}
                <p
                  className={clsx(
                    'mb-1.5 px-3.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-softform-text-muted/70',
                    // On desktop collapsed state, hide label text entirely
                    collapsed ? 'pt-1.5 lg:hidden' : 'pt-1.5',
                  )}
                  aria-hidden="true"
                >
                  {group.label}
                </p>

                <ul className="space-y-0.5">
                  {group.items.map((item) => (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        onClick={onClose}
                        title={item.label}
                        aria-label={item.label}
                        className={({ isActive }) =>
                          clsx(
                            'group relative flex items-center rounded-2xl text-[13.5px] font-medium transition-all duration-200',
                            collapsed
                              ? 'gap-3 px-3.5 py-2.5 lg:justify-center lg:gap-0 lg:px-2 lg:py-3'
                              : 'gap-3 px-3.5 py-2.5',
                            isActive
                              ? 'text-softform-navy-950 font-semibold'
                              : 'text-softform-text-secondary hover:bg-white/40 hover:text-softform-navy-900',
                          )
                        }
                      >
                        {({ isActive }) => (
                          <>
                            {isActive && !reducedMotion && (
                              <motion.div
                                layoutId="activeSidebarPill"
                                className="absolute inset-0 -z-10 rounded-2xl bg-white/82 border-l-2 border-softform-teal-500 shadow-[0_4px_16px_rgba(8,17,31,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]"
                                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                              />
                            )}
                            {isActive && reducedMotion && (
                              <div
                                className="absolute inset-0 -z-10 rounded-2xl bg-white/82 border-l-2 border-softform-teal-500 shadow-[0_4px_16px_rgba(8,17,31,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]"
                              />
                            )}
                            <item.icon
                              size={18}
                              strokeWidth={isActive ? 2 : 1.5}
                              className={clsx(
                                'shrink-0 transition-colors z-10',
                                isActive
                                  ? 'text-softform-teal-deep'
                                  : 'text-softform-text-muted group-hover:text-softform-text-secondary',
                              )}
                            />
                            <span className={clsx('truncate z-10', collapsed ? 'lg:hidden' : '')}>
                              {item.label}
                            </span>
                          </>
                        )}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>

          {/* ── Footer — collapse toggle only ───────────────────── */}
          <div
            className={clsx(
              'border-t border-white/50',
              collapsed
                ? 'flex items-center justify-center px-2 py-3'
                : 'flex items-center justify-end px-5 py-3',
            )}
          >
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
