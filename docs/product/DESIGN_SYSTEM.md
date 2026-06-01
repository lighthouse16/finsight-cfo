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
