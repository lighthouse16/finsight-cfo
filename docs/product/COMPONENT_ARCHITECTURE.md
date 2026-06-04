# Component Architecture

FinSight CFO is a root-level Vite React TypeScript project. This document defines the frontend source structure for scaling from a landing page into a product app.

## Directory responsibilities

### `src/components/ui`

Small shared UI primitives with no product-specific behavior.

Examples:

- buttons
- inputs
- badges
- tabs
- cards
- empty states

Use this folder when a component is reusable across landing, platform, and future features.

### `src/components/layout`

Shared layout shells and navigation structures.

Examples:

- app shell
- sidebar
- top bar
- page frame
- section container

Layout components may compose UI primitives but should not contain feature-specific data logic.

### `src/components/landing`

Landing-page-only components.

Rules:

- Keep marketing sections here.
- Do not place platform dashboard components here.
- Do not change landing copy or CTA labels during structure-only work.

### `src/components/visual`

Reusable visual, motion, animation, and decorative components.

Examples:

- scroll wrappers
- parallax sections
- animated backgrounds
- 3D icons
- non-business data visuals

These components must not contain finance logic or backend calls.

### `src/components/platform`

Shared platform-level components that are reusable across product routes.

Platform Component Responsibilities:
- `src/components/platform/PlatformShell.tsx` owns the overall platform layout shell, collapsible sidebar states, subtle scrollbar behavior, and mobile drawer transitions.
- `SidebarNav` owns navigation link rendering, navigation grouping, and receives the `collapsed` and `mobile` state props from `PlatformShell`.
- `TopCommandBar` renders workspace switching, profile triggers, and global actions. It acts strictly as a workspace control surface and must not contain arbitrary preview or demo badges.
- `PageHeader` handles page title, primary header actions layout, responsive wrapping, and the `titleAddon` slot (e.g. for accessible info tooltips).
- `EmptyModuleState` is for intentional placeholders only (e.g., indicating modules awaiting company data connectors).

Feature-specific widgets should stay inside their feature folder.

### `src/features/market-watch`

Market Watch feature module.

Expected structure:
```text
src/features/market-watch/
  api/
    marketWatchApi.ts
  components/
  data/
    marketWatchSeed.ts
  types.ts
  MarketWatchPage.tsx
```

Directory and File Responsibilities:
- `MarketWatchPage.tsx` acts as the root orchestrator that assembles the page header, summary metric cards, tab navigation, and responsive sub-views.
- `components/` owns all tab views, card presentations, and feature-specific modular UI components.
- `components/MarketMetricCard.tsx` owns the Market Watch executive signal card presentation. It must keep the compact label/severity top row, prominent non-truncated status, concise implication line, and lightweight bottom source/freshness microcopy aligned with the Executive Signal Card Pattern in `SYSTEM_DESIGN.md`.
- `data/marketWatchSeed.ts` contains strictly safe local mockup/seed data only. No real or simulated live computations.
- `api/marketWatchApi.ts` serves as the future backend swap point. All data retrieval should go through here.
- `types.ts` owns the feature-specific data contracts and type definitions.

Rules:
- `components/` contains Market Watch-only UI.
- `data/` contains static seed/config data only until real data integration exists.
- `types.ts` contains feature-specific TypeScript types.
- Do not add finance calculations or real Market Watch logic until explicitly requested.

### `src/pages`

Route-level page components.

Pages compose layout, shared components, and feature modules. Pages should stay thin and avoid embedding complex reusable UI directly.

### `src/routes`

Routing configuration for the Vite React app.

Rules:

- Use React Router.
- Do not create Next.js `app/` or file-system routes.
- Unknown routes must render a not-found placeholder rather than a blank screen.

## Component naming conventions

- Use `PascalCase` for component filenames and exported React components.
- Use descriptive names: `PlatformPlaceholderPage`, not `Placeholder`.
- Keep one primary component per file unless small local helpers are tightly coupled.
- Hooks use `useCamelCase` and live in `src/hooks` unless feature-specific.
- Types use `PascalCase` and should be exported from the nearest relevant `types.ts`.

## Feature folder conventions

A feature folder owns product-specific UI, data, and types for one domain.

Use feature folders when:

- the component is only meaningful inside one product area
- the data model is domain-specific
- the component would not be reused by landing or other platform routes

Feature folders should avoid importing from other feature folders directly unless a shared abstraction has been moved into `src/components`, `src/hooks`, or `src/lib`.

## Shared vs feature components

Create a shared component when:

- it is used by two or more unrelated areas
- it has no feature-specific business meaning
- its API can stay generic and stable

Keep a component feature-local when:

- it depends on feature-specific language or data shape
- it is only used by one product route
- making it generic would add unnecessary abstraction

When unsure, keep the component feature-local first. Promote it to shared only after a second real use case appears.

## Platform Features & Engineering Rules

### API Abstraction Rule

Market Watch and other feature presentation components must never call backend endpoints, database systems, or external third-party APIs directly. All data access must be routed through the dedicated feature API boundary (e.g., `src/features/market-watch/api/marketWatchApi.ts` functions) or passed down strictly as props. This guarantees high testability, clean boundaries, and a singular swap point for future real data integration.

### UI Safety Rule

FinSight CFO is a decision-grade workspace built on trust. Feature components must never make fake real-time claims, show fake credit scoring, calculate speculative "approval probabilities," or present unverified bank/compliance claims. If features require connected company data to produce results, they should use `EmptyModuleState` or clearly marked "Requires Connected Workspace" states rather than mocking fake telemetry.
