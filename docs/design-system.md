# Approved design system: cding.me

Approved on 2026-10-27. These rules govern the production homepage. The sibling
`name-reveal-demo/` retains the exploratory prototypes; it is not deployed.

## Composition

The vertical name occupies an annotation column within the page composition.
The English heading, biography, section headings, publication numbers, and
contact block share one main left edge. The photograph shares the main right
edge. On wide, hover-capable screens the annotation appears on hover or keyboard
focus. Narrow layouts and touch devices show a persistent, noninteractive
bilingual heading.

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
- Major section gap: 64 px desktop; 48 px mobile.

## Responsive behavior

Below 800 px there is insufficient room for a separate annotation column. The
name moves to a fixed right-hand column inside the heading, with at least 24 px
between it and the English text (16 px on screens up to 340 px wide). This aligns
its right edge with the page grid. The Chinese glyphs are 20% larger than the
previous compact version: 24 px instead of 20 px, occupying the full heading row.

At 800 px and wider with a fine, hover-capable pointer, the name is a native
button that reveals Chinese on mouse entry or keyboard focus. Activation can
toggle it; Escape dismisses it. Its space remains reserved. On smaller layouts,
or devices without hover, CSS swaps it for plain bilingual text: no unneeded
button role, hidden action, or discoverability hint. Resizing resets transient
interaction state; both representations share the same typography partial.

At 600 px and below, the portrait sits above the biography and fills the same
content width. The heading, portrait, biography, and later sections all share
24 px outer insets. A 32 px gap separates portrait and biography.

## Appearance and implementation

Keep the original light/dark palettes, selected automatically from the system.
There is no production theme toggle, grid overlay, preview route, or query flag.

Canonical implementation:

- `assets/css/style.css`: spacing tokens, grid, typography, breakpoints, themes.
- `layouts/index.html` and `layouts/partials/name-text.html`: accessible markup.
- `assets/js/site.js`: desktop reveal; mobile remains ordinary heading text.
- `docs/font-build.md`: approved glyph provenance and deterministic subsetting.

The production build fingerprints its CSS, JavaScript, and font resources. The
font subset must retain the chosen outlines; do not substitute a similar font.
Adjust named tokens and shared alignments rather than isolated pixel offsets.

Reference captures: `design-reference-desktop.png` and
`design-reference-mobile.png` in this directory. They are repository guidance,
not public website assets. The desktop capture shows keyboard reveal; the mobile
capture shows the persistent heading.

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

The visible Chinese and English blocks have equal vertical centers in desktop
and all six phone presets. Each heading is 72 px high, followed by 24 px of clear
space, and none of the phone presets has horizontal overflow. Desktop mouse
entry/exit, keyboard focus, and Escape were exercised. The mobile accessibility
tree exposes the bilingual heading as text, without an inactive toggle control.
Light and dark appearances were visually inspected.
