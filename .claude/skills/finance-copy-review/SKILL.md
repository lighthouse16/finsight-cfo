---
name: Finance Copy Review
description: Scan visible UI copy for risky finance/credit/lending language and suggest bank-review-safe alternatives
context: fork
allowed-tools: Read, Glob, Grep, Edit
---

# Finance Copy Review

Scan visible UI text for risky finance, credit, and lending language. Replace with bank-review-safe alternatives.

## When to Use

Use this skill to verify that visible UI copy is safe for bank/RM review:
- Before committing UI changes
- After adding new features with finance-related text
- When preparing for stakeholder review
- To audit existing UI copy

## Risky Language to Avoid

### Approval/Decision Language
- "approved", "guaranteed", "eligible", "qualified"
- "AI decided", "automatic approval", "final decision"
- "you will receive", "you are approved"

### Risk/Safety Language
- "safe", "no risk", "risk-free", "guaranteed returns"
- "certain outcome", "zero risk", "completely safe"

### Overconfident Lending Language
- "loan approved", "credit granted", "you qualify for"
- "instant approval", "pre-approved"

### Debug/Internal Language
- "demo", "mock", "synthetic", "dataset"
- "debug", "internal", "test data", "placeholder"

## Safe Alternatives

### Indicative Language
- "indicative assessment", "preliminary view"
- "based on available records", "appears suitable"
- "initial analysis suggests"

### Review-Required Language
- "for RM review", "subject to bank policy"
- "pending verification", "requires review"
- "subject to approval"

### Workspace/Tool Language
- "application workspace", "review-ready"
- "available records", "data summary"
- "analysis tool"

### Conditional Language
- "may be suitable", "could indicate"
- "subject to", "depending on", "if verified"

## Search Strategy

### 1. Find UI Files
```bash
# Find component files
find src/components -name "*.tsx" -o -name "*.jsx"

# Find page files
find src/pages -name "*.tsx" -o -name "*.jsx"
# or
find app -name "page.tsx"
```

### 2. Search for Risky Words
```bash
# Approval language
grep -r "approved\|guaranteed\|eligible\|qualified" src/

# Risk language
grep -r "safe\|no risk\|risk-free\|guaranteed" src/

# Decision language
grep -r "AI decided\|automatic\|final decision" src/

# Debug language
grep -r "demo\|mock\|synthetic\|dataset\|debug" src/
```

### 3. Review Context
For each match:
- Read the file to understand context
- Determine if the word is in visible UI text (not code comments)
- Assess risk level (high, medium, low)
- Suggest safe alternative

### 4. Report Findings
List all risky language found with:
- File path and line number
- Original text
- Risk reason
- Suggested replacement

## Output Format

```
Finance Copy Review
===================

Files scanned: [count]
Issues found: [count]

HIGH RISK:
1. [File]:[line]
   Original: "[text]"
   Risk: [why it's risky]
   Replace with: "[safe alternative]"

MEDIUM RISK:
2. [File]:[line]
   Original: "[text]"
   Risk: [why it's risky]
   Replace with: "[safe alternative]"

LOW RISK:
3. [File]:[line]
   Original: "[text]"
   Risk: [why it's risky]
   Replace with: "[safe alternative]"

Summary:
- [count] approval/decision language issues
- [count] risk/safety language issues
- [count] debug/internal language issues

Recommended Actions:
1. Fix high-risk issues immediately
2. Review medium-risk issues with team
3. Consider fixing low-risk issues for polish

Safe to proceed: ✓ Yes / ✗ No (if high-risk issues found)
```

## Example Report

```
Finance Copy Review
===================

Files scanned: 12
Issues found: 4

HIGH RISK:
1. src/pages/Dashboard.tsx:45
   Original: "Your loan has been approved for $50,000"
   Risk: Implies final approval decision
   Replace with: "Indicative debt capacity: $50,000 (subject to RM review)"

2. src/components/CreditScore.tsx:23
   Original: "You're eligible for this loan"
   Risk: Overconfident eligibility claim
   Replace with: "Based on available records, appears suitable for review"

MEDIUM RISK:
3. src/components/RiskAssessment.tsx:67
   Original: "This investment is safe"
   Risk: Guarantees safety/no risk
   Replace with: "Analysis based on available records"

LOW RISK:
4. src/components/DataTable.tsx:12
   Original: "Demo data shown below"
   Risk: Exposes internal/debug language
   Replace with: "Sample analysis shown below"

Summary:
- 2 approval/decision language issues
- 1 risk/safety language issue
- 1 debug/internal language issue

Recommended Actions:
1. Fix Dashboard.tsx and CreditScore.tsx immediately (high risk)
2. Review RiskAssessment.tsx wording with team
3. Update DataTable.tsx for polish

Safe to proceed: ✗ No (2 high-risk issues must be fixed)
```

## Principles

- **Bank-review-safe**: All wording must be suitable for RM/bank review
- **Preserve meaning**: Keep intent while reducing risk
- **Context matters**: Consider where text appears (heading vs help text)
- **Consistent tone**: Maintain professional fintech voice
- **No false positives**: Only flag visible UI text, not code comments
