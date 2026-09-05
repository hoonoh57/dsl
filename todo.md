# todo.md

Status: **ACTIVE TODO / NEXT-1C STRATEGY MANAGER WYSIWYG / ACTUAL KIWOOM ENV CONTRACT REMOTE_UNVALIDATED**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 위치

```text
Base Market Chart
-> actual Kiwoom REST market data
-> Strategy Manager Add-on
-> DSL strategy CRUD / authoritative validation / immutable version
-> strategy별 Parameter Profile CRUD
-> validated strategy/version/profile Chart apply
-> authoritative DSL signal/execution WYSIWYG
-> Backtest Dialog
-> same DSL/version/profile Paper
-> limited Live
```

현재는 **NEXT-1C 실제 Base Chart + Strategy Manager CRUD WYSIWYG**다.

사용자 실제 화면에서 다음은 PASS했다.

```text
Market Chart shell 표시
Strategy Manager · DSL Dialog 자동 open
DSL 전략 목록/편집 UI 표시
```

## 2. 4축 authority

```text
Chart = UX / Add-on host / visualization / Kiwoom market-data request transport
DSL   = strategy source / CRUD / validation / version / Backtest semantics
Kiwoom provider = actual market-data / broker API source
```

Strategy Manager 진입 때문에 Kiwoom 축을 끄거나 mock 데이터를 대체하지 않는다.

금지 유지:

```text
Chart parser / local DSL validation / DB 접근
UI persistence authority
Bridge 전략 의미 해석
로컬 evaluator fallback
임의 mock key 생성
키 값 복사/로그 출력
```

## 3. Kiwoom env authority

사용자가 확인한 실제 `.env` 위치와 변수명이 SSOT다.

```text
E:\2026\gemini\dsl-main-validation-20260904\.env

KIWOOM_MODE=mock|real
KIWOOM_APPKEY=<secret>
KIWOOM_SECRETKEY=<secret>
KIWOOM_BASE_LIVE=https://api.kiwoom.com
KIWOOM_BASE_PAPER=https://mockapi.kiwoom.com
KIWOOM_USE_PAPER=1|0
KIWOOM_ACCOUNT=<account optional for chart reads>
```

현재 사용자 env는 `KIWOOM_MODE=mock` + `KIWOOM_USE_PAPER=1`로 모의투자 REST를 사용한다.

launcher는 DSL workspace root를 `KIWOOM_ENV_DIR`로 Chart process에 전달한다. secret 값 자체는 출력하지 않는다.

Chart `KiwoomRequestBridge`는 위 실제 변수명을 그대로 사용한다. `KIWOOM_MOCK_APP_KEY`, `KIWOOM_REAL_APP_KEY` 같은 별도 key 이름을 요구하지 않는다.

모드별 REST base URL:

```text
mock -> KIWOOM_BASE_PAPER
real -> KIWOOM_BASE_LIVE
```

`KIWOOM_MODE`와 `KIWOOM_USE_PAPER`가 충돌하면 fail-closed한다.

## 4. 저장소 / candidates

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
Strategy Workspace executable/test candidate: 1b0892ff68394856dda27fe5b5679ebd5429eabe
launcher candidate: 274966d0008466f7b31e4cf7c9e0b939ddba98e7
```

launcher 동작:

```text
DSL root .env 존재 확인
-> KIWOOM_ENV_DIR = DSL root
-> launcher-owned 기존 Chart process 종료
-> 최신 Chart code + 현재 DSL .env로 Chart 재기동
```

`strategies.db` 로컬 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
current candidate: 72d5e898ea13dab24575677677565c2d1393e829
```

핵심 변경:

```text
KiwoomRequestBridge
-> KIWOOM_MODE
-> KIWOOM_APPKEY
-> KIWOOM_SECRETKEY
-> KIWOOM_BASE_PAPER / KIWOOM_BASE_LIVE
-> KIWOOM_USE_PAPER consistency guard

KiwoomAccessTokenProvider / KiwoomLocalProxy
-> selected REST base URL 사용

chart.html?manager=1
-> normal MarketChartWorkspace 그대로 사용
-> normal Chart persistence 그대로 사용
-> actual Kiwoom market-data path 그대로 사용
-> Strategy Manager Dialog만 자동 open
```

## 5. 사용자 실제 오류와 교정

### A. 5m DSL validation

```text
ERROR · DSL timeframe(5m)과 데이터 timeframe(1d)이 일치하지 않습니다.
```

교정:

```text
StrategyWorkspace validation fixture는 실제 market timeframe을 주장하지 않음
BacktestEngine authoritative compile/runtime/broker path 유지
실제 market/data_timeframe Backtest strict mismatch 검사는 유지
```

### B. Kiwoom key missing 502

```text
ERROR · Kiwoom proxy HTTP 502:
KIWOOM_MOCK_APP_KEY is required.
```

원인:

```text
실제 .env는 KIWOOM_APPKEY / KIWOOM_SECRETKEY 사용
Chart bridge가 존재하지 않는 KIWOOM_MOCK_APP_KEY 계열을 요구
```

교정:

```text
실제 DSL-root .env 변수명을 그대로 Chart bridge가 사용
mock -> KIWOOM_BASE_PAPER
real -> KIWOOM_BASE_LIVE
Base Chart는 실제 Kiwoom REST 데이터를 계속 사용
```

## 6. 지금 바로 할 일 — 화면 재검증

두 workspace 최신 remote만 받은 뒤 launcher 한 번 실행한다.

```text
http://127.0.0.1:5174/chart.html?manager=1
```

화면 acceptance:

```text
1. KIWOOM_MOCK_APP_KEY missing 502 없음
2. 실제 Kiwoom REST Chart 데이터 표시
3. Strategy Manager Dialog 자동 open
4. 기존 5m DSL -> 검증 후 저장
5. VALIDATED + version + SHA
6. 닫기/재오픈 -> validated 복구
7. DSL 수정 -> DRAFT
8. 재검증 -> 새 version
9. 삭제 -> 재오픈 후 삭제 유지
```

실패 시 화면 오류 한 줄만 전달한다.

## 7. NEXT-1C 종료 조건

```text
actual Kiwoom Base Chart + Strategy Manager CRUD WYSIWYG PASS
-> compact Tactical P1 Full PASS
-> trusted checkpoint 승격
-> todo.md 갱신
```

그 전에는 NEXT-2로 넘어가지 않는다.

## 8. 이후

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
