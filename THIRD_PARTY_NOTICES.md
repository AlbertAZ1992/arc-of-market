# Third-Party Notices

ArcOfMarket publishes its own compact calculations and source attribution. It does not claim ownership
of upstream market data, names, trademarks, or databases.

- Yahoo Finance / yfinance: used as an in-memory adjusted-close research input. Releases may include
  compact metrics and at most 252 rebased return observations starting at 100; they do not include
  original price levels, raw OHLCV, or a downloadable price database. Operators remain responsible
  for confirming that their use complies with upstream terms.
- Wikipedia: current index membership is adapted from Wikipedia contributors under CC BY-SA 4.0.
  Releases identify the observation date and disclose current-universe survivorship bias.
- FRED: this product uses FRED data but is not endorsed or certified by the Federal Reserve Bank of
  St. Louis. Releases retain the original series IDs and mark values as latest revised observations.
- U.S. Treasury: daily par yield curve rates are used for compact current values and changes.
- Office of Financial Research: Financial Stress Index observations are attributed to OFR. ArcOfMarket
  is not endorsed by OFR or the U.S. Treasury.
- Cboe Global Markets: VIX is read in memory. Public Releases contain only the current value, previous
  value, daily change, and ArcOfMarket-derived risk state, not the full historical file.
- U.S. CFTC: Traders in Financial Futures reports are U.S. government information published for public
  analysis. Releases acknowledge CFTC and publish VIX positioning history without implying endorsement.
- ICE Data Indices / BofA: the licensed high-yield OAS series distributed through FRED is not fetched or
  published by the public pipeline.

Third-party Python dependencies retain their own licenses. ArcOfMarket's Apache-2.0 license applies to
the original code, contracts, and methodology text, not to upstream data rights or trademarks.
