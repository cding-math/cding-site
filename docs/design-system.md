# Approved design system: cding.me

Approved and revised on 2026-10-27. These rules govern the production homepage. The sibling
`name-reveal-demo/` retains the exploratory prototypes; it is not deployed.

## Composition

The vertical name occupies an annotation column within the page composition.
The English heading, biography, section headings, publication numbers, and
contact block share one main left edge. The photograph shares the main right
edge. The Chinese name is a quiet, optional personal detail: hidden by default
at every width, revealed through hover, keyboard focus or tap. Viewport width
controls placement; input method controls interaction. A narrow desktop window
uses the right-hand placement with hover, while a wide touchscreen uses the
left annotation with tap.

Desktop, at the maximum width:

| Element | Width |
| --- | ---: |
| Outer inset | 24 px |
| Annotation column | 24 px |
| Column gutter | 24 px |
| Main content | 672 px |
| Outer inset | 24 px |
| Total | 768 px |

The biography divides the main content into 432 px of text, a 40 px gutter, and
a 200 px photograph. These dimensions all use an 8 px spacing unit.

## Vertical rhythm

- Desktop top inset: 64 px. Mobile top inset: 32 px.
- English heading: 36/48 px desktop; 32/40 px mobile.
- Chinese: three upright 24 px cells in both layouts.
  Fixed cells avoid the font's oversized native vertical advance.
- Both layouts: the three cells fill the full 72 px heading height. The English
  line is explicitly centered beside the entire Chinese column, with no top
  offset or dependence on a button's implicit content alignment.
- Heading-to-intro clearance is always 24 px, on both layouts and in every
  visibility state. The desktop introduction therefore starts at 160 px;
  the mobile portrait starts at 128 px.
- Body text: 17/28 px. Paragraph gap: 16 px. Publication-row gap: 24 px.
- Publication titles: 17/28 px, Inter weight 550. This softens the former bold
  700 without removing the distinction from coauthors and links. The existing
  variable font supplies 550 with no extra download. Mathematical symbols keep
  KaTeX's regular weight and native shapes; do not force synthetic bold math.
- Major section gap: 64 px desktop; 48 px mobile.

## Responsive behavior

Below 800 px there is insufficient room for a separate annotation column. The
name moves to a fixed right-hand column inside the heading, with at least 24 px
between it and the English text (16 px on screens up to 340 px wide). This aligns
its right edge with the page grid. The Chinese glyphs are 20% larger than the
previous compact version: 24 px instead of 20 px, occupying the full heading row.

At 800 px and wider, Chinese occupies the existing left annotation column;
below 800 px it appears on the English name's right, inside the heading grid.
No hover/pointer media query selects placement or makes the name persistent.

All screen widths use the same native button. Mouse entry or keyboard focus
reveals Chinese; activation toggles visibility. A touch tap reveals it and a
second tap dismisses it. Tapping elsewhere, Escape or leaving keyboard focus
also dismisses it. Mouse exit hides an unselected hover reveal. The 220 ms fade
and 3 px entrance motion remain restrained; reduced motion removes the transition.

The name's space is always reserved. Resizing changes CSS placement without
explicitly resetting the reveal state; ordinary pointer/focus events still apply.
No visible hint is added. Screen readers receive a stable bilingual name and
hidden interaction instructions; the focus outline is for keyboard navigation.
The plain `.name-static` representation is now print-only, where both names
remain visible without requiring interaction.

At 600 px and below, the portrait sits above the biography and fills the same
content width. The heading, portrait, biography, and later sections all share
24 px outer insets. A 32 px gap separates portrait and biography.

## Appearance and implementation

Keep the original light/dark palettes, selected automatically from the system.
There is no production theme toggle, grid overlay, preview route, or query flag.

Canonical implementation:

- `assets/css/style.css`: spacing tokens, grid, typography, breakpoints, themes.
- `layouts/index.html` and `layouts/partials/name-text.html`: accessible markup.
- `assets/js/site.js`: one hover/focus/tap state machine, independent of width.
- `docs/font-build.md`: approved glyph provenance and deterministic subsetting.

The production build fingerprints its CSS, JavaScript, and font resources. The
font subset must retain the chosen outlines; do not substitute a similar font.
Adjust named tokens and shared alignments rather than isolated pixel offsets.

Reference captures: `design-reference-desktop.png` and
`design-reference-mobile.png` in this directory. They are repository guidance,
not public website assets. Both captures show keyboard reveal, with Chinese
placed on opposite sides according to width. Chinese starts hidden on both.
Older captures in the performance audit preserve their original tested revision.

## Phone review presets

Portrait layout viewports from the [official Playwright device catalog](https://github.com/microsoft/playwright/blob/main/packages/isomorphic/deviceDescriptorsSource.json),
retrieved 2026-10-27:

| Phone | CSS viewport |
| --- | --- |
| iPhone 17 Pro | 402 × 681 |
| iPhone 17 Pro Max | 440 × 763 |
| Google Pixel 8 | 412 × 839 |
| Google Pixel 9 Pro | 427 × 876 |
| Samsung Galaxy S24 | 360 × 780 |
| Samsung Galaxy A55 | 480 × 1040 |

These reproduce layout sizes, not browser engines, operating-system text scaling,
device pixel density, or browser chrome. The local prototype retains these presets for design review; production uses
responsive CSS rather than device detection.

## Browser verification

The original geometry was reviewed at desktop width and all six phone presets,
including light/dark appearance. The later interaction revision preserves those
spacing tokens. It was checked locally at 1280 px and 402 px: hidden/revealed
states keep the heading at 72 px and the introduction at document y=160/128 px,
with no horizontal overflow. Keyboard reveal and Escape work at both widths;
resizing a revealed heading moves the annotation while retaining its state.

Mouse entry/exit, touch first/second tap, outside dismissal, keyboard and pointer
cancellation sequences were also checked against the actual event handlers.
These checks do not constitute testing on a physical phone. The mobile
accessibility tree now exposes an operable toggle button rather than static text.

## Loading stability

The final typography and geometry above remain authoritative. A preloaded Inter
core carries identical selected outlines and default shaping; larger coverage
loads only when needed. Body-only local fallback metrics preserve the biography
while Inter downloads. These are loading behavior, not a new design variant.
Mathematics is pre-rendered so titles do not change from raw TeX after paint.
See `performance.md` and `math-rendering.md` before altering these mechanisms.
