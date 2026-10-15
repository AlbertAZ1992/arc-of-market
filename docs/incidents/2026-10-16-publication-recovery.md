# Publication recovery, 2026-10-16

The September 23 release skipped September 22 in `coreRotationInputs.previousSession`.
The collector had removed an entire price row when any unrelated core symbol was missing.
Cloud correctly refused the discontinuous strategy input. The daily workflow then kept
publishing only the latest release and failed on each subsequent day. Raw market releases
continued to update while official posts and daily emails stopped at September 22.

## Corrections

- Validate each symbol's history independently and retain all available trading rows.
- Require complete, positive, finite QQQ/VTV strategy inputs before approving core data.
- Schedule at 17:17, 18:17, 19:17, 20:17 and 21:17 New York time. The first attempt is
  05:17 China time during U.S. daylight saving time and 06:17 during U.S. standard time.
  GitHub can delay scheduled jobs; these are trigger times, not a delivery guarantee.
- Allow a rerun to publish the existing immutable release even when there is no Git diff.
- Retry transient publication failures with the same release identity; reject bad input
  immediately rather than retrying it as an outage.

## Historical recovery

`releases/history/roc35-recovery-2026-10-16.json` contains 15 reconstructed observations
for September 23 through October 13. They use currently available adjusted daily QQQ/VTV
prices and carry computation time and input digests. They are not point-in-time official
releases or evidence of historical email delivery. Existing immutable releases remain intact.

Cloud replayed these observations from its September 22 production checkpoint, preserving
portfolio state and confirmation memory. Existing history was retained. October 14 uses the
original immutable official Market Release and a single normal brief notification event.

Validation: Ruff formatting/lint, the repository CI's `ty check scripts src`, and 77 tests
passed. Cloud recovery was first exercised against a database export, with foreign keys
checked and original rows preserved, before the production import.
