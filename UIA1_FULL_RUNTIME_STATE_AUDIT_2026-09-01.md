# UIA-1 Full Runtime State Audit — 2026-09-01

Status: **WRITTEN / USER-LOCAL REVALIDATION REQUIRED**

## Problem

Real UI acceptance showed selective restore failures even though one JSON document existed:

```text
SuperTrend -> restored
volume / indicator pane heights -> not restored
added compare subjects -> not reliably restored
```

A single persistence file is not sufficient if individual runtime projections are restored through separate code paths without a complete post-startup equality check.

## Corrected acceptance model

```text
hydrate chart-state.json
 -> construct complete chart/runtime
 -> restore primary subject / timeframe / viewport / display
 -> restore Add-ons and compare subjects
 -> restore all persisted pane layouts
 -> capture actual live runtime snapshot
 -> compare persisted JSON against actual runtime projection
 -> PASS: attach persistence
 -> FAIL: persistence remains detached and report all mismatches together
```

The restore audit covers persisted semantic state and its live projection, including:

```text
primary instrument
primary timeframe / base date / adjusted mode
viewport
price display mode
active registered Add-ons
all persisted Add-on state/properties
primary price + volume pane heights
all persisted Add-on pane heights
compare-subject list vs actually mounted compare panes
```

## SSOT protection rule

Startup auto-layout or incomplete runtime reconstruction must not become a new authority.

Therefore persistence is not attached until the persisted state and actual runtime projection pass the exhaustive restore audit. If restore fails, the existing `chart-state.json` is preserved and the UI reports `STATE RESTORE ERROR` with the mismatching paths.

## Close checkpoint

After startup restore has been verified, close/dispose captures the current live chart state before the final one-document flush. This prevents feature-specific close hooks from being required for pane layout, primary request, viewport, or display mode.

## Acceptance

`verify.bat` must include syntax/tests for the runtime audit. Real UI remains authority. UIA-1 is not PASS until a restart restores the full semantic state and the exhaustive audit reports no mismatch.
