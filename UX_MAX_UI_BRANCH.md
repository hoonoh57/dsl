# UX Max UI Branch

Branch: `ux-max-ui`

## Goal

Maximize user convenience around the original product flow without replacing or contaminating the existing UI or deterministic DSL Core.

```text
user idea
 -> prompt / imported source
 -> DSL draft
 -> user review/edit
 -> existing DSL/backend contracts
 -> backtest/chart/result
```

## Preservation rule

The existing UI in `app_ui.py` is preserved unchanged.

- Legacy UI: `/`
- UX-max UI: `/ux`
- Existing API contracts reused: `/api/strategies`, `/api/transpile`, `/api/backtest`
- New entrypoint: `app_ui_ux.py`

Run:

```powershell
python .\app_ui_ux.py
```

Then open:

```text
http://127.0.0.1:8000/ux
```

The legacy screen remains available at:

```text
http://127.0.0.1:8000/
```

## UX priorities

1. Make the primary workflow obvious: idea -> DSL -> save -> backtest -> result.
2. Keep natural language, Pine Script and Kiwoom inputs in one composer instead of separate product mental models.
3. Keep the final DSL visible and editable as the execution control point.
4. Keep deterministic Core/guard messaging visible; prompt generation does not get execution authority.
5. Add strategy search, draft recovery, keyboard shortcuts, copy/format actions and one-screen metrics/chart feedback.
6. Preserve a direct link back to the legacy UI.

## Authority boundary

This branch changes presentation/workflow only. It does not add leader/follower syntax, adaptive execution authority, allocation authority, provider authority, or hard-guard bypasses.

The UI can request DSL drafting or existing transformations, but execution remains behind the existing DSL/backend contracts.

## Focused test

```powershell
python -m unittest test_ux_max_ui.py
```

The test fixes the preservation contract: `/` and `/ux` must coexist, both share the same existing FastAPI app, the legacy root must not be replaced, and the UX surface must continue to use the existing API endpoints.
