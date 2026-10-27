# Loading audit — 2026-10-27

## Scope and method

Measured the live https://cding.me/ before changes (commit `d3d0aed`), then
compared an isolated local control and the production candidate. Final live
verification will be recorded below after Cloudflare publishes the change.

Lighthouse 13.5.0 ran in a separate headless Helium/Chromium 156 browser with
fresh temporary profiles. Desktop: 1280 × 900, device scale 1, CPU 1×. Mobile:
402 × 874, device scale 3, CPU 4×. Mobile emulation does not reproduce a physical
phone, Safari, or Android's system fonts. Tests ran sequentially on this Mac.

- Unthrottled: actual host connection (`throttlingMethod: provided`).
- Slow 4G: DevTools throttling, 150 ms request latency, 1,600 Kbps download,
  750 Kbps upload. This is actual browser throttling, not Lighthouse simulation.
- Slow 3G stress: 400 ms request latency, 400 Kbps download/upload, CPU 4×.
- Cold: separate fresh profile per scenario. Warm: same mobile profile and
  `disableStorageReset: true` on the immediately following navigation.
- Timings are from navigation start; FCP is first content, LCP is largest content
  (the portrait on mobile), and CLS measures unexpected movement. They are
  individual lab observations, not population averages or field guarantees.

## Initial live measurements

| Scenario | FCP | LCP | CLS |
| --- | ---: | ---: | ---: |
| Desktop, actual connection | 0.796 s | 0.796 s | 0.004851 |
| Desktop, Slow 4G | 0.618 s | 0.618 s | 0.018654 |
| Mobile, Slow 4G, cold | 0.871 s | 1.742 s | 0.077907 |
| Mobile, Slow 4G, warm | 0.387 s | 0.387 s | 0 |
| Mobile, Slow 3G, cold | 1.306 s | 5.770 s | 0.077907 |

Independent [PageSpeed report](https://pagespeed.web.dev/analysis/https-cding-me/te5uft74vy?form_factor=mobile)
from 11:07 AM PDT: mobile FCP 1.538 s, LCP 3.006 s, CLS 0.068; desktop
0.425 s, 0.706 s, 0.025. Its environment is different (Lighthouse's simulated
Slow 4G/Moto G Power), so its timings should not be compared directly with the
DevTools table. It independently identified the Inter swap as a shift source.
There was no CrUX field dataset for this site. The `mobile-before-*.jpg` files
are that report's ordered filmstrip frames; they have no recorded trace times.

## Causes and changes

1. The 199 KB broad-Latin Inter preload changed biography wrapping. The approved
   outlines now arrive in a 38,136-byte core; broad coverage is still available
   on demand. Body-only local fallback metrics preserve line breaks while it
   loads. Font fidelity is separately verified by the subset generator.
2. Raw TeX in publication titles changed to formatted math after client KaTeX
   ran. A trace showed two opposite 28 px row movements (font swap, then math).
   Exact KaTeX 0.19.1 HTML/MathML is now checked in and inserted by Hugo; no
   client renderer is loaded. The two used math faces use `font-display: swap`.
3. The new Chinese subset was not the cause: it is only 2,572 bytes and completed
   before FCP in every cold baseline and final-local scenario. Reserved heading
   dimensions prevent it from moving adjacent page content.
4. Legacy CDN image/math-font entries retained old conflicting cache headers.
   Targeted cache refresh and verification are part of final live deployment.

## Final local candidate

| Scenario | FCP | LCP | CLS |
| --- | ---: | ---: | ---: |
| Desktop, unthrottled localhost | 0.128 s | 0.128 s | 0 |
| Desktop, Slow 4G | 0.598 s | 0.598 s | 0.000173 |
| Mobile, Slow 4G, cold | 0.603 s | 1.175 s | 0.000287 |
| Mobile, Slow 4G, warm | 0.233 s | 0.233 s | 0 |
| Mobile, Slow 3G, cold | 1.461 s | 4.152 s | 0.000287 |

Local control vs final candidate on Slow 4G mobile: CLS 0.077907 → 0.000287;
LCP 1.454 s → 1.175 s. The local server used gzip/cache headers, but does not
include Cloudflare's network path or injected scripts; live results below are
needed for deployment conclusions. TBT was zero in this final local matrix.

Font finish on final-local mobile Slow 4G: Chinese 0.418 s, Inter 0.939 s;
Slow 3G: Chinese 1.146 s, Inter 3.429 s. Text remains readable before Inter
finishes. The final custom letterforms can still visibly replace fallback
letterforms on a sufficiently slow first visit: there is no promise of zero
font delay. Large paragraph/list jumps were eliminated in these tests; the
remaining tiny CLS is inline text movement. Warm font transfers were zero.

## Rechecking

Use the same Lighthouse version, dimensions, network values and CPU factors.
Keep runs sequential and preserve cold/warm distinction. Save the LHR JSON,
network/font timings, trace and timed filmstrip outside the published site.
Compact raw measurements are checked in here; large traces remain local.
Inspect the first nonblank frame and the final frame, not just the score.

Recheck after biography/publication edits, font updates, grid changes or hosting
cache changes. Additional scripts/characters can load larger fallback fonts.
OS-specific fallback availability can change results. Actual iOS/Android
hardware and real-user monitoring remain outside this audit.
