# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / THREE-AXIS TRANSITION + EXTERNAL-LLM AUTHORING + CONTINUOUS-IMPROVEMENT / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다.

최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` branch 상태가 stale 문서보다 우선한다.

---

## 1. 새 세션 복구 순서

반드시 다음 순서로 현재 권한을 복구한다.

```text
1. SESSION_HANDOFF.md
2. THREE_AXIS_TRANSITION_CHECKPOINT_2026-08-31.md
3. DSL_FROZEN_CORE_MIGRATION_POLICY.md
4. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
5. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
6. DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
7. DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
8. DSL_THREE_AXIS_FINAL_TARGET.md
9. DSL_THREE_AXIS_MODULE_BOUNDARY.md
10. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
11. CURRENT_STATE.md
12. current `dsl-live-studio` branch/head
```

사용자가 `세션이어가!`, `세션복구`, `계속` 등 같은 의미로 말하면 위 문서를 읽고 사용자에게 이미 확정된 내용을 다시 설명하도록 요구하지 않는다.

첫 복구 응답은 짧게 다음만 제시한다.

```text
현재 단계
한 일
할 일
금지사항 / 검증상태
```

---

## 2. 절대 보존 — frozen legacy Core

기존 검증 DSL Core는 이제 migration source가 아니라 **영구 read-only golden reference**다.

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

중요:

```text
legacy core 수정 중단 != DSL 기능 개발 중단
```

DSL 고유 기능 개발은 새 AXIS 1에서 계속한다.

---

## 3. 새 3축 물리 구조

현재 새 개발 root:

```text
axes/
  axis1_dsl/
  axis2_selection/
  axis3_monetization/

bridges/
  contracts/
```

현재는 권한/README/contract scaffold 단계이며 기존 Core 전체를 대규모 복사하지 않았다.

세 축 사이 원칙:

```text
각 축 독립 개발 / 독립 테스트
직접 내부 import 금지
내부 DB/state 직접 참조 금지
상호연동은 versioned Request -> Response Bridge만 허용
```

권한:

```text
AXIS 1 = DSL Capability Engine
AXIS 2 = point-in-time cross-sectional selection
AXIS 3 = Condition/Strategy CRUD + monetization/orchestration
Chart  = 계산 없이 projection/evidence 표시
```

---

## 4. AXIS 1 — DSL Capability Engine

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

Broader repository status는 계속:

```text
REMEDIATION_REQUIRED
```

### 현재 주요 AXIS 1 backlog

코드/기존 audit로 확인된 우선 보완 대상:

```text
TOP: tuple / multi-output typed return + destructuring
user-defined functions
bounded loops
on_tick / on_fill rollback/commit lifecycle
partial fills / partial exits
pyramiding / multi-position accounting
full TA-Lib/reference differential fixtures
capability metadata completeness
full-engine batch/streaming parity
generic chart projection completeness
```

특히 `CoreTALib.bbands()` / `supertrend()`처럼 내부 함수가 여러 값을 반환하는 경우가 있어도 현재 DSL Registry/Semantic/Assignment에는 일반 tuple/destructuring contract가 없다.

3축 migration 때문에 이 기능들이 장기간 보류되어서는 안 된다.

순서:

```text
현재 capability audit 확정
 -> 새 AXIS 1에 boundary 단위 이식
 -> frozen Core parity
 -> migration checkpoint
 -> tuple/multi-output부터 신규 DSL 기능 개발
```

---

## 5. AXIS 2 — 사전계산 snapshot 기반 종목선별

시장레짐/다중종목 비교를 Instrument DSL Runtime에 밀어 넣지 않는다.

기존 provider 원칙:

```text
precompute
 -> immutable point-in-time as_of snapshot
 -> AXIS 2 filter/rank/top-N
 -> CandidateSetResponse + evidence
```

개발대상:

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

AXIS 1은 필요 시 이 결과 중 일부를 등록된 read-only `ctx.*` 또는 execution input으로 소비할 뿐이다.

AXIS 1이 universe를 검색하거나 peer 종목을 실시간 비교/랭킹하지 않는다.

---

## 6. AXIS 3 — Strategy / Condition Monetization

AXIS 3 책임:

```text
Condition CRUD
Strategy CRUD
Baseline 보존
strategy lineage/version
Candidate Set -> strategy 선택
AXIS 1 execution request 조립
backtest/chart/validation 결과 연결
compare / promote / reject / archive
```

분리:

```text
Feature Catalog = DSL 기능검증 SSOT / 불변
Condition CRUD  = 종목선별 규칙 / 버전
Strategy CRUD   = 수익전략 / 버전 / 비교 / 폐기
```

기본 Baseline:

```text
MACD_BASELINE_V1 [불변]
```

---

## 7. 최종 사용자 목표 — 자연어 한 문장으로 선별부터 매매까지

최종 제품은 사용자가 자연어로 종목선별 + 전략 + 리스크/청산까지 요청할 수 있어야 한다.

대표 목표 예:

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
= 최근 breakout / reference strength / re-breakout / cross-sectional selection

AXIS 3
= 선택된 후보에 적용할 Strategy version + reference/context orchestration

AXIS 1
= 15m single-symbol deterministic entry/exit/risk execution
```

최근 사용자 화면에서는 15분 차트에 1m DSL이 남아 있어 timeframe mismatch 오류가 확인됐다.
이 사례는 전략/차트 timeframe authority가 request/compile 단계에서 정확히 일치해야 함을 보여주는 evidence다.
특정 timeframe 예외를 Core에 넣어 해결하지 않는다.

---

## 8. External LLM Authoring Lane — 자연어 완전파서를 직접 만들지 않는다

자연어 금융 의미를 우리 로컬 NLP가 완전히 이해/검증하는 범용 엔진을 만들지 않는다.

외부 LLM을 **untrusted strategy proposal generator**로 사용하고 사람이 매개할 수 있다.

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

Repo-local external authoring skill:

```text
skills/external_llm_strategy_authoring/SKILL.md
```

외부 LLM structured response contract:

```text
authoring/contracts/external_strategy_draft.v1.schema.json
schema_version = external_strategy_draft/v1
```

Skill에 포함:

```text
DSL syntax
supported capability
unsupported capability
available data sources
AXIS 2 precomputed feature boundary
ctx.* binding rules
timeframe/causality
strict return schema
do-not-invent rules
correction protocol
```

중요:

```text
SKILL.md != execution SSOT
```

궁극적으로 Skill/Prompt material은 machine registries/contracts/error catalog에서 생성한다.

외부 LLM이 미구현 기능을 필요로 하면 문법을 창작하지 않는다.

```text
needs_capability = [...]
 -> BLOCKED_NEEDS_CAPABILITY
 -> 적절한 AXIS backlog
```

---

## 9. Local deterministic validation pipeline

외부 LLM 출력은 다음 순서로 fail-closed 검증한다.

```text
V1 structured response schema
 -> V2 capability IDs
 -> V3 data-source / feature IDs
 -> V4 AXIS boundary
 -> V5 timeframe / causality
 -> V6 DSLParser
 -> V7 DSLSemanticAnalyzer
 -> V8 compile / dry-run
 -> V9 Condition/Strategy persistence validation
 -> ACCEPTED_DRAFT
```

오류를 assertion 완화, compatibility exception, source surgery로 숨기지 않는다.

실패는 먼저 분류한다.

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

---

## 10. 지속개선 루프 — 이 시스템의 핵심 강점

시스템 완성 후에도 Prompt / Skill / DSL / Data contract를 지속 보완할 수 있어야 한다.

**LLM 반환 오류는 버리지 않고 구조화 evidence로 누적한다.**

Validation event contract:

```text
authoring/contracts/authoring_validation_event.v1.schema.json
```

기록 대상:

```text
request_id / draft_id / iteration
user intent fingerprint
skill version
prompt version
validator version
validation stage
error code / diagnostic
capability/data-source identity
root-cause classification
correction result
final acceptance state
```

운영 루프:

```text
LLM draft
 -> deterministic validation
 -> validation event logging
 -> evidence accumulation
 -> periodic aggregate review
 -> root-cause classification
 -> Prompt / Skill / DSL / Data contract 중 가장 좁은 원인 개선
 -> focused tests
 -> regression
 -> version bump / promotion
 -> 개선 전후 지표 비교
```

절대 금지:

```text
오류 빈도가 높다고 Parser 자동 완화
Prompt 자동 self-modification
Skill 자동 덮어쓰기
LLM 결과에 맞춘 validation bypass
legacy frozen core 수정
```

개선은 항상:

```text
evidence
 -> human/developer review
 -> micro-tranche
 -> automated verification
 -> promotion
```

순서다.

대표 품질지표:

```text
first-pass acceptance rate
mean correction iterations
schema failure rate
Parser failure rate
Semantic failure rate
unsupported capability rate
intent ambiguity rate
repeat-error rate after correction
Prompt/Skill version별 acceptance rate
```

같은 오류가 반복되면 먼저 다음을 구분한다.

```text
LLM이 기존 문법을 자주 오해하는가?
Prompt 설명이 부족한가?
Skill 예제가 부족한가?
Validator diagnostic이 부족한가?
DSL 표현력이 실제 부족한가?
Data/feature contract가 부족한가?
```

이 분류 없이 Parser나 Core를 바꾸지 않는다.

핵심 문장:

> **사용할수록 자연어 작성 정확도와 DSL 표현력은 함께 향상되지만, 실행 권한과 검증 기준은 절대로 흐려지지 않는다.**

---

## 11. Chart / observability 원칙

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

## 12. 현재 병행 개발 Track

```text
Track A — AXIS 1
1. 잔여 capability exact audit
2. migration manifest
3. 첫 boundary 1개 이식 + frozen parity
4. tuple/multi-output 우선 신규 개발
5. 이후 DSL backlog micro-tranche

Track B — AXIS 2
1. precomputed snapshot schema v1
2. market/sector/beta/histogram point-in-time evidence
3. generic filter/rank/top-N
4. CandidateSetResponse v1

Track C — AXIS 3
1. Condition CRUD / Strategy CRUD physical separation
2. version/lineage
3. Candidate Set -> AXIS 1 execution orchestration

Track D — External LLM Authoring
1. SKILL.md v1 [DONE]
2. external_strategy_draft/v1 schema [DONE]
3. continuous-improvement policy [DONE]
4. authoring_validation_event/v1 schema [DONE]
5. Prompt Builder
6. response ingest/schema validator
7. capability/data-source validator
8. DSL Parser/Semantic validator adapter
9. Correction Prompt Builder
10. human-mediated iteration workflow
11. validation event logger + periodic aggregate report
12. generated Skill/Prompt from machine registries
```

각 Track은 독립 병행 가능하지만 각 Track 내부 작업은 micro-tranche로 진행한다.

AXIS 1 migration 완료를 기다린다는 이유로 DSL 기능개발을 장기 중단하지 않는다.
AXIS 2 구현 완료를 기다린다는 이유로 Authoring Lane을 중단하지 않는다.

---

## 13. 다음 세션의 즉시 작업

새 세션에서 무작정 전략코드나 대규모 migration부터 시작하지 않는다.

현재 우선순위:

```text
A1. AXIS 1 잔여 exact audit 완료
    - JMA up/down/normalized slope direct access
    - projection completeness
    - Strategy CRUD separation

A2. AXIS 1 migration manifest 작성

A3. 첫 migration boundary 1개만 이식 + frozen parity

D1. Prompt Builder contract/implementation 시작 가능
    - 현재 machine capability/data-source snapshot을 입력으로 사용
    - 외부 LLM 반환은 strict draft schema 사용
    - validation event logger를 처음부터 같이 설계

B1. AXIS 2 precomputed snapshot schema v1은 독립 병행 가능
```

대규모 전체 `core/` 복사는 금지한다.

---

## 14. 검증/상태 표현 규칙

현재 상태:

```text
frozen legacy core: ESTABLISHED / source immutable by policy
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

새 executable 변경은 사용자 local PASS가 없으면 `REMOTE_UNVALIDATED`로 표시한다.

부분 PASS를 다음으로 과장하지 않는다.

```text
3축 전체 완료
자연어 전략작성 완료
실전 수익성 검증 완료
live trading readiness
repository-wide compliance PASS
```

---

## 15. 금지사항

```text
frozen core 수정
특정 종목/venue/timeframe/전략 예외를 Core에 추가
Feature Catalog baseline을 전략 연구로 수정
Chart에서 indicator/selection 재계산
AXIS 간 내부 구현 직접 참조
LLM output을 validation 없이 실행
LLM이 발명한 capability/data source 자동 등록
실패 assertion 완화
반복오류를 근거 없이 Parser 완화로 해결
Prompt/Skill/Core 자동 self-modification
synthetic fixture를 실전 수익성 근거로 사용
후보 threshold를 검증된 최적값으로 단정
```

---

## 16. `세션이어가!` 행동 규칙

사용자가 새 세션에서 세션 복구를 요청하면:

```text
1. 위 권한문서를 읽는다.
2. current `dsl-live-studio` HEAD를 확인한다.
3. frozen Core 무변경을 전제로 한다.
4. 기존 결정사항을 사용자에게 다시 묻지 않는다.
5. 한 일 / 할 일을 분리해 짧게 복구한다.
6. 이 문서의 13번 즉시 작업부터 이어간다.
7. 코딩 전에 해당 micro-tranche의 실제 코드/테스트 상태를 audit한다.
8. 실패는 원인분류 후 수정하며 assertion/원칙을 약화하지 않는다.
```

이 문서가 다음 세션의 첫 복구 authority다.
