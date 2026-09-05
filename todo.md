# todo.md

Status: **ACTIVE TODO / NEXT-1C PRODUCTION COMPOSITION / TWO-DOCUMENT RECOVERY RESTORATION IN PROGRESS**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 제품 흐름

```text
Strategy Manager Dialog
-> DSL strategy CRUD
-> authoritative validate + immutable version
-> strategy별 Global/Add-on parameter override CRUD
-> validated strategy/version/profile Chart apply
-> authoritative DSL signal/execution WYSIWYG
-> strategy Backtest Dialog
-> same DSL/version/profile Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

현재 위치는 **NEXT-1C production composition + actual CRUD WYSIWYG**다.

## 2. 저장소 / 작업공간

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
```

trusted executable/test checkpoint:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

trusted evidence:

```text
NEXT-1A combined focused: 13 PASS
Tactical P1 Full: PASS
```

NEXT-1C DSL mount evidence:

```text
2cdc5096fd49f684f07c0b0fdf59c470545330a5
mount-focused: user-local PASS
Full: pending
```

현재 `main.py` production composition:

```text
app.include_router(strategy_workspace_router)
```

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
```

trusted checkpoint:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

trusted evidence:

```text
strategy workspace transport: 6 PASS
DSL manager port: 5 PASS
managed strategy regression: 8 PASS
Tactical P1 Full with this Chart checkout: PASS
```

NEXT-1C Chart candidate:

```text
e99bde72886c0afea04e07bfab0bd25fa8ab15b8
status: REMOTE_UNVALIDATED
```

scope:

```text
MarketChart
 -> BrowserStrategyWorkspacePort default capability
 -> Runtime receives capabilities.strategyWorkspace

serve.mjs
 -> DslStrategyWorkspaceHttpGateway
 -> same-origin strategyWorkspaceProxyMiddleware
 -> DSL_STRATEGY_WORKSPACE_URL or default http://127.0.0.1:8000
```

## 3. 방금 발견/교정 중인 운영 결함

### A. verbose console violation

원칙:

```text
SUCCESS = 기본 1줄
FAILURE = 실패 test/stage/location/message만
```

구현:

```text
scripts/run_focused_tests.py
scripts/verify_tactical_p1.ps1 compact failure filter
Chart scripts/run-tests.mjs 사용
```

직접 `python -m unittest -v` / `node --test` 사용 금지.

### B. two-document authority drift

잘못 생성/사용된 경쟁 운영문서:

```text
SESSION_HANDOFF.md
STRATEGY_PRODUCT_FLOW_TODO.md
CONSOLE_OPERATIONS_POLICY.md
```

조치:

```text
rules.md = 유일 원칙 authority
todo.md  = 유일 현재상태/TODO authority
위 세 경쟁 운영문서 삭제
tests도 rules.md + todo.md만 검사
다른 Markdown은 세션복구/current-state authority로 사용 금지
```

## 4. 최근 실패 분류

최근 compact focused 결과:

```text
19 tests 중 1 failure
```

실패 원인:

```text
test defect
```

`test_stage1_console_output_policy`가 `SESSION_HANDOFF.md` 전체에서 금지 명령 문자열이 없어야 한다고 검사했으나, 그 문자열은 실행명령이 아니라 '금지 예시'로 문서에 존재했다. 더 근본적으로 해당 테스트가 폐기 대상 운영문서를 authority로 검사한 것이 문제다.

따라서 테스트는 `rules.md` / `todo.md` 두 문서만 검사하도록 교정한다.

## 5. NEXT-1C 금지범위

이번 tranche에는 다음을 섞지 않는다.

```text
strategy parameter UI
Chart strategy apply
DSL signal marker generation
Backtest Dialog
Paper/Live
Core/Parser/Runtime/Backtest/Broker semantics 변경
```

## 6. 바로 다음 검증 — COMPACT ONLY

### A. DSL workspace

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

git fetch origin main
git checkout --detach origin/main
git rev-parse HEAD

python .\scripts\run_focused_tests.py `
  test_stage1_console_output_policy `
  test_stage1_strategy_workspace_production_mount `
  test_stage1_strategy_workspace_http_bridge `
  test_stage1_wysiwyg_strategy_workspace
```

성공 기대:

```text
[PASS] Focused tests passed (<count>).
```

### B. Chart workspace

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD

npm test -- `
  tests/strategy_workspace_production_composition.test.mjs `
  tests/strategy_workspace_http_transport.test.mjs `
  tests/dsl_strategy_manager_workspace_port.test.mjs `
  tests/managed_strategy_addon.test.mjs
```

성공 기대:

```text
[PASS] Cascade contract tests passed (<count>).
```

### C. Full

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\verify_tactical_p1.ps1 `
  -Mode Full `
  -ChartRepo ..\cascade-chart-validation-20260904
```

성공 기대:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

## 7. NEXT-1C actual WYSIWYG acceptance

focused + Full PASS 후 실제 화면에서 확인:

```text
1. Strategy Manager open
2. 신규 작성
3. Draft 저장
4. 닫기/재오픈 -> draft 복구
5. 검증 후 저장 -> VALIDATED + version
6. 닫기/재오픈 -> exact validation 복구
7. DSL 한 글자 수정 -> DRAFT
8. 재검증 -> 새 version
9. 삭제
10. 닫기/재오픈 -> 삭제 유지
```

이 acceptance가 통과하기 전에는 NEXT-1C를 DONE/TRUSTED로 닫지 않는다.

## 8. NEXT-1C 이후

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
  - common schema/default
  - strategy별 override CRUD
  - reset one/all = override delete
  - Backtest/Paper/Live mode applicability

NEXT-3 validated strategy/version/profile -> selected Chart subject
  - authoritative DSL signal/execution projection

NEXT-4 strategy Backtest Dialog
  - 기간/종목/전략/profile
  - metrics/trades/equity/execution markers

NEXT-5 same DSL/version/profile realtime Paper
  -> evidence comparison
  -> minimal fine tuning
  -> limited Live
```

## 9. 연구 상태

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: REJECTED
some trailing candidates: no material improvement
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```
