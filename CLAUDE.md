# Finsight CFO - Project Instructions

## Project Context

Finsight CFO is an AI-powered CFO workspace for SMEs and financial stakeholders. This is a professional, banking-grade fintech product that helps businesses understand:

- Financial health and performance
- Cashflow analysis and forecasting
- Debt capacity and credit readiness
- Market risk assessment
- ESG-linked finance opportunities
- Advisor recommendations
- Bank/RM-review-safe next actions

## Product Principles

### UI/UX Standards

The product MUST feel:
- Banking-grade and enterprise fintech
- Professional and trustworthy
- Calm, structured, and data-driven
- Commercially usable and production-ready
- Senior-built with strong visual hierarchy

The product MUST NOT feel:
- Like a crypto dashboard or colorful startup toy
- Like a generic admin template or card slop
- Like a chatbot-only demo or prototype
- Like random cards of text with weak hierarchy
- Like a toy or internal debug tool

### Visual Hierarchy Requirements

- Strong typographic hierarchy (clear heading levels)
- Purposeful spacing and alignment
- High information density without clutter
- Professional table and chart presentation
- Responsive behavior across devices
- Accessible color contrast and interaction states

## Finance Language Rules

### AVOID these words in visible UI:
- "approved", "guaranteed", "eligible", "safe", "no risk"
- "AI decided", "final decision", "automatic approval"
- "demo", "mock", "synthetic", "dataset", "debug", "internal"
- Overconfident lending language

### PREFER these alternatives:
- "indicative", "appears suitable", "based on available records"
- "for RM review", "subject to bank policy", "pending verification"
- "requires review", "available records", "application workspace"
- "review-ready", "preliminary assessment"

## Tech Stack

Detect the stack by inspecting:
- `package.json` for dependencies
- `tsconfig.json` or `jsconfig.json` for TypeScript/JavaScript
- `vite.config.*` or `next.config.*` for build tools
- `src/` or `app/` directory structure
- `tailwind.config.*` for styling approach

Common patterns:
- React + TypeScript + Vite + Tailwind CSS
- Next.js + TypeScript + Tailwind CSS
- React + shadcn/ui components

## Coding Rules

### Before Editing
1. **Read first**: Always inspect files before editing
2. **Understand context**: Check imports, types, and dependencies
3. **Preserve structure**: Keep routes, service calls, and component boundaries
4. **Match style**: Follow existing patterns and conventions

### During Implementation
1. **Focused changes**: Edit only what's needed for the task
2. **Preserve routes**: Don't modify routing unless explicitly asked
3. **Preserve backend calls**: Keep API/service integration intact
4. **Avoid new dependencies**: Use existing libraries when possible
5. **Type safety**: Maintain TypeScript types and interfaces
6. **Accessibility**: Ensure WCAG compliance for UI changes

### After Changes
1. **Run lint**: Execute `npm run lint` or equivalent
2. **Run build**: Execute `npm run build` or equivalent
3. **Check types**: Verify TypeScript compilation
4. **Test locally**: Run dev server if UI changes made

## Verification Commands

Detect and use project-specific commands:

```bash
# Lint
npm run lint
# or
pnpm lint
# or
yarn lint

# Build
npm run build
# or
pnpm build
# or
yarn build

# Type check
npm run type-check
# or
tsc --noEmit

# Dev server
npm run dev
# or
pnpm dev
# or
yarn dev
```

## Workflow Rules

### For UI/UX Changes
1. Use `/fintech-taste-review` to assess current state
2. Use `/ui-ux-pro-review` for deeper UX analysis
3. Implement changes with focus on hierarchy and polish
4. Run lint and build to verify
5. Use `/prepush-check` before committing

### For Feature Development
1. Use `/senior-dev-cycle` for orchestrated team workflow
2. Product architect plans the approach
3. Senior frontend engineer implements
4. Code reviewer finds and fixes bugs
5. QA engineer verifies build and release readiness

### For Finance Copy
1. Use `/finance-copy-review` to scan visible UI text
2. Replace risky wording with bank-review-safe alternatives
3. Verify changes don't break UI layout

### Before Committing
1. Run `/prepush-check` to verify:
   - Git status is clean (no accidental staged files)
   - Lint passes
   - Build succeeds
   - No secrets or tokens in staged files
2. Review suggested commit message
3. Commit only when safe

## Subagents Available

- **product-architect**: Plans scope and protects IA/routes
- **senior-frontend-engineer**: Implements focused React/UI changes
- **code-reviewer-bugfixer**: Reviews code and fixes bugs
- **qa-release-engineer**: Verifies release readiness
- **finance-domain-reviewer**: Reviews finance/credit/ESG wording
- **design-taste-reviewer**: Reviews UI hierarchy and product polish

## Skills Available

- **/fintech-taste-review**: Project-specific UI taste review
- **/ui-ux-pro-review**: Deep UX quality analysis
- **/senior-dev-cycle**: Orchestrated team workflow
- **/prepush-check**: Pre-commit safety verification
- **/finance-copy-review**: Finance language safety check

## File Organization

```
src/
  components/     # Reusable UI components
  pages/          # Page-level components
  services/       # API and data services
  types/          # TypeScript type definitions
  utils/          # Utility functions
  styles/         # Global styles

.claude/
  agents/         # Subagent definitions
  skills/         # Project-specific skills
  settings.json   # Project configuration
```

## Common Pitfalls to Avoid

1. **Don't break routes**: Preserve navigation structure
2. **Don't add unnecessary deps**: Use existing libraries
3. **Don't skip verification**: Always run lint/build
4. **Don't use risky finance words**: Follow language rules
5. **Don't create generic card slop**: Maintain strong hierarchy
6. **Don't commit without checking**: Use `/prepush-check`

## Quality Standards

- TypeScript strict mode compliance
- ESLint rules passing
- Build with zero errors
- Responsive design (mobile, tablet, desktop)
- Accessible (WCAG AA minimum)
- Professional fintech visual quality
- Bank-review-safe language
