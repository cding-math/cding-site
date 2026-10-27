# Website security

Reviewed on 2026-10-26. This is a static Hugo site hosted on Cloudflare Pages;
there are no application servers, databases, logins, forms, or file uploads in
this repository. This review is not a guarantee that every possible issue has
been found.

## Findings and changes

- Requests for `/gemini.json`, `/openai.json`, `/service-account.json`, `.env`
  files, and `/.git/config` returned the homepage before this change. They did
  not return credential files. A top-level `404.html` now disables Cloudflare
  Pages' automatic homepage fallback. A 404 is correct routing, not access
  control: never deploy secrets, even behind an obscure URL.
- The deployed `/README.md` contained obsolete setup instructions, not secrets.
  It and tracked Finder metadata have been removed from the published files.
- The static mount in `hugo.toml` permits only the asset paths and file types the
  site uses. Hidden-file exclusions must come before includes in Hugo's glob
  slice. New asset types require an explicit configuration change.
- `.gitignore` excludes common credential filenames, environment files, private
  keys, and Finder metadata. This does not detect secrets embedded in ordinary
  source files and is not a substitute for reviewing commits.
- KaTeX was updated from 0.16.11 to 0.19.1, with the npm package's SHA-512
  integrity value verified before copying its distribution files. Versioned
  asset URLs avoid stale browser caches. The old asset URLs redirect to the
  updated version. Keep the package license with the vendored files.
- Inline application scripts and the `onload` handler were replaced with a
  deferred local script. Email assembly uses DOM text properties rather than
  `innerHTML`. Math rendering explicitly disables trusted commands and retains
  bounded expansion and sizing. It now runs in a maintainer-only script; Hugo
  consumes its checked-in cache. Publication titles pass through Markdown with
  raw HTML disabled. Markdown uses
  Hugo's default, which does not render raw HTML. Existing coauthor links in
  `data/publications.yaml` remain trusted, author-maintained HTML.
- Browser response headers block framing, object embeds, inline event handlers,
  form submissions, and base-URL changes. They restrict resource origins,
  disable unused device permissions, and enforce HTTPS for 30 days after a
  browser receives the HSTS header. HSTS deliberately excludes subdomains and
  preload to avoid affecting other services.

## Content Security Policy limitation

Cloudflare Bot Fight Mode injects changing inline JavaScript. The enforced CSP
therefore permits inline script elements while blocking inline event handlers,
`eval`, and scripts from unlisted external origins. This is partial protection,
not a strict CSP. Removing `unsafe-inline` without implementing fresh per-response
nonces would break the existing Cloudflare bot detection. A fixed build-time
nonce is not a secure replacement. Inline styles remain permitted for KaTeX.

## Verification

- Hugo production build and JavaScript syntax checks passed.
- An isolated build containing nine fake secret/configuration files in root and
  nested static directories published none of them.
- Generated pages have no inline application scripts/event handlers, and their
  local asset references resolve. The 404 page is generated correctly.
- A browser preview with the response policy rendered the publication math,
  contact link, and missing-page view without JavaScript or CSP errors.
- Pattern scanning of current source and 46 historical text blobs found no
  credential matches. This is a bounded check, not a forensic compromise audit.

## Hosting and account controls

### 2026-10-27 asset update

- Production CSS, JavaScript, and selected font subsets are fingerprinted into
  `/assets/`; immutable caching is confined to that namespace.
- Canonical HTML routes explicitly revalidate. Global cache headers were removed
  to avoid conflicting values from overlapping Cloudflare `_headers` rules.
- Font licenses are included through exact static allowlist entries. Source
  fonts, generation scripts, design documentation, and local previews stay out
  of the published output.
- Existing CSP, request isolation, and other security headers are retained.
- `scripts/verify_build.py` checks published paths, asset hashes/SRI, licenses,
  font budgets, preload reuse, and cache-rule separation.

Build with `hugo --cleanDestinationDir`, deploy only `public/`, and review the
output before publishing. Keep HTTPS redirects, TLS 1.2 or newer, Cloudflare's
bot and DDoS protections, DNSSEC, and domain transfer protection enabled.
Keep two-factor authentication enabled on Cloudflare, GitHub, and the email
account used for account recovery. Account-specific review results are kept
out of the published source documentation.

## Sources

- [Cloudflare Pages routing](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Cloudflare headers](https://developers.cloudflare.com/pages/configuration/headers/)
- [Cloudflare JavaScript detection and CSP](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/)
- [KaTeX htmlData advisory](https://github.com/KaTeX/KaTeX/security/advisories/GHSA-cg87-wmx4-v546)
- [KaTeX prototype-pollution advisory](https://github.com/KaTeX/KaTeX/security/advisories/GHSA-238p-pmpm-9mq7)
- [KaTeX 0.19.1](https://github.com/KaTeX/KaTeX/releases/tag/v0.19.1)
- [Cloudflare Registrar DNSSEC](https://developers.cloudflare.com/registrar/get-started/enable-dnssec/)
