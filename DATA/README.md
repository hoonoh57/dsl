# DATA

`DATA/` is the local, rebuildable market-data acceleration layer for the independent cascade lab.

Authority is intentionally split:

```text
market-data-factory MySQL = durable market-data SSOT
DATA/ Parquet            = rebuildable analytical cache
JSON cascade definitions = UI/check-box/parameter persistence
```

Rules:

- Generated cache files under `DATA/` are local-only and must not be committed.
- The DSL, condition modules, Chart, and WYSIWYG UI must not connect to the market-data MySQL database directly.
- Market data enters through a feature-blind Request -> Response adapter owned by the data boundary.
- Cache manifests must identify the source dataset status and fingerprint used to materialize the Parquet cache.
- A source fingerprint change makes the cache stale; stale cache must not silently be treated as current.
- Parquet is derived data, never a second source of truth. Deleting `DATA/` must be recoverable by re-materializing from the market-data owner.
- Completed historical sessions may be served from Parquet. Current/live data remains a hot-source concern and must be merged through the same external market-data contract rather than written as an alternative DSL authority.

Planned generated layout:

```text
DATA/
  manifest/
  parquet/
    daily/
    minute_1m/
    index/
    market_cap/
  derived/
    mtf/
  condition_cache/
  cascade_cache/
  tmp/
  locks/
```

Only this README is version-controlled. All generated content is ignored by Git.
