# Critical Inter font subset

`assets/fonts/inter-core.woff2` is the early-loading face for ordinary English
text. It retains the approved Inter Variable 4.001 outlines, variable axes,
metrics, and default shaping while avoiding the full broad-Latin payload.
The internal family is **Changying Core Sans**; the CSS family remains the
website's `Site Sans` alias.

## Artifact and provenance

- Source: unchanged `static/fonts/InterVariable.woff2`.
- Upstream project: <https://github.com/rsms/inter>.
- Embedded source version: `Version 4.001;git-9221beed3`.
- Source SHA-256: `693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3`.
- Output: `assets/fonts/inter-core.woff2`, **38,136 bytes** (37.24 KiB).
- Output SHA-256: `483f80f3caceff6a268b6660b1fba3015b6fcb6d1555c076ed2a0a6ec94cd13f`.
- Copyright and SIL Open Font License 1.1 metadata remain unchanged. The
  accompanying license is `static/fonts/Inter-OFL.txt`; see
  `docs/inter-font-build.md` for its official source and verification.

Primary family/full/PostScript names and applicable named-instance names are
renamed to identify the derivative separately. The original authors and license
are retained. Compared with the 38,072-byte experiment, this artifact changes
the subset naming metadata, not the selected glyphs or their shaping.

## Coverage and shaping policy

There are **105 encoded codepoints** and **153 glyphs**, including substitutions
and components. Exact encoded coverage:

```text
U+0000          Null
U+0020–007E     Printable ASCII
U+00A0          Non-breaking space
U+00A9          Copyright
U+2013–2014     En/em dashes
U+2018–2019     Single quotation marks
U+201C–201D     Double quotation marks
U+2026          Ellipsis
```

The build requests the default shaping feature set
`calt, ccmp, clig, kern, liga, locl, mark, mkmk, rlig, rvrn`.
After removing rules irrelevant to this character domain, the retained feature
tags are **GSUB `calt`** and **GPOS `kern`**. All applicable glyphs and lookups
remain. Optional stylistic sets, fractions, and character variants are not part
of this critical face; the approved design does not enable them.

Both variable axes remain intact:

| Axis | Minimum | Default | Maximum |
| --- | ---: | ---: | ---: |
| Optical size (`opsz`) | 14 | 14 | 32 |
| Weight (`wght`) | 100 | 400 | 900 |

The broad Latin subset remains available for non-core characters, and the
original full Inter covers other scripts. Unicode ranges must partition these
sources so a cold visit does not download the broad face as an interim fallback.
Preload the core face, not the broad one. The Chinese name has its own independent
2,572-byte Zhuque subset; KaTeX owns its mathematical fonts.

Core CSS range:

```css
unicode-range: U+0000-007F, U+00A0, U+00A9, U+2013-2014,
  U+2018-2019, U+201C-201D, U+2026;
```

Broad-Latin range after removing the core range:

```css
unicode-range: U+0080-009F, U+00A1-00A8, U+00AA-024F, U+0300-036F,
  U+1E00-1EFF, U+2000-2012, U+2015-2017, U+201A-201B, U+201E-2025,
  U+2027-206F, U+20A0-20CF, U+2113, U+2122, U+2190-2199, U+2212,
  U+FEFF, U+FFFD;
```

These disjoint descriptors preserve the former broad face's declared coverage.
Future non-core text may trigger its additional download. New text, mixed-face
shaping, or typography/feature changes require browser retesting; do not assume
today's performance and shaping evidence covers new characters or stylistic sets.

## Regeneration

This is a **maintainer-only** operation. Cloudflare/Hugo consumes the checked-in
WOFF2 and must not install Python packages, fetch upstream fonts, or regenerate
the subset during deployment.

Use the existing pinned `scripts/requirements-fonts.txt` environment:
FontTools **4.60.2**, Brotli **1.2.0**, plus a local HarfBuzz shared library.
The script reuses the audited HarfBuzz wrapper in `scripts/subset_inter_font.py`.
From the repository root:

```sh
python3 scripts/subset_inter_core.py
```

The source defaults to `static/fonts/InterVariable.woff2`, output to
`assets/fonts/inter-core.woff2`, and sample HTML to `public/index.html`. Supplied
paths allow an isolated comparison build or a different generated homepage:

```sh
python3 scripts/subset_inter_core.py /path/to/InterVariable.woff2 \
  --output /tmp/inter-core-check.woff2 \
  --html /path/to/generated/index.html
```

If HarfBuzz is not found automatically, add `--harfbuzz-library /path/to/library`.
No font is installed into the operating system. The script enforces the approved
source checksum and pinned Python versions, and produces the same artifact
regardless of which supported HTML sample is supplied.

## Verification

The script checks the decoded output, not merely the pre-compression object:

1. Exact 105-codepoint coverage and 153-glyph count.
2. Required shaping/variation tables and the applicable `calt`/`kern` feature tags.
3. Byte-identical `fvar`, `avar`, `STAT`, and `MVAR`, plus identical variation
   tuples for every retained glyph.
4. **918 outline/advance comparisons:** every retained glyph at weights
   400/500/600, each at optical size 14 and 32. Units per em and line metrics match.
5. Current-page and generic text shaping at weights 400/500/600/700 and optical
   sizes 14/15/17/20/24/32, under default, `calt`, and `kern` settings. Glyph names,
   clusters, advances, and offsets must match the source exactly.
6. Original copyright/license metadata, renamed primary/instance names, a
   payload below 40 KB, and byte-identical independent builds.

Initial verification used **HarfBuzz 11.2.1**, with 60 text specimens and **4,320
shaping comparisons**. Counts can change with the homepage text or pre-rendered
math, but the font output and geometry checks remain deterministic.

HTML sampling excludes `.name-chinese`, scripts, styles, SVG/MathML, and nested
KaTeX subtrees. It also strips raw TeX dollar-delimited spans from older generated
HTML. Math uses separate fonts and must not be mistaken for missing core Latin
coverage. A parser fixture checks both raw TeX and nested pre-rendered math.
Non-core ordinary text is reported instead of silently adding glyphs to this
fixed-coverage subset; it requires broad-fallback and layout/performance review.
An additional fixture generated with the project's actual KaTeX 0.19.1 produced
the same font bytes, skipped the rendered mathematical symbols, and correctly
reported a deliberately added non-core `é` as requiring the broad fallback.

Font fidelity does not by itself establish loading performance. Use cold-cache,
throttled browser measurements and filmstrips to verify request selection,
font completion, and absence of paragraph/list reflow after integration.
