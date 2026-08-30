# Kiwoom Condition Chart Vendor Pin

This project consumes the chart implementation from `hoonoh57/kiwoom-condition` as a read-only pinned Git submodule.

Source repository: `https://github.com/hoonoh57/kiwoom-condition`
Source branch at selection time: `main`
Pinned source commit: `4791ef62c9207149702a68ef251499c6e05b6dcc`
Pinned chart subtree: `condition1516/chart-platform`
Pinned chart subtree tree SHA: `203b677a3491a998490ea764aab3ac1cd6f88b5e`

Policy:

- Do not modify the source repository as part of DSL work.
- Do not edit vendored chart files to adapt them to DSL.
- Integration code must live outside `vendor/kiwoom-condition`.
- Updating the pin requires an explicit source-version decision and a new verification checkpoint.
- The chart platform's own `CHART_PLATFORM_PROVENANCE.json` remains authoritative for its internal upstream provenance.
