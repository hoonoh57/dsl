# Three-Axis Transition Checkpoint — 2026-08-31

Status: **ACTIVE SESSION RECOVERY CHECKPOINT / READ WITH CURRENT_STATE + SESSION_HANDOFF**

이 문서는 2026-08-31 세션에서 확정된 3축 전환의 최신 결정만 기록한다. 기존 `CURRENT_STATE.md` / `SESSION_HANDOFF.md`의 과거 설명과 충돌하면 아래 새 권한 문서를 우선한다.

우선순위 문서:

```text
DSL_FROZEN_CORE_MIGRATION_POLICY.md
DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
skills/external_llm_strategy_authoring/SKILL.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
DSL_THREE_AXIS_FINAL_TARGET.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
```

## 1. Frozen legacy core

Repository-root:

```text
core/
```

는 영구 read-only golden reference로 전환했다.

Freeze identity:

```text
source commit: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree:     8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정
core/ 이동
core/ 삭제
core/ 신규 파일 추가
새 기능을 core/에 역이식
```

자동 guard:

```text
tests/test_frozen_legacy_core_guard.py
```

## 2. New physical roots created

```text
axes/axis1_dsl/
axes/axis2_selection/
axes/axis3_monetization/
bridges/contracts/
```

현재는 README/권한 골격만 생성했으며 기능 코드를 대규모 복사하지 않았다.

이유:

```text
정확한 capability audit
 -> 한 경계씩 이식
 -> frozen Core parity
 -> checkpoint
 -> 신규 기능 계속 개발
```

## 3. AXIS 1 capability backlog is NOT deferred by migration

현재 code audit로 확인한 주요 gap:

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
generic projection completeness
```

3축 전환은 위 기능 개발 중단 사유가 아니다.

원칙:

```text
legacy core 수정 중단 != DSL 기능 개발 중단
```

새 AXIS 1 migration parity 직후 tuple/multi-output부터 우선 개발한다.

## 4. AXIS 2 uses precomputed point-in-time snapshots

시장레짐/다중종목 비교를 Instrument DSL 문법이나 Runtime에 밀어 넣지 않는다.

기존 provider 원칙을 유지한다.

```text
precompute
 -> freeze immutable as_of snapshot
 -> AXIS 2 filter/rank/top-N
 -> CandidateSetResponse
```

필수 개발대상:

```text
market regime snapshots
beta/high-beta universe snapshots
sector strength + constituents
normalized MACD Histogram per-symbol snapshots
high-beta universe Histogram rank/top-N
leading-sector members Histogram rank/top-N
relative strength
turnover / capital-flow
leader/follower bounded evidence
generic Condition CRUD
historical point-in-time replay validation
```

예:

```text
고베타 종목군
 -> 동일 as_of normalized Histogram
 -> cross-sectional rank
 -> top-N

상위 주도섹터
 -> historical constituent snapshot
 -> sector 내부 Histogram rank
 -> top-N per sector
```

AXIS 1은 필요 시 일부 결과를 read-only `ctx.*`/execution input으로 소비할 뿐 universe 검색/peer ranking을 수행하지 않는다.

## 5. External LLM Authoring Lane is parallel, not a fourth execution axis

자연어를 자체 NLP 엔진으로 완전히 이해/검증하려고 하지 않는다.

대신 다음 human-mediated loop를 병행한다.

```text
user natural language
 -> local Prompt Builder
 -> human -> external LLM
 -> strict structured strategy draft
 -> local deterministic validation
 -> PASS: Strategy/Condition draft
 -> FAIL: correction prompt
 -> human -> external LLM
 -> repeat
```

권한:

```text
External LLM = untrusted strategy proposal generator
Human        = mediation / intent confirmation
Local system = schema/capability/data-source/DSL validation authority
AXIS 2       = selection execution authority
AXIS 3       = Strategy/Condition persistence and orchestration
AXIS 1       = deterministic DSL execution authority
```

Repo-local skill:

```text
skills/external_llm_strategy_authoring/SKILL.md
```

Structured response contract:

```text
authoring/contracts/external_strategy_draft.v1.schema.json
schema_version = external_strategy_draft/v1
```

스킬에는 현재 DSL 문법/함수, data/context causality, AXIS 2 precomputed feature boundary, 반환구조, unsupported capability 처리, correction mode를 기록한다.

중요:

```text
SKILL.md != execution SSOT
```

최종적으로 skill/prompt는 AXIS 1 capability registry + AXIS 2 feature/data-source registry + Bridge schemas + error catalog에서 생성한다.

외부 LLM이 현재 미구현 기능을 필요로 하면 문법을 발명하지 않고:

```text
needs_capability
```

로 반환한다. 로컬 validator는 이를 `BLOCKED_NEEDS_CAPABILITY`로 처리할 수 있어야 한다.

Correction loop는 exact validator error를 다시 외부 LLM에 전달하며, 오류를 숨기거나 assertion을 완화하지 않는다.

## 6. Authoring failure evidence becomes a continuous improvement loop

시스템 완성 후에도 Prompt/Skill/Validator/DSL은 증거를 기반으로 지속 보완한다.

```text
사용자 요청
 -> LLM draft
 -> deterministic validation
 -> PASS/FAIL/BLOCKED event 기록
 -> correction lineage 기록
 -> 일정 기간/충분한 표본 누적
 -> 실패 패턴 집계
 -> root cause 분류
 -> 가장 좁은 경계 개선
 -> regression
 -> 개선 전후 재발률 비교
```

Machine-readable event contract:

```text
authoring/contracts/authoring_validation_event.v1.schema.json
schema_version = authoring_validation_event/v1
```

최소 root cause 분류:

```text
PROMPT_DEFECT
SKILL_GAP
LLM_DRAFT_DEFECT
SCHEMA_DEFECT
VALIDATOR_DEFECT
DSL_PARSER_GAP
DSL_SEMANTIC_GAP
DSL_CAPABILITY_GAP
DATA_CONTRACT_GAP
AXIS_CONTRACT_GAP
USER_INTENT_AMBIGUITY
TEST_DEFECT
ENVIRONMENT_ISSUE
UNKNOWN
```

같은 error code가 반복된다는 이유만으로 Parser/Semantic을 느슨하게 만들지 않는다.

개선 우선순위는 기본적으로 다음처럼 좁은 경계부터 본다.

```text
Prompt
 -> Skill
 -> Correction Prompt
 -> Diagnostics
 -> Schema/Validator
 -> Generic DSL Parser/Semantic
 -> Generic DSL Capability
```

DSL 보완으로 승격하려면 특정 전략 한 건이 아니라 여러 서로 다른 intent에서 동일한 generic 표현력 gap이 반복되고, Prompt/Skill 보완으로 해결되지 않으며, 결정론적 계약/테스트가 가능해야 한다.

운영 metric 후보:

```text
first_pass_acceptance_rate
mean_correction_iterations
schema_failure_rate
capability_block_rate
parser_failure_rate
semantic_failure_rate
unknown_feature_rate
ambiguous_intent_rate
repeat_error_rate_after_fix
```

정기 review 또는 충분한 failure event 누적 시 Prompt/Skill/DSL remediation tranche를 결정한다.

Frozen legacy `core/`는 이 개선 루프의 수정 대상이 아니다. 신규 DSL 개선은 새 `axes/axis1_dsl/`에서만 수행한다.

## 7. Immediate next micro-tranches

대규모 migration을 하지 않는다. 다음 track은 병행 가능하지만 각 track 내부는 micro-tranche로 진행한다.

```text
Track A — AXIS 1
1. 기존 조합능력 exact audit 잔여항목 완료
   - JMA up/down/normalized slope direct access
   - projection completeness
   - Strategy CRUD separation
2. AXIS 1 migration manifest
3. 첫 migration boundary 1개 이식 + parity
4. tuple/multi-output부터 신규 DSL capability 개발

Track B — AXIS 2
1. precomputed snapshot schema v1
2. point-in-time market/sector/beta/histogram evidence contract
3. generic filter/rank/top-N
4. CandidateSetResponse v1

Track C — AXIS 3
1. Condition CRUD / Strategy CRUD separation
2. strategy version/lineage contract
3. Candidate Set -> AXIS 1 execution request orchestration

Track D — External LLM Authoring
1. SKILL.md v1 [DONE]
2. external_strategy_draft/v1 schema [DONE]
3. authoring_validation_event/v1 schema [DONE]
4. Prompt Builder
5. response ingest/schema validator
6. capability/data-source validator
7. DSL Parser/Semantic adapter
8. Correction Prompt Builder
9. human-mediated iteration workflow
10. structured validation-event logger
11. periodic aggregation/review report
12. generated skill/prompt from machine registries
```

첫 migration boundary가 무엇인지 audit로 결정하기 전에는 전체 `core/`를 무작정 복사하지 않는다.

Track D는 AXIS 1/2/3 구현 완료를 기다리지 않고 개발할 수 있지만, 외부 draft를 실제 Strategy/Condition으로 승격할 때는 당시의 machine capability/data-source contract를 다시 검증한다.

## 8. Current compliance wording

```text
frozen-core transition documents/roots: established
frozen guard: added, local execution PASS not yet reported
AXIS 1 migration: NOT STARTED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
Bridge v1 schema: DESIGN PENDING
External LLM authoring policy: ESTABLISHED
External LLM authoring skill v1: ADDED
external_strategy_draft/v1 JSON schema: ADDED
authoring continuous-improvement policy: ESTABLISHED
authoring_validation_event/v1 JSON schema: ADDED
Prompt Builder / ingest validator / correction loop / event logger: NOT IMPLEMENTED
repository-wide compliance: REMEDIATION_REQUIRED
```

부분 진척을 전체 3축 완료, 자연어 전략작성 완료, 또는 repository-wide PASS로 표현하지 않는다.
