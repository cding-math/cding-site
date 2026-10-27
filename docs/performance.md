# Asset loading and deployment

## Chinese name

The approved Zhuque Fangsong design is distributed as a **2,572-byte WOFF2**
containing 丁长缨 only, rather than the 8,824,084-byte upstream TTF. See
`font-build.md` for the source hash, license, build instructions, and verification.

The homepage preloads the exact fingerprinted font URL used by CSS, with
`as="font"`, `type="font/woff2"`, and `crossorigin`. This avoids a separate
first-hover download and provides the persistent mobile name promptly. The
tradeoff is a 2.5 KiB download even for desktop visitors who never hover.

`font-display: swap` keeps text available if the font is delayed. Fixed glyph
cells and a reserved 72 px heading prevent the Chinese font from moving the
photo or biography. A fallback glyph can look different briefly; this is not a
promise of zero latency or zero layout shift for the entire page.

## English typography

The original Inter variable font is also subset to broad Latin, Latin Extended,
combining marks, punctuation, and common symbols. All variable axes and shaping
features are retained and verified against the source; see `inter-font-build.md`.
Its CSS alias is `Site Sans`, followed by the unchanged full `Inter` as a fallback
for future characters outside the subset. Complementary Unicode ranges prevent
the full fallback from downloading for ordinary Latin text while Site Sans loads.

The Latin file is **199,328 bytes**, down from **352,240 bytes** (43.41% smaller).
Together with the 2,572-byte Chinese subset, the two primary fonts total 201,900
bytes, below the previous single Inter download. These are file-size measures,
not a promise of a particular network latency.

The homepage preloads this smaller Latin file and uses `font-display: swap`.
This avoids the previous `optional` behavior keeping a fallback face for an
entire slow first visit. Text remains visible during loading; early discovery and
the smaller payload reduce the delay before the approved typography appears.
The font is not a reason to delay the whole page behind a loading state.

## Versioning and cache policy

Hugo builds the fonts first, injects their hashed URLs into the stylesheet,
minifies CSS/JS, then fingerprints the final CSS/JS. All such output lives under
`/assets/`, with `Cache-Control: public, max-age=31536000, immutable`. A content
change produces a new URL, so a long browser cache cannot retain an old revision.

Canonical HTML routes explicitly use `public, no-cache` so browsers validate
their copy. Cloudflare may still cache and revalidate these responses. This is
different from `no-store` and avoids needless repeat downloads when unchanged.

Cloudflare's Browser Cache TTL or Cache Rules can override origin freshness.
The intended account setting is **Respect Existing Headers**. Verify the actual
custom-domain response after deployment; a `no-cache` directive requires
validation even if Cloudflare also supplies a numeric max-age. Existing browser
caches from an earlier deployment cannot be purged remotely.

Unversioned Inter fallback, images, CV, and vendor resources keep their existing
cache policy. The old `/css/style.css` and `/js/site.js` files remain only for
compatibility with previously cached HTML; the new homepage does not request them.
The global `_headers` block contains security headers only, avoiding duplicate,
comma-joined Cache-Control values from overlapping route rules.

## Deployment

Cloudflare's Git integration builds `main` with Hugo 0.157.0 and publishes
`public/`. All font artifacts are committed. The build requires no Node package
installation, font tooling, font service, Worker, or runtime backend.

Before pushing:

1. Build cleanly with the configured Hugo version.
2. Run `python3 scripts/verify_build.py public` and the JavaScript syntax check.
3. Compare desktop and mobile geometry against `design-system.md` and its
   reference screenshots. Check hover, keyboard, static mobile text, and themes.
4. Ensure docs, scripts, font sources, preview routes, and alternative fonts are
   absent from the generated site; retain required font-license files.

After pushing:

1. Verify the Cloudflare check for the exact pushed commit.
2. Verify live HTML references the new hashed resources and revalidates.
3. Fetch the subset font and confirm its length/hash, MIME type, and immutable
   cache policy. Check that preload and CSS use the same URL.
4. Inspect the live page and confirm the name renders, the contact link and math
   work, and missing routes still return 404.

Rollback uses a reviewed Git revert of the deployment commit and a normal push;
the content hashes make the reverted asset versions unambiguous.

## References

- [Cloudflare Pages headers](https://developers.cloudflare.com/pages/configuration/headers/)
- [Pages asset serving](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Browser Cache TTL](https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/set-browser-ttl/)
- [Hugo fingerprinting](https://gohugo.io/functions/resources/fingerprint/)
- [Hugo CSS templates](https://gohugo.io/functions/resources/executeastemplate/)
