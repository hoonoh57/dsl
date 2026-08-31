# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / THREE-AXIS TRANSITION / EXTERNAL-LLM AUTHORING / CONTINUOUS-IMPROVEMENT / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다.

최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` branch 상태가 stale 문서보다 우선한다.

가장 중요한 최신 운영 결정:

> **중요한 방침은 즉시 문서에 반영한다. 그러나 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호 순서를 절대로 건너뛰지 않는다.**

좋은 새 아이디어가 생겨도 현재 Step이 완료되기 전에는 구현하지 않고 PARKING LOT에 기록한다.

---

## 1. 새 세션 복구 순서

반드시 다음 순서로 읽는다.

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. THREE_AXIS_TRANSITION_CHECKPOINT_2026-08-31.md
4. DSL_FROZEN_CORE_MIGRATION_POLICY.md
5. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
6. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
7. DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
8. DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
9. DSL_THREE_AXIS_FINAL_TARGET.md
10. DSL_THREE_AXIS_MODULE_BOUNDARY.md
11. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
12. CURRENT_STATE.md
13. current `dsl-live-studio` branch/head
```

사용자가 `세션이어가!`, `세션복구`, `계속` 등 같은 의미로 말하면 이미 확정된 내용을 다시 사용자에게 설명하도록 요구하지 않는다.

첫 복구 응답은 짧게:

```text
현재 Step
한 일
할 일
금지사항 / 검증상태
```

만 제시하고 현재 Step부터 이어간다.

---

## 2. 작업순서 SSOT — 반드시 번호대로 진행

실행순서 authority:

```text
DSL_NEXT_WORK_ORDER.md
```

현재 포인터:

```text
CURRENT_STEP = 1
CURRENT_STEP_NAME = AXIS 1 잔여 exact capability audit 완료
```

원칙:

```text
현재 Step 수행
 -> automated verification
 -> 필요 시 user-local PASS
 -> 관련 authority 갱신
 -> SESSION_HANDOFF 갱신
 -> checkpoint
 -> CURRENT_STEP + 1
```

금지:

```text
흥미로운 새 기능 때문에 다음 Step 선행
여러 Track을 동시에 벌려놓기
현재 Step의 실패를 덮고 다음 Step 진행
작업 후 문서 갱신을 나중으로 미루기
```

새 아이디어는 버리지 않는다.

```text
새 아이디어
 -> PARKING LOT 기록
 -> 관련 미래 Step 연결
 -> 현재 Step 계속
```

작업순서를 변경하려면 사용자의 명시적 결정이 먼저 있어야 하며, **코드 변경 전에 `DSL_NEXT_WORK_ORDER.md`를 먼저 수정한다.**

---

## 3. 절대 보존 — frozen legacy Core

기존 검증 DSL Core는 **영구 read-only golden reference**다.

```text
path:          core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree:     8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정
core/ 이동
core/ 삭제
core/ 신규 파일 추가
새 기능을 legacy core/에 역이식
새 3축 구현이 legacy core 내부 객체에 영구 의존
```

허용:

```text
읽기
기존 regression
새 AXIS 1과 golden parity 비교
migration source reference
```

자동 guard:

```text
tests/test_frozen_legacy_core_guard.py
```

아직 이 guard의 **user-local 실행 PASS는 보고되지 않았다.**

핵심:

```text
legacy core 수정 중단 != DSL 기능 개발 중단
```

DSL 고유 기능 개발은 새 AXIS 1에서 계속한다.

---

## 4. 새 3축 물리 구조와 권한

개발 root:

```text
axes/
  axis1_dsl/
  axis2_selection/
  axis3_monetization/

bridges/
  contracts/
```

현재는 scaffold/authority 단계이며 기존 Core 전체를 대규모 복사하지 않았다.

축 사이 원칙:

```text
각 축 독립 개발 / 독립 테스트
직접 내부 import 금지
내부 DB/state 직접 참조 금지
상호연동은 versioned Request -> Response Bridge만 허용
```

권한:

```text
AXIS 1 = DSL Capability Engine
AXIS 2 = precomputed point-in-time cross-sectional selection
AXIS 3 = Condition/Strategy CRUD + monetization/orchestration
Chart  = 계산 없이 projection/evidence 표시
```

---

## 5. AXIS 1 — 현재 상태와 최우선 backlog

새 기능 개발 위치:

```text
axes/axis1_dsl/
```

기존 구현 중 신뢰된 핵심:

```text
fail-closed Parser/AST
scalar/series/bool/string semantic type
arithmetic/comparison/boolean
history reference
state + on_bar + nested if/else
confirmed-bar MTF
parent context read-only binding
MARKET/LIMIT/STOP/STOP_LIMIT/OCO/DAY broker lifecycle
bar_close / next_open execution policies
user.macd_normalized
session.day_return_pct
```

기존 trusted checkpoint:

```text
registered feature catalog       75 / 75 PASS
registered execution invariants  23 / 23 PASS
Live Studio direct-Core path     TRUSTED
v2 + v3 + v4 invariant UI        TRUSTED
DSL Core Phase 1                 TRUSTED
```

Broader repository status:

```text
REMEDIATION_REQUIRED
```

현재 주요 AXIS 1 backlog:

```text
TOP: tuple / multi-output typed return + destructuring
generic projection contract
capability/function metadata completeness
user-defined functions
bounded loops
on_tick / on_fill rollback/commit lifecycle
partial fills / partial exits
pyramiding / multi-position accounting
full TA-Lib/reference differential fixtures
full-engine batch/streaming parity
```

특히 내부 indicator가 여러 값을 만들더라도 현재 DSL Registry/Semantic/Assignment에는 일반 tuple/destructuring contract가 없다.

단, 신규 기능 개발은 **Step 4 migration parity가 끝난 뒤 Step 5에서 위 순서대로** 진행한다.

---

## 6. AXIS 2 — 사전계산 snapshot 기반 종목선별

시장레짐/다중종목 비교를 Instrument DSL Runtime에 밀어 넣지 않는다.

```text
precompute
 -> immutable point-in-time as_of snapshot
 -> AXIS 2 filter/rank/top-N
 -> CandidateSetResponse + evidence
```

필수 개발대상:

```text
market regime snapshot
beta / high-beta universe snapshot
sector strength + historical constituent snapshot
normalized MACD Histogram per-symbol snapshot
high-beta universe Histogram rank/top-N
leading-sector constituent Histogram rank/top-N
relative strength
turnover / capital-flow
leader/follower bounded evidence
generic Condition CRUD
historical point-in-time replay validation
```

예:

```text
고베타 종목군
 + 동일 as_of normalized Histogram
 -> rank
 -> top-N

상위 주도섹터
 + 당시 constituent snapshot
 + 종목별 normalized Histogram
 -> sector 내부 rank
 -> top-N
```

AXIS 1은 필요 시 결과 일부를 등록된 read-only `ctx.*`/execution input으로 소비할 뿐 universe 탐색/peer ranking을 하지 않는다.

---

## 7. AXIS 3 — Strategy / Condition Monetization

책임:

```text
Condition CRUD
Strategy CRUD
Baseline 보존
strategy lineage/version
Candidate Set -> strategy 선택
AXIS 1 execution request 조립
backtest/chart/validation 연결
compare / promote / reject / archive
```

분리:

```text
Feature Catalog = DSL 기능검증 SSOT / 불변
Condition CRUD  = 종목선별 규칙 / 버전
Strategy CRUD   = 수익전략 / 버전 / 비교 / 폐기
```

Baseline:

```text
MACD_BASELINE_V1 [불변]
```

---

## 8. 최종 사용자 목표 — 자연어 한 문장으로 선별부터 매매까지

대표 목표:

```text
최근 10일 이내 EMA120을 돌파하면서 normalized/new MACD Histogram 강도가 기준 이상이었던 종목 중,
현재 동일 강도 이상으로 EMA120을 재돌파하는 종목을 고르고,
15분봉에서 종가가 EMA120 이상이고 Histogram이 기준봉 이상이며
MACD 상향돌파 또는 JMA 상승전환 시 매수,
JMA 하락전환 시 매도하되 일정 수익 이전이고 EMA120 위면 매도 금지,
수익 확보 후 JMA 하락전환이면 매도.
```

책임 분해:

```text
AXIS 2
= 과거 breakout/reference strength/re-breakout/cross-sectional selection

AXIS 3
= 선택된 후보에 적용할 Strategy version + reference/context orchestration

AXIS 1
= 15m single-symbol deterministic entry/exit/risk execution
```

최근 사용자 화면에서 15분 차트에 1m DSL이 남아 timeframe mismatch 오류가 확인됐다.
이는 request/strategy/chart timeframe authority를 정확히 연결해야 한다는 evidence다.
특정 timeframe 예외를 Core에 넣어 해결하지 않는다.

---

## 9. External LLM Authoring Lane

자연어 금융 의미 전체를 로컬 범용 NLP로 완전 파싱하려 하지 않는다.

외부 LLM은 **untrusted strategy proposal generator**다.

```text
User natural language
 -> Local Prompt Builder
 -> Human -> External LLM
 -> strict Structured Strategy Draft
 -> Local deterministic validation
       |
       +-- PASS -> Condition/Strategy draft
       |
       +-- FAIL -> Correction Prompt Builder
                     -> Human -> External LLM
                     -> corrected draft
                     -> validation repeat
```

권한:

```text
External LLM = proposal only
Human        = mediation / intent confirmation
Local system = deterministic acceptance/rejection authority
AXIS 2       = selection authority
AXIS 3       = persistence/orchestration authority
AXIS 1       = compile/runtime/backtest/broker authority
```

Repo-local Skill:

```text
skills/external_llm_strategy_authoring/SKILL.md
```

Structured response:

```text
authoring/contracts/external_strategy_draft.v1.schema.json
schema_version = external_strategy_draft/v1
```

Skill은 execution SSOT가 아니다.
궁극적으로 machine capability/data-source/Bridge/error registry에서 생성한다.

미구현 기능 필요 시 외부 LLM이 문법을 발명하지 않고:

```text
needs_capability = [...]
 -> BLOCKED_NEEDS_CAPABILITY
```

로 반환한다.

---

## 10. Local deterministic validation + 지속개선

외부 LLM 결과 검증:

```text
V1 schema
 -> V2 capability IDs
 -> V3 data-source / feature IDs
 -> V4 AXIS boundary
 -> V5 timeframe / causality
 -> V6 DSLParser
 -> V7 DSLSemanticAnalyzer
 -> V8 compile / dry-run
 -> V9 Condition/Strategy persistence
 -> ACCEPTED_DRAFT
```

오류 원인분류:

```text
test defect
product defect
prompt defect
skill gap
LLM draft defect
DSL parser gap
DSL capability gap
data-contract gap
user-intent ambiguity
authority drift
environment issue
unknown
```

Validation event contract:

```text
authoring/contracts/authoring_validation_event.v1.schema.json
```

지속개선 루프:

```text
LLM draft
 -> deterministic validation
 -> structured event logging
 -> evidence accumulation
 -> periodic aggregate review
 -> root-cause classification
 -> 가장 좁은 원인 개선
 -> focused tests
 -> regression
 -> version promotion
 -> 개선 전후 비교
```

대표 지표:

```text
first-pass acceptance rate
mean correction iterations
schema/Parser/Semantic failure rate
unsupported capability rate
intent ambiguity rate
repeat-error rate
Prompt/Skill version별 acceptance rate
```

절대 금지:

```text
Parser 자동 완화
Prompt/Skill 자동 self-modification
LLM output에 맞춘 validation bypass
legacy frozen core 수정
```

핵심:

> **사용할수록 자연어 작성 정확도와 DSL 표현력은 함께 향상되지만, 실행 권한과 검증 기준은 흐려지지 않는다.**

---

## 11. Chart / observability

Chart는 계산기가 아니라 전략개발 계측기다.

```text
Selector evidence
MACD / Signal / Histogram
normalized Histogram
JMA strength
position/context
reference threshold
required threshold
permission
trigger
BUY / SELL
```

을 계산한 축에서 projection으로 받아 표시한다.

Chart가 indicator/selection/strategy 계산을 재구현하지 않는다.

---

## 12. 앞으로 반드시 이 순서로 진행

상세 acceptance/완료조건은 `DSL_NEXT_WORK_ORDER.md`가 권한이다.

```text
1. AXIS 1 잔여 exact capability audit
2. AXIS 1 migration manifest + boundary 순서
3. Frozen Core 보호 gate PASS
4. AXIS 1 boundary-by-boundary migration + parity
5. AXIS 1 신규 DSL 기능 개발
   - tuple/multi-output부터 고정 순서
6. AXIS 1 machine-readable registry / diagnostics
7. Bridge common + AXIS 1 execution contract v1
8. AXIS 2 precomputed snapshot contract v1
9. AXIS 2 generic selection + 핵심 market/sector/beta/hist ranking
10. AXIS 3 Condition/Strategy CRUD + orchestration
11. AXIS 2 -> AXIS 3 -> AXIS 1 E2E Bridge
12. External LLM Authoring workflow 구현
13. Continuous Improvement 분석/개선 도구
14. 최종 자연어 E2E acceptance scenario
15. Legacy docs disposition + broader compliance audit
```

**동시 병행 실행하지 않는다.**

아이디어는 PARKING LOT에 넣고 현재 Step을 끝낸다.

---

## 13. 현재 상태

```text
CURRENT_STEP: 1

frozen legacy core: ESTABLISHED / immutable by policy
frozen guard: ADDED / user-local PASS not yet reported
new three-axis roots: ESTABLISHED
AXIS 1 migration: NOT STARTED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
Bridge v1: design pending
External LLM authoring policy: ESTABLISHED
External LLM skill v1: ADDED
external_strategy_draft/v1 schema: ADDED
continuous improvement policy: ESTABLISHED
authoring_validation_event/v1 schema: ADDED
Prompt Builder / ingest / correction workflow: NOT IMPLEMENTED
repository-wide compliance: REMEDIATION_REQUIRED
```

새 executable 변경은 사용자 local PASS가 없으면 `REMOTE_UNVALIDATED`다.

부분 PASS를 다음으로 과장하지 않는다.

```text
3축 전체 완료
자연어 전략작성 완료
실전 수익성 검증 완료
live trading readiness
repository-wide compliance PASS
```

---

## 14. 중요 방침/로직 변경 문서화 규칙

앞으로 다음이 발생하면 **그 턴에서 바로 문서 갱신**한다.

```text
architecture authority 변경
AXIS 책임 변경
DSL 문법/실행 의미 변경
데이터소스/causality 변경
Bridge contract 변경
검증 기준 변경
외부 LLM protocol 변경
지속개선 분류/정책 변경
작업순서 변경
중요 backlog/우선순위 변경
```

최소 갱신:

```text
관련 authority 문서
DSL_NEXT_WORK_ORDER.md (현재 Step/순서 영향 시)
SESSION_HANDOFF.md
```

**작업만 진행하고 세션 문서를 나중에 정리하는 방식은 금지한다.**

---

## 15. 금지사항

```text
frozen core 수정
현재 Step 건너뛰기
여러 미래 Step 동시 구현
특정 종목/venue/timeframe/전략 예외를 Core에 추가
Feature Catalog baseline을 전략 연구로 수정
Chart에서 indicator/selection 재계산
AXIS 간 내부 구현 직접 참조
LLM output을 validation 없이 실행
LLM이 발명한 capability/data source 자동 등록
실패 assertion 완화
근거 없이 Parser 완화
Prompt/Skill/Core 자동 self-modification
synthetic fixture를 실전 수익성 근거로 사용
후보 threshold를 검증된 최적값으로 단정
```

---

## 16. `세션이어가!` 행동 규칙

새 세션 복구 요청 시:

```text
1. 위 복구 authority 순서대로 읽는다.
2. current `dsl-live-studio` HEAD를 확인한다.
3. `DSL_NEXT_WORK_ORDER.md`의 CURRENT_STEP을 확인한다.
4. frozen Core 무변경을 전제로 한다.
5. 기존 결정을 사용자에게 다시 묻지 않는다.
6. 한 일 / 할 일을 분리해 짧게 복구한다.
7. CURRENT_STEP 외의 구현을 시작하지 않는다.
8. 코딩 전에 해당 Step의 실제 코드/테스트 상태를 audit한다.
9. 실패는 원인분류 후 수정하며 원칙/assertion을 약화하지 않는다.
10. Step 완료 시 문서/checkpoint/current pointer를 함께 갱신한다.
```

이 문서와 `DSL_NEXT_WORK_ORDER.md`가 다음 세션의 첫 실행 authority다.
