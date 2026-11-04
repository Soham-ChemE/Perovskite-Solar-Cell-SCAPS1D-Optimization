# QA for the live page (2026-11-04)

Served from docs/ with python -m http.server, loaded in headless Chromium (software WebGL, so render timing is not representative).

## Lighthouse (desktop preset)

Performance 100, Accessibility 98, Best Practices 100, SEO 100

| Metric | Value |
|---|---|
| First Contentful Paint | 0.3 s |
| Largest Contentful Paint | 0.5 s |
| Speed Index | 0.8 s |
| Total Blocking Time | 10 ms |
| Cumulative Layout Shift | 0 |
| Time to Interactive | 0.5 s |
| Avoids enormous network payloads | Total size was 838 KiB |

Report: lighthouse.report.html, lighthouse.report.json.

## Headless-browser check

| View | Load (ms) | Transfer (bytes) | Images loaded | Canvases | Failed requests | Console errors |
|---|---|---|---|---|---|---|
| desktop | 1307 | 2,773,599 | 4/4 | heroCanvas 1440x900, sweepCanvas 476x300 | 0 | 0 |
| mobile | 1286 | 2,773,599 | 4/4 | heroCanvas 375x812, sweepCanvas 305x200 | 0 | 0 |

Screenshots: 2026-11-04-desktop-hero.png, 2026-11-04-mobile-375-hero.png, 2026-11-04-desktop-full.png, 2026-11-04-mobile-375-full.png, 2026-11-04-desktop-end.png, 2026-11-04-desktop-dark-midscroll.png, 2026-11-04-desktop-dark-etl-bars.png.
