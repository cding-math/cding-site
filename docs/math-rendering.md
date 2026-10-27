# Stable first-paint mathematics

Mathematical titles now arrive already rendered in the HTML. Previously the
browser first laid out raw `$q$` text, then reformatted it after loading KaTeX.
In a slow-network trace that changed a publication title's line count and moved
following rows by 28 px. The Inter swap caused another movement in the opposite
direction. Pre-rendering removes that intermediate layout and the approximately
79 KB compressed KaTeX JavaScript/auto-render download from page loading.

## Preserve the approved renderer

`scripts/render_math.mjs` uses the existing vendored **KaTeX 0.19.1** directly,
with `trust: false`, bounded expansion/size, and errors that fail generation.
It uses Node built-ins only—no npm installation or network access.

The generated `data/math_rendered.json` is checked in. Hugo's passthrough hook
uses that cache for Markdown and publication titles. HTML plus MathML preserves
the existing visual rendering and accessible mathematical meaning. The same
vendored stylesheet/fonts remain in use. Hugo copies the two currently used
WOFF2 faces to content-hashed `/assets/` URLs without altering their bytes.
Their `swap` declarations reuse those URLs and receive immutable caching;
legacy paths remain available for older HTML and other mathematical faces.

Hugo 0.157.0's embedded math renderer was evaluated but its HTML class names do
not match KaTeX 0.19.1's stylesheet. Do not silently substitute it or perform
ad-hoc class-name replacements. The cache keeps exact renderer/CSS compatibility
while preserving the Hugo-only Cloudflare build.

## Add or change mathematics

1. Edit the normal Markdown/publication title.
2. Add any new LaTeX expression, without delimiters, to
   `data/math_expressions.json`.
3. Run `node scripts/render_math.mjs` and commit the updated cache.
4. Run `node scripts/render_math.mjs --check`, build Hugo, and inspect the result.

Both inline and display forms are generated. An expression missing from the
cache fails the Hugo build rather than shipping unformatted math. The supported
delimiters are `$...$`, `\(...\)`, `$$...$$`, and `\[...\]`; escape literal dollar
signs in Markdown. Raw HTML remains disabled in Goldmark.

The cache records the renderer version and SHA-256. Regenerate and recheck it
when updating KaTeX. These data files and maintainer scripts are not published.
Cloudflare continues to run only `hugo --cleanDestinationDir`.
