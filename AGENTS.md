# AGENTS.md

## Project type

This is a root-level Vite React TypeScript project.

- Run commands from the repository root: `D:\projects\finsight-cfo`
- Do not assume there is a `frontend/` folder.
- Do not convert this project to Next.js.
- Do not create Next.js `app/` routes.

## UI work

Before UI work, read:

- `docs/product/SYSTEM_DESIGN.md`
- `docs/product/DESIGN_SYSTEM.md`
- `docs/product/COMPONENT_ARCHITECTURE.md`

Follow the existing Softform Financial Intelligence UI visual system. Do not change the visual system unless explicitly requested.

## Finance logic

Do not invent finance logic.

Avoid adding calculations, risk models, eligibility rules, lending decisions, or backend assumptions unless explicitly requested and specified.

## Build artifacts and dependencies

Do not commit:

- `dist/`
- `node_modules/`
- `.env`
- `.env.local`
- log files

## Validation

Before reporting done, run:

```bash
npm run lint
npm run build
```

Also check:

```bash
git status --short
```

Do not commit unless explicitly asked.
