# Softform Financial Intelligence UI

## 1. System name

**Softform Financial Intelligence UI**

## 2. Style definition

A light-first tactile fintech interface system combining frosted surfaces, soft elevation, rounded dashboard architecture, atmospheric gradients, and precise financial data hierarchy.

## 3. Design philosophy

Softform Financial Intelligence UI fits FinSight CFO because the product must feel calm, credible, and decision-grade while still communicating intelligence and modernity. SME finance leaders need clarity and confidence, not a loud AI interface or crypto-like dashboard theatre.

The system balances elegance and credibility by pairing luminous soft surfaces with deep navy anchors. Frosted panels and rounded shells make the interface approachable, while precise type hierarchy, tabular numbers, and restrained signal colors keep financial information readable and trustworthy.

Gradients are used as atmospheric light, not as paint. They should feel like soft illumination behind glass: mist green, icy blue, warm cream, sage, muted aqua, and amber glow. They should not dominate text, flood cards, or turn the product into a saturated startup template.

Deep navy anchors the product because financial decisions require seriousness, contrast, and institutional credibility. Navy is used for primary calls to action, important contrast cards, headers, and high-priority text.

Financial information must stay readable at all times. Frosted surfaces cannot reduce contrast, decorative motion cannot obscure values, and signal colors cannot imply certainty the product does not have.

## 4. Core principles

- **Soft surfaces, sharp financial intelligence**: tactile cards can be soft, but hierarchy and data must remain exact.
- **Use gradients like light, not paint**: gradients illuminate surfaces; they do not become loud color blocks.
- **Luminous, not loud**: the interface should glow softly rather than shout.
- **Tactile depth over hard borders**: use inset highlights, soft shadows, and glass edges instead of harsh outlines.
- **Deep navy anchors credibility**: primary actions and contrast panels should use navy rather than electric blue.
- **Teal is a signal, not a background flood**: teal/aqua marks status, chart paths, icons, and small accents only.
- **Amber is warmth, not a warning unless explicitly used**: amber can add atmospheric light or caution warmth, but should not become a dominant brand color.
- **Data stays precise and readable**: values, labels, and chart states must maintain strong contrast.
- **Motion feels physical, not decorative**: hover states lift softly as if made of material.
- **No fake finance certainty**: visual emphasis must not imply guarantees or invented precision.

## 5. Color system

```css
--mist-50: #f4faf7;
--mist-100: #e8f4f1;
--ice-100: #e7f0f4;
--warm-cream: #f8f2df;
--soft-sage: #c9ddd7;

--navy-950: #08111f;
--navy-900: #0d1726;
--navy-800: #132337;
--navy-700: #1c324b;

--text-primary: #111827;
--text-secondary: #526173;
--text-muted: #8794a3;

--aqua-300: #85d9ce;
--teal-500: #20a99a;
--deep-teal: #0e615b;
--emerald-soft: #38b883;

--amber-200: #f6df9d;
--amber-300: #f1cf78;
--amber-500: #d9a83f;

--surface-white: rgba(255,255,255,0.72);
--surface-mint: rgba(234,247,244,0.72);
--surface-ice: rgba(231,240,244,0.72);
--surface-navy: rgba(13,23,38,0.92);
```

### Usage rules

- Primary CTA uses deep navy, not electric blue.
- Secondary buttons use frosted white.
- Headline is mostly navy with restrained teal emphasis.
- Teal/aqua only for signal accents.
- Amber only for atmospheric warmth or caution.
- Hard cyan/teal borders are forbidden.
- Saturated green headline text is forbidden.
- Pure blue SaaS gradients are forbidden.

## 6. Gradient system

### Page background

```css
radial-gradient(circle at 12% 82%, rgba(241, 207, 120, 0.42), transparent 32%),
radial-gradient(circle at 82% 18%, rgba(133, 217, 206, 0.34), transparent 34%),
radial-gradient(circle at 72% 78%, rgba(28, 50, 75, 0.10), transparent 36%),
linear-gradient(135deg, #f4faf7 0%, #e7f0f4 48%, #f8f2df 100%)
```

### Hero/product cockpit surface

```css
radial-gradient(circle at 82% 18%, rgba(133, 217, 206, 0.28), transparent 38%),
radial-gradient(circle at 18% 88%, rgba(246, 223, 157, 0.28), transparent 34%),
linear-gradient(145deg, rgba(255,255,255,0.72), rgba(232,244,241,0.68))
```

### Deep navy contrast card

```css
radial-gradient(circle at 88% 12%, rgba(32, 169, 154, 0.22), transparent 32%),
linear-gradient(145deg, #0d1726 0%, #132337 52%, #1c324b 100%)
```

## 7. Surface and material system

### Soft shell

Large rounded container used for major sections, hero cockpits, and grouped product previews. It uses atmospheric gradients, wide radius, soft outer depth, and white inset highlights.

### Frosted card

Translucent white/mint/ice card for regular content. Text must remain readable against the glass.

### Elevated panel

A frosted card with stronger shadow and inset highlight for important modules.

### Pressed pill

Capsule controls, badges, navigation items, and secondary buttons with soft inner highlights and restrained borders.

### Navy contrast card

Deep navy surface for primary action cards, high-priority recommendations, and strong CTAs. It uses subtle teal light, not blue glow.

### Ambient glow layer

Low-opacity radial gradient behind sections or cards. It must not be interactive or reduce contrast.

### Example surface treatment

```css
background:
  linear-gradient(145deg, rgba(255,255,255,0.70), rgba(234,247,244,0.62));
border: 1px solid rgba(255,255,255,0.72);
box-shadow:
  0 18px 50px rgba(8, 17, 31, 0.16),
  0 8px 22px rgba(8, 17, 31, 0.08),
  inset 0 1px 0 rgba(255, 255, 255, 0.76);
```

## 8. Radius system

- Small controls: `14-18px`
- Pills: `999px`
- Cards: `26-36px`
- Large panels: `40-56px`
- Hero shells: `48-64px`

## 9. Shadow/elevation system

- **Shadow color rule**: all framed background shadows use deep navy only: `rgba(8, 17, 31, ...)`, from `--navy-950: #08111f`.
- **Do not use background-matching shadows**: avoid mist, ice, cream, or pale green shadows because they blend into the page atmosphere.
- **Base card**: soft deep-navy shadow, low vertical offset, no black harshness.
- **Floating panel**: larger deep-navy blur and a slight y-offset for dashboard modules.
- **Hero shell**: broad deep-navy shadow with strong inset highlight.
- **Pressed surface**: subtle deep-navy outer shadow plus inner shadow/highlight for pills and controls.
- **Deep navy card**: stronger navy-tinted shadow for dark contrast surfaces.
- **Hover lift**: `translateY(-3px)` to `translateY(-6px)`, shadow increases softly.

Current implementation tokens:

```css
--shadow-base-card:
  0 18px 50px rgba(8, 17, 31, 0.16),
  0 8px 22px rgba(8, 17, 31, 0.08),
  inset 0 1px 0 rgba(255,255,255,0.76);

--shadow-floating-panel:
  0 28px 86px rgba(8, 17, 31, 0.22),
  0 12px 30px rgba(8, 17, 31, 0.10),
  inset 0 1px 0 rgba(255,255,255,0.82),
  inset 0 -1px 0 rgba(20,40,55,0.08);

--shadow-hero-shell:
  0 38px 120px rgba(8, 17, 31, 0.26),
  0 16px 44px rgba(8, 17, 31, 0.12),
  inset 0 1px 0 rgba(255,255,255,0.84);

--shadow-navy-card:
  0 28px 76px rgba(8,17,31,0.34),
  0 10px 28px rgba(8,17,31,0.14),
  inset 0 1px 0 rgba(255,255,255,0.12);

--shadow-pressed:
  0 12px 32px rgba(8,17,31,0.14),
  0 4px 14px rgba(8,17,31,0.07),
  inset 0 1px 0 rgba(255,255,255,0.84),
  inset 0 -1px 0 rgba(20,40,55,0.07);
```

## 10. Typography system

Do not change text content.

- **Large editorial headline**: high weight, tight but readable tracking, deep navy default.
- **Navy default text**: headings and important labels use navy.
- **Restrained teal emphasis**: only a few emphasized words, never full rainbow gradients.
- **Uppercase micro labels**: small labels use letter spacing, muted graphite/sage tones.
- **Tabular financial numbers**: financial values and percentages use tabular numerals.
- **Readable body copy**: body copy uses graphite secondary text with generous line-height.

## 11. Component style rules

### Header / command bar

- Floating frosted white/ice command bar.
- Large pill radius.
- Inner highlight and subtle shadow.
- Navy text and restrained hover states.
- Deep navy CTA.

### CTA buttons

- Primary: deep navy gradient, white text, tactile shadow, slight hover lift.
- Secondary: frosted white, navy text, subtle inner highlight.
- No electric-blue button fills.

### Hero cockpit

- Frosted mist/ice softform material.
- White border and inset highlight.
- Muted teal chart/signal accents.
- Navy contrast card for main action tile.
- Preserve existing layer hover interaction when present.

### Product preview

- Rounded dashboard architecture.
- Frosted panels with soft elevation.
- Data hierarchy remains clear.

### Cards

- Large rounded corners.
- Translucent surfaces.
- Soft shadows and inner highlights.
- No harsh outlines.

### Module tiles

- Use tactile elevation and restrained accent icons.
- Avoid saturated full-card color floods.

### Explainability/source trail

- Use precise hierarchy, readable labels, and subtle connector lines.
- Avoid neon graph styling.

### Waitlist panel

- Use a soft shell with navy CTA.
- Inputs are frosted/white with clear focus-visible states.

### Footer

- Keep disclaimer content unchanged.
- Use deep navy or mist surface with readable contrast.

## 12. Motion system

- Soft hover lift only where interaction benefits from physicality.
- Small floating movement may be used for ambient visuals.
- Smooth reveal animations are acceptable when already present.
- No aggressive motion, spin, neon pulse, or overanimated WebGL.
- Reduced motion fallback must preserve usability.

## 13. Responsive system

- Desktop can carry richer atmosphere and layered surfaces.
- Tablet layouts simplify spacing and reduce excessive depth.
- Mobile stacks tactile cards vertically with no horizontal overflow.
- Hero cockpits and dashboard previews must scale down cleanly.

## 14. Accessibility

- Maintain adequate contrast on frosted surfaces.
- Use visible focus states.
- Keep text readable and avoid low-contrast glass text.
- Do not make understanding dependent on motion.
- Preserve semantic structure and existing user flows.

## 15. Anti-patterns

- Electric blue CTA.
- Saturated green headline.
- Harsh teal outlines.
- Crypto dashboard styling.
- Purple AI gradients.
- Hard rectangular SaaS cards.
- Excessive blur.
- Low contrast frosted text.
- Overanimated WebGL.
- Fake financial certainty.

## 16. Platform Shell Patterns

The platform shell provides the persistent visual framework and navigation container for the FinSight CFO workspace.

- **Floating Softform Sidebar**: The sidebar is styled as a floating frosted container with soft shadows, resting elegantly on the page background.
- **Collapsible Desktop Sidebar**: Users can collapse the sidebar to maximize screen workspace.
- **Icon-Only Collapsed State**: When collapsed, the sidebar transitions to a narrow, space-efficient icon-only bar showing only the section/page icons.
- **Grouped Navigation Sections**: Navigation items are logically grouped (e.g., Core Workspace, Market intelligence) to present structured access routes.
- **Mobile Drawer Behavior**: On mobile screens, the sidebar transitions into a sliding drawer overlay controlled via a responsive menu button, ensuring a native-like mobile experience.
- **Subtle Scrollbar Behavior**: Scrollbars in sidebars and scrollable areas must be hidden or extremely soft by default, and only become visible when explicitly hovered, scrolled, or focused.
- **Top Command Bar**: The top command bar acts strictly as a workspace control surface (e.g., profile settings, workspace switching, or global controls) and should remain uncluttered.
- **No Preview/Demo Badges**: No raw "preview" or "demo" badges should be displayed in the core product shell to preserve a premium, production-ready feel.

## 17. Page Header Patterns

The page header establishes the visual context and functional entry point for each module.

- **Strong, Concise Titles**: Page titles should be clear, prominent, and concise.
- **Minimize Subtitle Redundancy**: Avoid displaying long, static visible subtitles when the page context and active tab/workspace are already clear.
- **Contextual Info Tooltips**: Instead of cluttering the page with permanent descriptive text, move detailed contextual explanations into a small info tooltip next to the title.
- **Hover and Focus Accessibility**: The info tooltip must support both mouse hover and keyboard focus states to ensure complete accessibility.
- **Responsive Action Alignment**: Primary action buttons align to the right on desktop, and automatically wrap or stack vertically on mobile screens to prevent overflow.

## 18. Market Watch UI Patterns

Market Watch serves as the external market pressure layer, providing SME decision-makers with critical signals affecting funding, lending, and cashflow.

- **Purpose**: Tracks macroeconomic and sector-specific indicators to inform SME funding decisions.
- **Finalized Tabs**:
  - **Market Pulse**: Overview of broad market indicators.
  - **Rates & Liquidity**: Bank rates, interbank liquidity, and central bank movements.
  - **FX & GBA**: Volatility signals and currency trends in global markets and the Greater Bay Area.
  - **Sector Benchmarks**: Industry-specific SME credit and growth indicators.
  - **Commodities**: Material costs and resource pressure signals.
  - **Stress Signals**: Financial distress metrics and tightening credit signals.
- **Careful & Exact Language**: Utilize precise, realistic labeling. Use terms like `context signal`, `source-fresh`, `workspace`, and `requires company data`.
- **No Realtime Claims**: Never claim data is "realtime" unless a live, direct backend source is connected and verified.
- **No Deceptive Finance Metaphors**: Do not show simulated "approval probability," "credit score," or guarantee metrics which imply certainty the product does not possess.

## 19. Executive Signal Card Pattern

Used for high-level module summaries (e.g., the top summary cards in the Market Watch dashboard).

- **Strict Card Anatomy**:
  - **Top Row**: Contains the label (e.g., "Funding Conditions") and a soft, desaturated severity chip (e.g., "Caution").
  - **Main Status Row**: Prominently displays the full status text (e.g., "Selective"). The status text must **never be ellipsized or truncated**.
  - **Implication Line**: A single, concise sentence explaining what this status means for the user's business.
  - **Subtle Visual Motif**: A highly integrated visual cue (such as a segmented signal bar, upward trend sparkline, split/divergence line, or currency-pair badge) rendered below the text. The visual motif supports the status and must **never compete** with it.
  - **Footer**: Displays the source label and a freshness chip (e.g., "HKMA Rates • Daily").
- **Severity Chip Focus**: Severity chips function strictly as supporting metadata and should not serve as the primary visual focus of the card.

## 20. Chip/Badge Pattern

Chips provide lightweight metadata tagging with zero visual clutter.

- **Severity Chips**: Compact, soft labels representing system state: `caution`, `high`, `neutral`, and `positive`.
- **Freshness Chips**: Indicate update frequencies: `daily`, `monthly`, `delayed`, `workspace`, and `seed data`.
- **Source Status Chips**: Indicate integration readiness: `ready for connector`, `seed data`, `requires backend`, and `requires company data`.
- **Aesthetic Rules**: Chips must be soft, compact, highly readable, and desaturated (never using overly saturated or harsh primary colors).

## 21. Tooltip Pattern

Used for progressive disclosure of instructions and definitions.

- **Iconography**: Use a neutral info/help icon (such as a Lucide `Info` or `CircleHelp` icon), not warning or exclamation indicators.
- **Trigger**: The trigger must be a keyboard-accessible visual button element.
- **ARIA Compliance**: Must include an explicit `aria-label` or `aria-describedby` attribute to link the trigger to the tooltip content.
- **Interaction**: The tooltip container must display smoothly on both hover and focus, and hide on mouse leave or blur.
- **Styling**: Rendered as a frosted Softform surface (glassmorphic border, high blur, subtle shadow). Never rely on browser-default `title` attributes.

## 22. Market Data and Source Language

FinSight CFO prioritizes transparent source disclosure for all external market telemetry.

- **V1 Data Abstraction**: The initial implementation (V1) runs on localized seed data routed through a structured API abstraction layer (`marketWatchApi.ts`).
- **Data Integrity**: Future live or near-real-time data displays must clearly show the original publisher (source), a precise "as-of" timestamp, and an accurate freshness marker.
- **Accurate Wording**: Avoid calling data "live" or "real-time" unless verified. Instead, use phrases like `source-fresh` or `near-real-time` only when technically accurate.
- **Source & Freshness Microcopy**: Every individual card, module, or data point displaying external signals must expose visible source and freshness microcopy.
