# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 **작업 순서 SSOT**다.

새로운 좋은 아이디어가 생겨도 현재 번호를 건너뛰어 구현하지 않는다.

```text
아이디어 발생
 -> 중요 방침이면 authority/session 문서 즉시 반영
 -> 구현 아이디어면 PARKING LOT에 기록
 -> 현재 번호 완료
 -> automated verification / user-local verification if required
 -> checkpoint
 -> 다음 번호로 이동
```

핵심 원칙:

> **방침은 즉시 기록하되, 구현 순서는 임의로 바꾸지 않는다.**

> **현재 번호가 끝나기 전에는 다음 번호를 실행하지 않는다.**

명시적 사용자 결정으로 순서가 변경되는 경우에만 이 문서를 먼저 갱신한 뒤 새 순서로 이동한다.

---

## 0. 현재 포인터

```text
CURRENT_STEP = 1
CURRENT_STEP_NAME = AXIS 1 잔여 exact capability audit 완료
```

현재 작업이 완료될 때마다 반드시:

```text
1. 결과 기록
2. PASS/FAIL 및 원인분류
3. 관련 authority 문서 갱신
4. SESSION_HANDOFF.md 갱신
5. CURRENT_STEP을 다음 번호로 이동
```

한다.

---

## 1. AXIS 1 잔여 exact capability audit 완료

**아직 코드를 이식하거나 신규 기능을 개발하지 않는다.**

확정할 항목:

```text
1-1. JMA up/down 값 direct strategy access
1-2. JMA normalized slope strength direct access
1-3. intermediate/threshold/permission/marker projection completeness
1-4. Strategy CRUD와 Feature Catalog 실제 물리/저장 경계
1-5. 기존 capability audit의 IMPLEMENTED / PARTIAL / NOT_IMPLEMENTED 판정 재확인
```

출력:

```text
DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md 최종판
```

완료 조건:

```text
각 항목이 코드/테스트 evidence를 가진다.
미구현과 검증부족을 구분한다.
구형 core/는 변경하지 않는다.
```

---

## 2. AXIS 1 migration manifest 및 이식 경계 순서 확정

현재 frozen `core/`의 각 책임을 새 `axes/axis1_dsl/`의 어디로 이식할지 mapping한다.

최소 분류:

```text
Parser / AST
Semantic / type
function/capability registry
indicator computation
state / bar runtime
MTF / parent context
execution / Backtest
Broker / accounting
projection / diagnostics
```

각 항목에:

```text
source path
new target path
copy-as-is / refactor-during-migration 여부
parity test
known legacy defect 여부
migration dependency order
```

를 명시한다.

완료 조건:

```text
전체 복사 금지
첫 migration boundary가 정확히 결정됨
각 boundary의 parity test가 정의됨
```

---

## 3. Frozen Core 보호 gate 검증

첫 실제 migration write 전에 frozen reference를 다시 잠근다.

기준:

```text
legacy path: core/
freeze tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

필수:

```text
tests/test_frozen_legacy_core_guard.py
```

user-local PASS가 필요한 executable/static guard는 PASS evidence를 받은 뒤 migration checkpoint로 기록한다.

완료 조건:

```text
frozen core tree unchanged
freeze guard PASS evidence
```

---

## 4. AXIS 1 boundary-by-boundary migration + full parity

Step 2에서 정한 경계 순서대로 **한 boundary씩만** 이식한다.

각 boundary 반복:

```text
이식
 -> focused automated parity
 -> frozen-core comparison
 -> defect classification
 -> regression
 -> checkpoint
 -> 다음 boundary
```

금지:

```text
전체 core/ 일괄 복사
migration 중 기능 추가를 섞기
parity 차이를 compatibility exception으로 숨기기
legacy core 수정
```

완료 조건:

```text
새 AXIS 1이 기존 trusted behavior를 재현
Feature Catalog baseline parity
execution invariant parity
Parser/Semantic/Runtime parity
Backtest/Broker parity
MTF/context parity
projection parity
```

이 시점에만 새 AXIS 1을 **migration-parity trusted**로 부를 수 있다.

---

## 5. AXIS 1 신규 DSL 기능 최우선 개발

3축 전환 때문에 DSL 고유 기능을 더 이상 보류하지 않는다.

아래 **내부 순서도 고정**한다.

```text
5-1. tuple / multi-output typed return + destructuring
5-2. tuple 포함 generic projection contract
5-3. capability/function metadata completeness
5-4. user-defined functions
5-5. bounded loops
5-6. on_tick / on_fill commit/rollback semantics
5-7. partial fills / partial exits
5-8. pyramiding / multi-position accounting
5-9. full TA-Lib/reference differential fixtures
5-10. full-engine batch/streaming parity
```

각 기능은 별도 micro-tranche + focused tests + AXIS 1 regression을 가진다.

특정 전략을 위해 문법을 하드코딩하지 않는다.

---

## 6. AXIS 1 machine-readable registry / diagnostics authority 확정

외부 LLM Skill/Prompt와 Bridge가 수동 문서에 의존하지 않도록 machine SSOT를 만든다.

필수:

```text
capability IDs
function signatures
input/output types
multi-output arity/types
lookback / causality metadata
supported/unsupported status
stable diagnostic/error codes
projection capabilities
```

완료 조건:

```text
Skill/Prompt 생성에 사용할 수 있는 registry snapshot 존재
Parser/Semantic/Runtime과 registry drift 자동검사 존재
```

---

## 7. Bridge common + AXIS 1 execution contract v1

먼저 표준 envelope와 AXIS 1 실행 계약을 고정한다.

```text
three_axis.common/v1
axis1.execution/v1
```

포함:

```text
request identity
schema version
as_of / timeframe / causality
strategy identity
context refs
execution result
orders/fills/trades
indicator/intermediate/threshold/permission series
markers
provenance / diagnostics
```

Bridge는 계산하지 않는다.

---

## 8. AXIS 2 precomputed point-in-time snapshot contract v1

시장레짐/다중종목 비교는 DSL Runtime이 아니라 사전계산 snapshot으로 제공한다.

먼저 데이터 계약을 만든다.

필수 feature family:

```text
market regime
beta / high-beta universe
sector strength
historical sector constituents
normalized MACD Histogram per symbol
relative strength
turnover / capital-flow
leader/follower bounded evidence
```

필수 원칙:

```text
exact as_of
point-in-time reproducibility
no future membership
no nearest-time guessing
provenance
```

---

## 9. AXIS 2 generic selection engine + 핵심 선별기능

계약 후 엔진을 만든다.

순서:

```text
9-1. generic universe input
9-2. filter
9-3. rank
9-4. top-N
9-5. evidence/reasons
9-6. Condition CRUD
9-7. CandidateSetResponse v1
9-8. market-regime selection
9-9. high-beta universe ranking
9-10. leading-sector member ranking
9-11. normalized Histogram cross-sectional rank
9-12. historical replay validation
```

대표 목표:

```text
고베타 종목군 -> Histogram rank/top-N
주도섹터 구성종목 -> Histogram rank/top-N
```

---

## 10. AXIS 3 Condition / Strategy CRUD + monetization orchestration

구현 순서:

```text
10-1. Condition CRUD physical persistence
10-2. Strategy CRUD physical persistence
10-3. immutable baseline identity
10-4. strategy parent/version/lineage
10-5. Candidate Set -> Strategy selection
10-6. AXIS 1 execution request assembly
10-7. comparison / promote / reject / archive
```

Feature Catalog와 완전 분리한다.

---

## 11. AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge

최종 기본 흐름을 deterministic하게 연결한다.

```text
SelectionRequest
 -> AXIS 2
 -> CandidateSetResponse
 -> AXIS 3
 -> StrategyExecutionRequest
 -> AXIS 1
 -> ExecutionResponse + projections
 -> AXIS 3 validation/comparison
```

완료 조건:

```text
축 간 내부 import 없음
versioned request/response only
request_id/provenance 추적 가능
Chart 재계산 없음
```

---

## 12. External LLM Authoring Lane 구현

기존 정책/Skill/schema를 실제 workflow로 연결한다.

현재 완료:

```text
SKILL.md v1
external_strategy_draft/v1 schema
authoring_validation_event/v1 schema
continuous-improvement policy
```

남은 구현 순서:

```text
12-1. Prompt Builder
12-2. external draft ingest/schema validator
12-3. capability/data-source validator
12-4. AXIS boundary/timeframe/causality validator
12-5. AXIS 1 Parser/Semantic/dry-run adapter
12-6. Correction Prompt Builder
12-7. human-mediated iteration workflow
12-8. validation event logger
12-9. machine registry -> generated Skill/Prompt material
```

외부 LLM은 proposal only이며 실행 권한이 없다.

---

## 13. Continuous Improvement 분석/개선 도구

실패를 누적해 Prompt/Skill/DSL/Data contract를 증거 기반으로 개선한다.

구현:

```text
validation event storage
periodic aggregation
error-code frequency
root-cause distribution
first-pass acceptance
mean correction iterations
Prompt/Skill version comparison
repeat-error analysis
capability-gap frequency
```

개선은 자동 self-modification이 아니다.

```text
evidence
 -> review
 -> 개선 후보
 -> 별도 micro-tranche
 -> tests/regression
 -> version promotion
```

---

## 14. 최종 자연어 E2E acceptance scenario

대표 자연어 목표를 end-to-end로 검증한다.

예:

```text
최근 10일 EMA120 돌파 + 기준 Histogram 강도
 -> 현재 동일/이상 강도로 EMA120 재돌파 종목 선별
 -> 15m close > EMA120
 -> Histogram >= reference
 -> MACD 상향돌파 OR JMA 상승전환 매수
 -> 수익확보 전 EMA120 위이면 JMA 하락전환 매도 금지
 -> 수익확보 후 JMA 하락전환 매도
```

검증 범위:

```text
Natural language
 -> external LLM structured draft
 -> deterministic local validation
 -> AXIS 2 selection
 -> AXIS 3 strategy orchestration
 -> AXIS 1 execution
 -> Chart projections
 -> Backtest/evidence
```

한 종목/한 기간의 성공만으로 완료를 주장하지 않는다.

---

## 15. Legacy documentation disposition + broader compliance audit

새 구조가 안정화된 뒤 마지막으로 수행한다.

```text
KEEP / ARCHIVE / RETIRE 문서 분류
frozen core는 계속 보존
stale authority 제거
repo-wide boundary/compliance automated audit
```

`REMEDIATION_REQUIRED`가 해소되기 전 repository-wide PASS를 주장하지 않는다.

---

## PARKING LOT 규칙

현재 번호와 관계없는 아이디어가 나오면 여기에 **기록만** 한다.

```text
PARKED idea
reason
related AXIS/track
expected future step
```

PARKING LOT에 기록했다는 이유로 작업순서를 변경하지 않는다.

긴급한 product defect / data-corruption / frozen-core violation처럼 현재 신뢰경계를 훼손하는 문제만 예외적으로 현재 Step을 중단할 수 있다. 이 경우에도 먼저 문서에 `ORDER_INTERRUPTED`와 원인을 기록한 뒤 복구한다.

---

## 중요 방침 변경 기록 규칙

앞으로 다음이 발생하면 **그 턴에서 문서를 같이 갱신**한다.

```text
architecture authority 변경
AXIS 책임 변경
DSL 문법/실행 의미 변경
데이터소스/causality 변경
Bridge contract 변경
검증 기준 변경
외부 LLM authoring protocol 변경
작업순서 변경
중요한 신규 backlog/우선순위 결정
```

최소 갱신 대상:

```text
관련 authority 문서
DSL_NEXT_WORK_ORDER.md (순서/현재 step에 영향이 있을 때)
SESSION_HANDOFF.md
```

작업만 하고 handoff를 나중에 갱신하는 방식은 금지한다.
