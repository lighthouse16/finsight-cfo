---
name: Senior Dev Cycle
description: Orchestrate a senior team workflow - architect plans, engineer implements, reviewer fixes bugs, QA verifies
context: fork
allowed-tools: Agent, Read, Glob, Grep, Bash
---

# Senior Dev Cycle

Orchestrate a professional development workflow using specialized subagents.

## When to Use

Use this skill for non-trivial feature development or UI improvements that benefit from:
- Architectural planning before implementation
- Focused implementation by a senior engineer
- Code review and bug fixing
- Release readiness verification

**Don't use for**: Simple typo fixes, single-line changes, or purely exploratory tasks.

## Workflow Steps

### 1. Product Architect Plans
**Agent**: `product-architect`
**Goal**: Understand scope, identify affected files, plan approach, flag risks

The architect will:
- Read the user's request and clarify scope
- Inspect current codebase structure
- Identify which files/routes/components are affected
- Plan implementation strategy that preserves IA
- Flag potential breaking changes or scope creep
- Define what's in and out of scope

**Output**: Implementation plan with files affected, risks, approach, and verification steps

### 2. Senior Frontend Engineer Implements
**Agent**: `senior-frontend-engineer`
**Goal**: Execute the plan with focused, surgical changes

The engineer will:
- Read affected files to understand current state
- Implement changes following the architect's plan
- Preserve routes, API calls, and component boundaries
- Match existing code style and patterns
- Run lint and build to verify correctness

**Output**: Changed files with implementation complete

### 3. Code Reviewer Fixes Bugs
**Agent**: `code-reviewer-bugfixer`
**Goal**: Review changes and fix any bugs found

The reviewer will:
- Inspect recently modified files
- Find TypeScript, React, import, responsive, and accessibility bugs
- Make minimal, surgical fixes
- Run lint and build after fixes
- Report bugs found and fixed

**Output**: Bug report with fixes applied

### 4. QA Engineer Verifies
**Agent**: `qa-release-engineer`
**Goal**: Verify release readiness

The QA engineer will:
- Check git status for uncommitted changes or staged artifacts
- Run lint to verify code quality
- Run build to verify production build succeeds
- Scan for accidentally staged secrets
- Report overall release readiness

**Output**: Release readiness report with blocking issues (if any)

## Implementation

When this skill is invoked, execute the workflow in sequence:

```
1. Spawn product-architect agent
   - Pass user's request
   - Wait for implementation plan
   - Review plan with user if needed

2. Spawn senior-frontend-engineer agent
   - Pass implementation plan
   - Wait for implementation complete
   - Verify files were changed

3. Spawn code-reviewer-bugfixer agent
   - Pass list of changed files
   - Wait for review and fixes
   - Verify lint/build passed

4. Spawn qa-release-engineer agent
   - Run release checks
   - Wait for readiness report
   - Report any blocking issues
```

## Final Output Format

After all agents complete, provide a summary:

```
Senior Dev Cycle Complete
=========================

1. Plan Summary:
   - Scope: [what was planned]
   - Files affected: [list]
   - Risks identified: [list]

2. Implementation:
   - Files changed: [list]
   - Changes made: [brief description]
   - Lint: ✓ Passed / ✗ Failed
   - Build: ✓ Passed / ✗ Failed

3. Code Review:
   - Bugs found: [count]
   - Bugs fixed: [count]
   - Remaining issues: [list if any]

4. Release Readiness:
   - Git status: ✓ Clean / ✗ Issues
   - Lint: ✓ Passed / ✗ Failed
   - Build: ✓ Passed / ✗ Failed
   - Secrets: ✓ Clean / ✗ Detected
   - Overall: ✓ READY / ✗ NOT READY

Remaining Risks:
- [List any risks or issues that need attention]

Suggested Commit Message:
"[type]: [description]"

Next Steps:
- [What to do next, if anything]
```

## Example Usage

**User request**: "Add a debt capacity calculator to the dashboard"

**Workflow**:
1. Architect plans: Identifies Dashboard.tsx, creates DebtCapacityCard component, adds calculation service
2. Engineer implements: Creates component, integrates into dashboard, adds types
3. Reviewer fixes: Finds missing useEffect dependency, fixes TypeScript error
4. QA verifies: Confirms lint passes, build succeeds, no secrets detected

**Final output**: Summary with all changes, verification results, and suggested commit message

## Principles

- **Sequential execution**: Each agent builds on the previous agent's work
- **Focused scope**: Keep changes minimal and targeted
- **Verification at each step**: Lint and build after implementation and review
- **Clear communication**: Report progress and findings at each stage
- **Release readiness**: Ensure code is ready to commit before finishing
