# Project guidance

- Keep communication concise, precise, and calm.
- Read `docs/design-system.md` before changing layout, typography, or interaction.
- Preserve the approved Zhuque Fangsong name treatment: 72 px heading, three
  upright 24 px glyphs, centered English, and 24 px clearance before the intro.
- Desktop (at least 800 px, fine pointer with hover): reveal on hover or keyboard
  focus. Narrow/touch layouts: persistent plain bilingual text, not a button.
- Production source is `assets/css/style.css`, `assets/js/site.js`, `layouts/`,
  `content/`, and `data/`. CSS is a Hugo template because it embeds font URLs.
- `static/css/style.css` and `static/js/site.js` are frozen compatibility files
  for older cached HTML. Do not use them for new UI changes.
- Hugo fingerprints production assets under `/assets/`. Never reuse a mutable
  filename with immutable caching. Preserve CSP and the static-file allowlist.
- Font artifacts are checked in. Cloudflare builds run Hugo only; do not add
  remote font requests, npm, Python, or font generation to the deployment build.
- See `docs/font-build.md` and `docs/inter-font-build.md` before changing fonts.
  Changing Chinese characters requires regenerating and verifying the subset.
- The sibling `name-reveal-demo/` is a historical local prototype. Do not copy
  its alternate fonts, grid overlays, query overrides, or preview routes into
  production. Keep reusable rules in this repository's `docs/` instead.
- Validate with `hugo --cleanDestinationDir`, `node --check assets/js/site.js`,
  and `python3 scripts/verify_build.py public`. Verify compatibility with the
  configured Cloudflare Hugo version, currently 0.157.0.
- `public/` is tracked: regenerate it cleanly and review it before committing.
  Never stage unrelated user files or credentials.
- Pushing `main` to `origin` triggers Cloudflare Pages. Deploy only when the user
  authorizes deployment; verify the matching check and the live site's assets,
  cache headers, and interaction after pushing.
