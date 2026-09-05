# todo.md

Status: **ACTIVE TODO / NEXT-1C STRATEGY MANAGER WYSIWYG / REAL KIWOOM ENV PATH REMOTE_UNVALIDATED**

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

## 3. Kiwoom env authoritative contract

기존 `hoonoh57/kiwoom-auto`의 `.env` 계약을 그대로 따른다.

```text
KIWOOM_MODE=mock|real
KIWOOM_USE_PAPER=1|0
KIWOOM_APPKEY=<secret>
KIWOOM_SECRETKEY=<secret>
KIWOOM_ACCOUNT=<account>
```

실제 key 값은 repo/로그/UI에 복사하지 않는다.

Chart bridge가 임의로 도입했던 다음 계약은 기존 운용계약보다 authority가 아니다.

```text
KIWOOM_MOCK_APP_KEY
KIWOOM_MOCK_SECRET_KEY
KIWOOM_REAL_APP_KEY
KIWOOM_REAL_SECRET_KEY
```

현재 Bridge는 `KIWOOM_MODE + KIWOOM_APPKEY + KIWOOM_SECRETKEY`를 우선 사용한다. legacy 변수는 기존 자동테스트/이행 호환만 유지한다.

## 4. 저장소 / candidates

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
Strategy Workspace executable/test candidate: 1b0892ff68394856dda27fe5b5679ebd5429eabe
launcher candidate: aa4df58dffb5e761b996874afbed6d8c5634cf35
```

launcher는 기본적으로 다음 existing env를 읽게 한다.

```text
E:\2026\gemini\kiwoom-auto\.env
```

구현상 `KIWOOM_ENV_DIR`만 Chart process에 전달하며 secret 내용을 읽어 출력하지 않는다.

Start 시 launcher-owned 기존 Chart process를 먼저 종료하고 최신 code + current `.env`로 재기동한다.

`strategies.db` 로컬 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
current candidate: 74bf5ea15f37f1479feb7d3da10a42359e98dc9b
```

핵심 변경:

```text
KiwoomRequestBridge
-> KIWOOM_MODE=mock|real
-> KIWOOM_APPKEY
-> KIWOOM_SECRETKEY
-> existing kiwoom-auto env contract 사용

chart.html?manager=1
-> normal MarketChartWorkspace 그대로 사용
-> normal Chart persistence 그대로 사용
-> actual Kiwoom market-data path 그대로 사용
-> Strategy Manager Dialog만 자동 open
```

앞서 잘못 넣은 `manager=1 -> clean add-on state / Kiwoom 우회` 방향은 원복했다.

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

### B. Kiwoom env contract drift

사용자 evidence:

```text
ERROR · Kiwoom proxy HTTP 502:
KIWOOM_MOCK_APP_KEY is required.
```

실제 원인:

```text
kiwoom-auto .env
-> KIWOOM_MODE / KIWOOM_APPKEY / KIWOOM_SECRETKEY

Chart bridge
-> 다른 이름의 KIWOOM_MOCK_* / KIWOOM_REAL_*만 요구

결과: existing valid key를 process가 못 찾음
```

교정:

```text
existing kiwoom-auto .env contract를 Chart bridge authority로 복원
launcher가 kiwoom-auto directory를 KIWOOM_ENV_DIR로 전달
Base Chart는 실제 Kiwoom REST 데이터를 계속 사용
```

## 6. 지금 바로 할 일 — 화면 재검증

두 workspace 최신 remote만 받은 뒤 launcher **한 번 실행**한다. 별도 Stop 단계는 필요 없다.

```text
http://127.0.0.1:5174/chart.html?manager=1
```

화면 acceptance:

```text
1. Kiwoom key missing 502 없음
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
