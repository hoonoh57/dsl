# UX Max UI Branch

Branch: `ux-max-ui`

## Goal

Maximize user convenience around the original product flow without replacing or contaminating the existing UI or deterministic DSL Core.

Natural-language mode is explicitly human-mediated:

```text
natural-language idea
 -> generate LLM request prompt
 -> human copies prompt to external LLM
 -> human pastes LLM result back
 -> strip optional code fence
 -> local DSL candidate
 -> actual DSL Parser + Semantic validation
 -> only on PASS enable the final backtest step
```

The application does not automatically call an external LLM in this branch.

## Preservation rule

The existing UI in `app_ui.py` is preserved unchanged.

- Legacy UI: `/`
- UX-max UI: `/ux`
- New UX-only validation API: `/api/ux/validate`
- Existing strategy CRUD reused: `/api/strategies`
- Existing legacy demo chart endpoint reused: `/api/backtest`
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

## Human-mediated LLM contract

The UI performs these stages explicitly:

1. user writes the strategy in natural language;
2. UI creates a copyable LLM request prompt;
3. user manually sends that prompt to an external LLM and receives the response;
4. user pastes the response into the UI;
5. the UI admits only the pasted text as a local DSL candidate, removing an optional markdown code fence;
6. `DSLParser.parse(...)` and `DSLSemanticAnalyzer.analyze(...)` must both PASS;
7. any edit to the DSL invalidates the PASS and disables the final button until re-validation.

LLM output therefore has no execution authority.

## Important current limitation

`/api/backtest` belongs to the preserved legacy `app_ui.py` demo engine. It currently calculates a fixed demonstration strategy and does not execute the validated DSL text itself.

For that reason the UX labels this stage **demo backtest** and explicitly does not claim that its chart/metrics are the execution result of the validated DSL.

A later, separately validated tranche should connect the already validated DSL to the repository's real deterministic DSL BacktestEngine rather than silently pretending that the legacy demo endpoint does so.

## Authority boundary

This branch changes presentation/workflow and adds fail-closed local validation only. It does not add leader/follower syntax, adaptive execution authority, allocation authority, provider authority, hard-guard bypasses, or automatic external-LLM authority.

## Focused test

```powershell
python -m unittest test_ux_max_ui.py
```

The focused tests pin these boundaries:

- `/` and `/ux` coexist on the same existing FastAPI app;
- legacy root is not replaced;
- natural-language flow explicitly contains the human relay;
- prompt mode does not use the legacy heuristic PROMPT transpiler;
- LLM output must pass real Parser + Semantic validation;
- invalid DSL fails closed;
- final chart stage is explicitly identified as the legacy demo backtest;
- external LLM output has no execution authority.
