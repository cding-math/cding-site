# Variable Latin font subset

The approved English typeface remains the existing **Inter Variable 4.001**
(`git-9221beed3`). `assets/fonts/inter-latin.woff2` is a smaller delivery of that
same font, with the internal family renamed **Changying Latin Sans**. The website
can use its own CSS alias, `Site Sans`. The original full Inter file remains
available as a fallback for scripts outside the Latin subset.

## Provenance and license

- Official project: <https://github.com/rsms/inter>.
- Input: the existing `static/fonts/InterVariable.woff2`, unchanged.
- Embedded version: `Version 4.001;git-9221beed3`.
- Input size: **352,240 bytes**.
- Input SHA-256: `693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3`.
- Official license: <https://github.com/rsms/inter/blob/master/LICENSE.txt>,
  retrieved 2026-10-27 and retained at `static/fonts/Inter-OFL.txt`.

The source's embedded copyright identifies **The Inter Project Authors** and its
embedded license specifies **SIL Open Font License 1.1**, matching that official
license. Copyright and license metadata are retained. Internal family/full/
PostScript names identify the subset separately, including any named-instance
names beginning with the original family name; this avoids relying on permission
to reuse an upstream reserved name for a derivative.

## Artifact and coverage

- File: `assets/fonts/inter-latin.woff2`.
- Size: **199,328 bytes** (194.66 KiB), **43.41% smaller** than the original.
- SHA-256: `5b0a8c4fbc73f3f5ac78c41b9f76874a86ed83e7e53f286e80209bc4048b08ef`.
- Encoded characters: **966**; glyphs including OpenType substitutions: **1,782**.

The subset retains all characters present in the input from these ranges:

```text
U+0000–024F   Basic Latin, Latin-1, Latin Extended A/B
U+0300–036F   Combining diacritics
U+1E00–1EFF   Latin Extended Additional
U+2000–206F   General punctuation
U+20A0–20CF   Currency symbols
U+2113       Script small l
U+2122       Trademark
U+2190–2199  Arrows
U+2212       Minus
U+FEFF       Zero-width no-break space, if present
U+FFFD       Replacement character, if present
```

The matching CSS `unicode-range` is:

```css
unicode-range: U+0000-024F, U+0300-036F, U+1E00-1EFF, U+2000-206F,
  U+20A0-20CF, U+2113, U+2122, U+2190-2199, U+2212, U+FEFF, U+FFFD;
```

Combining marks deliberately accompany the Latin ranges so decomposed accents
retain the original composition/mark-positioning behavior. All OpenType feature
tags are retained, including discretionary stylistic alternates; the subset is
therefore larger than a basic ASCII-only font. Coverage is not tailored merely
to today's biography. The two variable axes are preserved without instancing:

| Axis | Minimum | Default | Maximum |
| --- | ---: | ---: | ---: |
| Optical size (`opsz`) | 14 | 14 | 32 |
| Weight (`wght`) | 100 | 400 | 900 |

## Regeneration

This is a maintainer operation. **Cloudflare/Hugo must only consume the
checked-in WOFF2; they do not install Python tools or regenerate fonts.** No font
is installed into the operating system by the build/verification script.

Use FontTools **4.60.2** and Brotli **1.2.0**, pinned in
`scripts/requirements-fonts.txt`, plus an existing HarfBuzz shared library:

```sh
python3 scripts/subset_inter_font.py static/fonts/InterVariable.woff2
```

The script searches the system for HarfBuzz and also recognizes the library in a
macOS Pillow wheel. If needed, supply its existing path explicitly:

```sh
python3 scripts/subset_inter_font.py static/fonts/InterVariable.woff2 \
  --harfbuzz-library /path/to/libharfbuzz.dylib
```

`--output /path/to/rebuild.woff2` writes a comparison build separately. Use a
temporary virtual environment for the pinned Python requirements if the current
environment differs; do not place dependency environments or full-font copies in
the repository.

## Verification performed

The script decodes the generated WOFF2 and checks:

1. Exact source-intersection coverage for the documented Unicode ranges.
2. All original GSUB/GPOS feature tags, including `ccmp`, `kern`, `mark`, and
   `mkmk`; GDEF/GSUB/GPOS and all variation tables remain present.
3. Byte-identical `fvar`, `avar`, `STAT`, and `MVAR` tables, retaining axes,
   named instances, axis mapping, and global variable metrics.
4. Identical `gvar` tuples for every retained glyph.
5. Identical decomposed outlines and advances for all 1,782 retained glyphs at
   weights **400, 500, 600**, each at optical sizes **14 and 32**. The axis-default
   instance is included. Fixed font line metrics also remain unchanged.
6. **2,772 HarfBuzz shaping comparisons** between source and subset: seven
   representative heading/paragraph/kerning/fraction/accent strings, nine
   weight/optical-size locations, and default shaping plus every individual
   feature tag. Glyph names, clusters, advances, and offsets match exactly.
   Validation used the already installed **HarfBuzz 11.2.1**.
7. Unchanged embedded copyright/license records, a payload below 256 KB, and
   byte-identical repeated builds.

HarfBuzz is used only to compare both fonts under the same shaping engine; its
version does not affect the generated artifact. Source hash and Python tool
versions are enforced. Preserve these checks when changing coverage or updating
the upstream font.
