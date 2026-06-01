---
name: Prepush Check
description: Pre-commit verification - check git status, lint, build, secrets, and staged artifacts
context: fork
allowed-tools: Read, Glob, Grep, Bash
---

# Prepush Check

Verify that code is safe to commit and push.

## When to Use

Use this skill before committing or pushing code to verify:
- Git status is clean (no accidental staged files)
- Lint passes
- Build succeeds
- No secrets or tokens in staged files
- No build artifacts accidentally staged

## Verification Steps

### 1. Git Status Check

```bash
git status
```

Check for:
- **Uncommitted changes**: Files modified but not staged
- **Untracked files**: New files that should be committed or ignored
- **Staged files**: Verify only intended files are staged
- **Build artifacts**: Detect accidentally staged dist/, build/, .next/, etc.
- **Secret files**: Detect accidentally staged .env, credentials.json, etc.

### 2. Lint Check

```bash
npm run lint || pnpm lint || yarn lint
```

Verify:
- No linting errors
- No critical linting warnings
- Code quality standards pass

### 3. Build Check

```bash
npm run build || pnpm build || yarn build
```

Verify:
- Build completes successfully
- No build errors
- Bundle size is reasonable
- No critical warnings

### 4. Secret Scan

Search staged files for common secret patterns:
- API keys: `API_KEY=`, `APIKEY=`, `apiKey:`
- Tokens: `TOKEN=`, `token:`, `access_token:`
- Passwords: `PASSWORD=`, `password:`
- Private keys: `-----BEGIN PRIVATE KEY-----`
- Long base64 strings (potential secrets)

Check these file types:
- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.json`
- `config.js`, `config.ts` (for hardcoded secrets)

### 5. Build Artifact Check

Detect accidentally staged build artifacts:
- `dist/`, `build/`, `.next/`, `out/`
- `*.js.map`, `*.css.map` (source maps)
- `node_modules/` (should never be staged)
- `.cache/`, `.turbo/`

## Output Format

Provide a pre-push readiness report:

```
Pre-Push Readiness Report
==========================

Git Status: ✓ Clean / ✗ Issues found
- [Details if issues found]

Staged Files:
- [List of staged files]
- [Flag any suspicious files]

Lint: ✓ Passed / ✗ Failed
- [Error/warning details if failed]

Build: ✓ Passed / ✗ Failed
- [Error details if failed]
- Bundle size: [size]

Secret Scan: ✓ Clean / ✗ Secrets detected
- [Details if secrets found]

Build Artifacts: ✓ Clean / ✗ Artifacts staged
- [Details if artifacts found]

Overall: ✓ SAFE TO COMMIT / ✗ NOT SAFE

Blocking Issues:
- [List of issues that must be fixed before commit]

Recommended Actions:
1. [Action to fix issue 1]
2. [Action to fix issue 2]
...

Suggested Commit Message:
"[type]: [description]"
```

## Example Reports

### Example 1: Safe to Commit
```
Pre-Push Readiness Report
==========================

Git Status: ✓ Clean

Staged Files:
- src/components/DebtCapacityCard.tsx
- src/pages/Dashboard.tsx
- src/types/finance.ts

Lint: ✓ Passed

Build: ✓ Passed
- Bundle size: 245 KB (gzipped)

Secret Scan: ✓ Clean

Build Artifacts: ✓ Clean

Overall: ✓ SAFE TO COMMIT

Suggested Commit Message:
"feat: add debt capacity calculator to dashboard"
```

### Example 2: Not Safe
```
Pre-Push Readiness Report
==========================

Git Status: ✗ Issues found
- Untracked file: .env.local (contains secrets)

Staged Files:
- src/components/Dashboard.tsx
- dist/index.js ⚠️ Build artifact
- .env.local ⚠️ Secret file

Lint: ✗ Failed
- 2 errors in src/components/Dashboard.tsx

Build: ✓ Passed

Secret Scan: ✗ Secrets detected
- .env.local:3 contains API_KEY=sk_live_...
- src/config.ts:8 contains hardcoded token

Build Artifacts: ✗ Artifacts staged
- dist/index.js should not be committed

Overall: ✗ NOT SAFE

Blocking Issues:
1. Remove .env.local from staging (contains secrets)
2. Remove dist/index.js from staging (build artifact)
3. Fix linting errors in Dashboard.tsx
4. Remove hardcoded token from config.ts

Recommended Actions:
1. Run: git reset HEAD .env.local dist/
2. Fix linting errors: npm run lint
3. Remove hardcoded secrets from config.ts
4. Re-run /prepush-check
```

## Principles

- **Safety first**: Block commits that contain secrets or build artifacts
- **Clear reporting**: Provide actionable feedback
- **No automatic fixes**: Report issues but don't fix them automatically
- **Comprehensive checks**: Verify all aspects of commit safety
