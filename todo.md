# todo.md

Status: **ACTIVE TODO / NEXT-1C STRATEGY MANAGER WYSIWYG / UI OPEN PASS / TWO DEFECT FIXES REMOTE_UNVALIDATED**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 위치

```text
Base Market Chart
-> Strategy Manager Add-on
-> DSL strategy CRUD / authoritative validation / immutable version
-> strategy별 Parameter Profile CRUD
-> validated strategy/version/profile Chart apply
-> authoritative DSL signal/execution WYSIWYG
-> Backtest Dialog
-> same DSL/version/profile Paper
-> limited Live
```

현재는 **NEXT-1C 실제 CRUD WYSIWYG**다.

사용자 실제 화면에서 다음은 PASS했다.

```text
Market Chart 표시
Strategy Manager · DSL Dialog 자동 open
DSL 전략 목록/편집 UI 표시
```

## 2. 4축 authority

```text
Chart = UX / Add-on host / visualization / Request-Response transport
DSL   = strategy source / CRUD / validation / version / Backtest semantics
```

금지 유지:

```text
Chart parser / local DSL validation / DB 접근
UI persistence authority
Bridge 전략 의미 해석
로컬 evaluator fallback
```

## 3. 현재 remote candidates

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
current executable/test candidate: 1b0892ff68394856dda27fe5b5679ebd5429eabe
launcher candidate: daf1e338614667dbb7a6dfc461a45658ec397b27
```

변경:

```text
core/strategy_validation_fixture.py
-> deterministic validation fixture
-> 실제 market timeframe을 주장하지 않음

addons/strategy_manager/workspace.py
-> 여전히 BacktestEngine.run(...) authoritative
-> validation fixture만 core에서 주입

실제 market/data_timeframe BacktestEngine mismatch 검사는 변경하지 않음
```

`strategies.db` 로컬 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
current direct WYSIWYG candidate: e23e277a7dfa9ac2d11ca6952a1c1a66b13d848a
```

변경:

```text
MarketChartWorkspace 기본 동작
-> 기존 persistence 복원 유지

chart.html?manager=1 direct WYSIWYG
-> restoreAddonPersistence = false
-> config/exact-chart.addons.json clean defaults 사용
-> strategy.manager만 활성
-> 사용자의 기존 Chart persistence는 읽거나 덮어쓰지 않음
```

## 4. 사용자 실제 오류와 교정

### A. 5m DSL validation

사용자 evidence:

```text
ERROR · DSL timeframe(5m)과 데이터 timeframe(1d)이 일치하지 않습니다.
```

원인:

```text
StrategyWorkspace validation
-> BacktestEngine 기본 synthetic fixture
-> fixture가 1d라고 잘못 주장
```

교정:

```text
validation fixture는 timeframe claim 없음
BacktestEngine authoritative compile/runtime/broker path 유지
실제 Backtest strict timeframe 검사는 유지
```

### B. Kiwoom 502가 Strategy Manager 검증 화면을 오염

사용자 evidence:

```text
ERROR · Kiwoom proxy HTTP 502
KIWOOM_MOCK_APP_KEY is required.
```

원인:

```text
direct WYSIWYG가 과거 persisted Chart Add-on 상태까지 복원
-> Strategy Manager와 무관한 Kiwoom/research Add-on이 같이 활성될 수 있음
```

교정:

```text
manager=1 direct WYSIWYG만 clean default add-on state
일반 Chart persistence 동작은 그대로
```

## 5. 지금 바로 할 일 — 화면 재검증만

두 workspace를 최신 remote로 맞추고 launcher를 재시작한다.

기대 URL:

```text
http://127.0.0.1:5174/chart.html?manager=1
```

화면에서 확인:

```text
1. Strategy Manager Dialog 자동 open
2. Kiwoom 502가 자동 발생하지 않음
3. 5m DSL -> 검증 후 저장
4. VALIDATED + version + SHA 표시
5. 닫기/재오픈 -> validated 상태 복구
6. DSL 수정 -> DRAFT
7. 재검증 -> 새 version
8. 삭제 -> 재오픈 후 삭제 유지
```

실패 시 화면 오류 한 줄 또는 스크린샷만 전달한다.

## 6. NEXT-1C 종료 조건

```text
실제 CRUD WYSIWYG PASS
-> compact Tactical P1 Full PASS
-> trusted checkpoint 승격
-> todo.md 갱신
```

그 전에는 NEXT-2로 넘어가지 않는다.

## 7. 이후

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
NEXT-3 validated strategy/version/profile -> selected Chart subject
NEXT-4 strategy Backtest Dialog
NEXT-5 same DSL/version/profile realtime Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

연구 상태:

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: REJECTED
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```
