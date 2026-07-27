# ArcOfMarket homepage design QA

Final result: passed

## Comparison

- Reference: `/Users/albertaz/Downloads/微信图片_20260727211421_224_2.png`
- Implementation: `http://127.0.0.1:4323/`
- Viewport: `1488 × 1058`
- Side-by-side image:
  `/Users/albertaz/.codex/visualizations/2026/07/27/arc-of-market-redesign/comparison.jpg`

## Visual review

| Area | Result | Notes |
| --- | --- | --- |
| Red frame and fixed sidebar | Passed | Frame, sidebar width, logo block and navigation rhythm align with the reference. |
| Typography | Passed | Uses the requested Noto Serif / Merriweather and Noto Sans / Open Sans stacks. |
| Hero hierarchy | Passed | Date, kicker, judgment, summary and three evidence items follow the same reading order. |
| Strategy strip | Passed | Uses the same horizontal editorial structure and keeps execution fields locked. |
| Evidence chart | Passed | Chart and right-hand interpretation column match the reference proportions. |
| Spacing and rules | Passed | Major horizontal divisions and content insets visually align at the target viewport. |
| Icons | Passed | Solar icon assets are used; no handmade SVG or placeholder assets are present. |

## Product and behavior review

- The homepage judgment is generated from checked-in market datasets.
- The placeholder breadth dataset is not used in a production-facing claim.
- The key chart loads S&P 500 and VIX data and fails closed if either dataset is unavailable.
- The five-act homepage story contains eight working charts with no production placeholder blocks.
- The Strategy Signals and historical-validation links navigate to working destinations.
- The Signals page distinguishes public validation from future execution-only subscription fields.
- The mobile layout has no document-level horizontal overflow at `390 × 844`.
- The mobile navigation opens, closes and reports its expanded state correctly.
- Type checks, lint, production build and chart-catalog audit pass without warnings.

## Resolved findings

- P1: Removed the duplicate ECharts legend below the editorial legend.
- P1: Prevented the Signals page headline from leaving a single orphaned character.
- P2: Shortened the trend evidence label so it remains on one line at the reference viewport.
