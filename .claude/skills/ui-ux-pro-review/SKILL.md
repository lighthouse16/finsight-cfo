---
name: UI/UX Pro Review
description: Deep UX quality review - IA, layout grammar, interaction states, accessibility, responsive behavior
context: fork
allowed-tools: Read, Glob, Grep
---

# UI/UX Pro Review

Deep UX quality review inspired by professional fintech design standards.

## When to Use

Use this skill for comprehensive UX evaluation:
- Before major releases
- After significant UI changes
- When product feels "off" but you can't pinpoint why
- To audit overall UX quality

## Review Dimensions

### 1. Information Architecture (IA)
- **Page purpose**: Each page has a clear, singular purpose
- **Navigation**: Logical hierarchy and clear paths
- **Content organization**: Related content grouped logically
- **Mental model**: Structure matches user expectations

### 2. Layout Grammar
- **Grid system**: Consistent column structure
- **Alignment**: Elements align to a clear grid
- **Spacing rhythm**: Consistent spacing scale (4px, 8px, 16px, 24px, 32px)
- **Visual weight**: Important elements have more visual weight

### 3. Typography
- **Hierarchy**: Clear H1 → H2 → H3 → body progression
- **Scale**: Appropriate font sizes (12px to 32px+)
- **Weight**: Strategic use of font weights (400, 500, 600, 700)
- **Line height**: Readable leading (1.5 for body, 1.2 for headings)
- **Measure**: Line length 45-75 characters for readability

### 4. Color & Contrast
- **Contrast ratios**: WCAG AA minimum (4.5:1 for text)
- **Color hierarchy**: Primary, secondary, tertiary colors clear
- **Semantic colors**: Success, warning, error, info consistent
- **Neutral scale**: Gray scale with clear steps

### 5. Component Design
- **Consistency**: Similar components look similar
- **Density**: Appropriate information density
- **Affordance**: Interactive elements look clickable
- **Feedback**: Clear hover, focus, active states

### 6. Interaction States
- **Default**: Clear initial state
- **Hover**: Visual feedback on hover
- **Focus**: Keyboard focus visible
- **Active**: Click/tap feedback
- **Disabled**: Clearly non-interactive
- **Loading**: Progress indication
- **Error**: Clear error messaging
- **Success**: Confirmation feedback

### 7. Empty States
- **No data**: Helpful message when no data available
- **First use**: Guidance for new users
- **Error state**: Clear error explanation and recovery
- **Loading state**: Skeleton loaders or spinners

### 8. Responsive Behavior
- **Mobile (< 640px)**: Single column, touch-friendly
- **Tablet (640px - 1024px)**: Optimized for medium screens
- **Desktop (> 1024px)**: Utilizes space effectively
- **Breakpoints**: Smooth transitions between sizes

### 9. Accessibility
- **Semantic HTML**: Proper heading levels, landmarks
- **ARIA labels**: Screen reader support
- **Keyboard navigation**: Tab order logical
- **Color contrast**: WCAG AA compliance
- **Focus indicators**: Visible focus states
- **Alt text**: Images have descriptive alt text

### 10. Performance & Polish
- **Load time**: Fast initial render
- **Animations**: Smooth, purposeful transitions
- **Micro-interactions**: Delightful details
- **Error handling**: Graceful degradation
- **Consistency**: Cohesive design language

## Review Process

### 1. Inspect Files
```bash
# Find UI files
find src/components -name "*.tsx"
find src/pages -name "*.tsx"
# or
find app -name "page.tsx"

# Find styles
find . -name "*.css" -o -name "tailwind.config.*"
```

### 2. Evaluate Each Dimension
For each dimension:
- Read relevant files
- Assess against standards
- Identify issues
- Rate 1-10

### 3. Prioritize Issues
- **Critical**: Breaks functionality or accessibility
- **High**: Significantly impacts UX
- **Medium**: Noticeable but not blocking
- **Low**: Polish and refinement

### 4. Provide Recommendations
- Specific file and line references
- Concrete fixes
- Priority order

## Output Format

```
UI/UX Pro Review - Finsight CFO
================================

Overall UX Score: [X]/10

1. Information Architecture: [X]/10
   - [Findings]
   - Issues: [list]

2. Layout Grammar: [X]/10
   - [Findings]
   - Issues: [list]

3. Typography: [X]/10
   - [Findings]
   - Issues: [list]

4. Color & Contrast: [X]/10
   - [Findings]
   - Issues: [list]

5. Component Design: [X]/10
   - [Findings]
   - Issues: [list]

6. Interaction States: [X]/10
   - [Findings]
   - Issues: [list]

7. Empty States: [X]/10
   - [Findings]
   - Issues: [list]

8. Responsive Behavior: [X]/10
   - [Findings]
   - Issues: [list]

9. Accessibility: [X]/10
   - [Findings]
   - Issues: [list]

10. Performance & Polish: [X]/10
    - [Findings]
    - Issues: [list]

Critical Issues (Fix Immediately):
1. [Issue] - [File]:[line]
2. [Issue] - [File]:[line]

High Priority Issues:
1. [Issue] - [File]:[line]
2. [Issue] - [File]:[line]

Medium Priority Issues:
1. [Issue] - [File]:[line]
2. [Issue] - [File]:[line]

Low Priority Issues:
1. [Issue] - [File]:[line]

Concrete Fixes:
1. [Specific change] in [file]
   - Before: [code]
   - After: [code]

2. [Specific change] in [file]
   - Before: [code]
   - After: [code]

Implementation Priority:
1. [Fix with highest impact]
2. [Fix with second highest impact]
3. [Fix with third highest impact]

Next Steps:
- [Recommended action 1]
- [Recommended action 2]
- [Recommended action 3]
```

## Principles

- **Banking-grade quality**: Professional, trustworthy, enterprise fintech
- **User-centered**: Design serves user needs, not aesthetics
- **Accessible by default**: WCAG AA minimum
- **Responsive always**: Works on all screen sizes
- **Consistent**: Cohesive design language throughout
- **Performant**: Fast and smooth interactions
