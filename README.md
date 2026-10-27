# cding.me

Personal academic website for Changying Ding, built with Hugo and deployed by
Cloudflare Pages from `main`.

Start with the [project handoff](docs/handoff.md) for implementation status,
measured limitations, and the documentation map.

## Edit and preview

```sh
hugo server
```

- Biography: `content/_index.md`
- Publications: `data/publications.yaml`
- Shared layout and name markup: `layouts/`
- Production styling and behavior: `assets/css/style.css`, `assets/js/site.js`
- CV, portrait, and unchanged vendor resources: `static/`

The CSS and JavaScript are minified and fingerprinted by Hugo. Fonts are
self-hosted; the Chinese name uses a checked-in three-character WOFF2 subset.

## Design and maintenance

- [Approved design system](docs/design-system.md)
- [Font provenance and reproducible Chinese subset](docs/font-build.md)
- [Inter core subset](docs/inter-core-font-build.md) and [broad Latin](docs/inter-font-build.md)
- [Stable math rendering](docs/math-rendering.md)
- [Performance and deployment](docs/performance.md)
- [Security notes](SECURITY.md)
- [Agent guidance](AGENTS.md)

## Build and validate

```sh
hugo --cleanDestinationDir
node --check assets/js/site.js
node scripts/render_math.mjs --check
python3 scripts/verify_build.py public
```

Cloudflare currently uses Hugo 0.157.0. Font generation is a maintainer-only
operation; no Python packages or upstream downloads are needed for deployment.
`public/` remains tracked and should be regenerated cleanly before a commit.
Pushing to `main` triggers the existing Cloudflare Pages Git integration.
