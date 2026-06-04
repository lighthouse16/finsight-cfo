# FinSight CFO Design System

The source of truth for FinSight CFO's visual system is:

- [SYSTEM_DESIGN.md](file:///d:/projects/finsight-cfo/docs/product/SYSTEM_DESIGN.md)

## Visual system

FinSight CFO uses **Softform Financial Intelligence UI**.

This is a light-first tactile fintech interface system combining frosted surfaces, soft elevation, rounded dashboard architecture, atmospheric gradients, and precise financial data hierarchy.

## Implementation rule

When scaling or modifying visual styles, use [SYSTEM_DESIGN.md](file:///d:/projects/finsight-cfo/docs/product/SYSTEM_DESIGN.md) as the source of truth for:

- colors
- gradients
- surfaces
- radius
- shadows
  - framed background shadows must use deep navy only: `rgba(8, 17, 31, ...)` from `--navy-950: #08111f`
- typography styling
- component visual rules
- motion treatment
- responsive visual behavior
- accessibility requirements
- anti-patterns
- platform shell patterns (e.g., floating Softform sidebar, collapsible states, top command bar)
- page header patterns (e.g., strong concise titles, accessible info tooltips, action wrapping)
- Market Watch UI patterns (e.g., executive signal cards, chip/badge conventions, tooltip patterns, market data source language)

## Content rule

Visual implementation must not change:

- page content
- marketing copy
- section order
- component names
- user flows
- waitlist behavior
- product positioning
- footer disclaimer

## Recent Patterns & Layout Enhancements

### 1. Source Provenance Tooltip Pattern
- **Access over clutter**: Data sources, as-of dates, and freshness markers must live inside header-adjacent info tooltips (`SourceInfoTooltip.tsx`), not as visible canvas banners or primary chips.
- **Wording**: Use clean user-facing terms in tooltips: *Workspace-derived*, *Context-only*, *Provider not configured*, *Source pending*, *Company records required*.

### 2. Vertical Flow Redesign (Rates, FX, and GBA)
- **Vertical Hierarchy**: Avoid right-sidebar grids that create awkward whitespace. Use a full-width vertical layout: (A) macro rates/pairs cards, (B) compact horizontal company exposure strips, (C) detail/watch grids.
- **Secondary calculations**: If data model context is not fully ready (e.g., *Funding Window*), hide the large container entirely and list requirements in a small footnote.

### 3. Cohesive Motion System
- **Timing & Easing**: 
  - Standard ease: `cubic-bezier(0.22, 1, 0.36, 1)` (duration 220-300ms)
  - Exit ease: `cubic-bezier(0.4, 0, 0.2, 1)` (duration 120-160ms)
- **Shared Layouts**: Active tab capsules must slide smoothly using shared layout animations (`layoutId="activeTabPill"`).
- **Reduced Motion**: Respect system preferences by removing staggers and translate displacements when `prefers-reduced-motion` is active.

