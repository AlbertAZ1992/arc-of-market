# ArcOfMarket Anyway-style redesign QA

Date: 2026-07-26

## Scope

- Homepage
- About
- Archive
- Lab
- Macro and S&P 500 chart pages
- Nasdaq, Dow Jones and Magnificent Seven chart pages
- Sector archive and twelve sector/topic pages
- Floating chart directory
- Desktop sidebar and mobile navigation states

## Reference contract

- Layout reference: `anyway.fm`
- Brand and content: ArcOfMarket
- Typography:
  - Serif: Noto Serif SC / Source Han Serif SC / Merriweather
  - Sans: Noto Sans SC / Source Han Sans SC / Open Sans
  - Mono: Fira Mono
- Icons: Solar Iconify collection
- Illustrations: intentionally omitted at the product owner's request

## Visual comparison

Desktop comparisons use the same 1280 × 720 viewport with the source on the left
and ArcOfMarket on the right:

- `product-audit/comparisons/00-home-source-local-v2.jpg`
- `product-audit/comparisons/10-about-source-local-v2.jpg`
- `product-audit/comparisons/20-archive-source-local-v2.jpg`
- `product-audit/comparisons/30-lab-source-local-v2.jpg`

Mobile breakpoint comparisons use a 390 × 844 canvas:

- `product-audit/comparisons/40-home-mobile-source-local.jpg`
- `product-audit/comparisons/50-about-mobile-source-local.jpg`
- `product-audit/comparisons/60-archive-mobile-source-local.jpg`
- `product-audit/comparisons/70-lab-mobile-source-local.jpg`

Checked:

- Red viewport frame and white editorial surface
- 173 px fixed desktop sidebar
- 40 px mobile header and red full-screen menu styling
- Dotted dividers and column boundaries
- Heading scale and content start positions
- Market tabs follow the intended reading order:
  Macro, S&P 500, Nasdaq, Dow Jones, Magnificent Seven, Sectors, Lab
- Archive contains only currently openable chart and research entries
- Two-column archive density and mobile single-column rules
- Alternating Lab timeline
- Fixed bottom chart directory, shadow, plain-language metadata and expanded panel
- No raster illustrations or copied site artwork

## Interaction checks

- Archive search for `全球金融压力` returns one matching chart.
- Floating chart directory opens, lists six macro charts and closes.
- All seven category tabs are present in the expected order.
- Nasdaq loads both TradingView chart panels.
- Sector archive links to all twelve sector/topic pages.
- Mobile archive has no document-level horizontal overflow at 390 px.
- Twenty-four static routes build successfully.
- Browser console shows no application errors.

## Automated checks

- `pnpm check`: passed with zero errors, warnings or hints.
- `pnpm lint`: passed with zero errors or warnings.
- `pnpm build`: passed; twenty-four routes generated.

## Result

The implementation matches the reference layout system while preserving
ArcOfMarket branding, the intended market-reading sequence, source transparency
and the requested no-illustration constraint. Public pages no longer expose
internal data-audit or authorization labels.

final result: passed
