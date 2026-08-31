# External LLM Strategy Authoring / Human-Mediated Validation Loop

Status: **AUTHORING-LANE AUTHORITY / ACTIVE / 2026-08-31 KST**

이 문서는 자연어 전략 요청을 3축 구조에 연결하는 authoring process를 정의한다.

핵심 결정:

```text
우리 시스템이 자연어 의미를 완전하게 이해/검증하는 범용 NLP 엔진을 만들지 않는다.
외부 LLM은 전략 초안 생성에 사용한다.
인간이 외부 LLM과 로컬 시스템 사이를 매개할 수 있다.
우리 시스템은 외부 LLM 출력을 신뢰하지 않는다.
결정론적 schema/capability/data-source/DSL 검증을 모두 통과한 결과만 전략 후보가 된다.
```

이 Authoring Lane은 AXIS 1/2/3과 별개의 제4 실행축이 아니다. 세 축 위에서 요청을 구조화하는 입력/저작 계층이다.

---

## 1. 권한 분리

```text
Natural-language user request
        |
        v
Local Prompt Builder
        |
        v
Human -> External LLM
        |
        v
Structured Strategy Draft
        |
        v
Local deterministic validation
        |
        +-- PASS -> Strategy/Condition draft
        |
        +-- FAIL -> Correction Prompt Builder
                         |
                         v
                 Human -> External LLM
                         |
                         +---- repeat until PASS or user stops
```

실행 권한:

```text
External LLM       = proposal only
Human              = mediation / intent confirmation
Prompt Builder      = current machine contracts를 설명하는 프롬프트 생성
Draft Ingest        = strict structured-output parsing
Validator           = deterministic acceptance/rejection
AXIS 2              = selection execution
AXIS 3              = strategy persistence/orchestration
AXIS 1              = DSL compile/semantic/runtime/backtest/broker execution
Chart               = projection/evidence display only
```

---

## 2. Skill file의 역할

Repo-local skill file:

```text
skills/external_llm_strategy_authoring/SKILL.md
```

Skill은 다음을 외부 LLM에 전달하기 위한 distribution artifact다.

```text
DSL syntax and examples
currently supported capability IDs
currently unsupported / migration-pending capabilities
data-source identities and causality rules
AXIS 2 precomputed feature rules
AXIS 1 read-only context rules
structured response schema
forbidden assumptions
correction protocol
```

중요:

```text
SKILL.md != execution SSOT
```

최종 목표는 다음 machine-readable SSOT에서 skill/prompt material을 생성하는 것이다.

```text
AXIS 1 capability/function registry
AXIS 2 feature/data-source registry
Bridge schemas
Strategy/Condition schemas
runtime error-code catalog
```

수동 skill 문서는 초기 transition artifact이며, registry가 준비되면 generated artifact로 전환한다.

---

## 3. Local natural-language parsing의 책임 한계

우리 시스템의 local parser는 다음만 수행한다.

```text
request text 보존
명시적 timeframe / 숫자 / symbol / date 같은 낮은 모호성 token 추출
사용자가 지정한 data-source/context hint 보존
Prompt Builder 입력 envelope 생성
외부 LLM 응답의 strict schema parsing
```

하지 않는 것:

```text
자연어의 모든 금융 의미를 자체적으로 추론
모호한 조건을 임의로 확정
지원하지 않는 DSL syntax를 자동 창작
누락된 data source를 추측
LLM 결과를 semantic validation 없이 실행
```

즉 natural-language parser는 execution authority가 아니다.

---

## 4. External LLM prompt construction

Prompt Builder는 사용자 원문에 현재 contract snapshot을 결합한다.

최소 포함물:

```text
A. verbatim user request
B. current DSL syntax/capability manifest
C. current unsupported-capability manifest
D. AXIS 2 precomputed feature/data-source manifest
E. available read-only ctx.* bindings
F. timeframe / causality rules
G. strict response schema
H. do-not-invent rules
I. examples of valid output
```

외부 LLM에 반드시 요구한다.

```text
지원 기능만 사용
지원하지 않는 기능이 필요하면 needs_capability에 명시
존재하지 않는 feature/data source/DSL function을 발명하지 않음
모호한 뜻은 assumptions 또는 unresolved_questions로 분리
selection과 trading strategy를 분리
모든 timeframe을 명시
사전계산 cross-sectional feature와 single-symbol DSL 계산을 구분
```

---

## 5. Structured Strategy Draft v1

외부 LLM의 응답은 자유서술문이 아니라 strict structured object여야 한다.

권장 envelope:

```json
{
  "schema_version": "external_strategy_draft/v1",
  "request_id": "...",
  "intent_summary": "...",
  "assumptions": [],
  "unresolved_questions": [],
  "needs_capability": [],
  "selection_plan": {
    "as_of_policy": "point_in_time",
    "universe": {},
    "filters": [],
    "rankings": [],
    "candidate_output": {}
  },
  "strategy_plan": {
    "timeframe": "15m",
    "inputs": {},
    "entry": [],
    "exit": [],
    "risk": [],
    "context_dependencies": []
  },
  "dsl_code": "...",
  "projection_requests": [],
  "data_dependencies": [],
  "rationale": []
}
```

`selection_plan`은 AXIS 2용, `strategy_plan`/`dsl_code`는 AXIS 3 -> AXIS 1용이다.

자유로운 explanatory text가 필요하면 `rationale` 안에 넣고 envelope 밖의 prose는 기본적으로 금지한다.

---

## 6. Deterministic validation pipeline

외부 LLM 응답 수신 후 다음 순서를 고정한다.

```text
V1 JSON/schema validation
 -> V2 known capability IDs only
 -> V3 known data-source / feature IDs only
 -> V4 cross-axis boundary validation
 -> V5 timeframe/causality validation
 -> V6 DSLParser
 -> V7 DSLSemanticAnalyzer
 -> V8 compile/dry-run fixture
 -> V9 Strategy/Condition persistence validation
 -> ACCEPTED_DRAFT
```

각 단계는 fail-closed다.

예:

```text
UNKNOWN_FEATURE_ID
UNSUPPORTED_CAPABILITY
BAD_SELECTION_AXIS
BAD_STRATEGY_TIMEFRAME
DSL_PARSE_ERROR
DSL_SEMANTIC_ERROR
DATA_SOURCE_NOT_POINT_IN_TIME
CONTEXT_BINDING_REQUIRED
```

검증 실패를 자동으로 의미 변경하여 통과시키지 않는다.

---

## 7. Correction loop

검증 실패 시 원본 전략을 사람이 직접 수술하는 것을 기본 흐름으로 하지 않는다.

Correction Prompt Builder가 다음을 생성한다.

```text
original user request
previous structured draft
exact validator errors
valid capability/data-source subset relevant to the errors
strict instruction: preserve intent, change only what is necessary
same response schema
```

루프:

```text
Draft N
 -> deterministic validation FAIL
 -> correction prompt N
 -> Human -> External LLM
 -> Draft N+1
 -> validation
```

종료 조건:

```text
all deterministic validation PASS
user explicitly accepts an unresolved assumption
required capability is not implemented -> BLOCKED_NEEDS_CAPABILITY
user cancels
```

무한 재시도는 금지하며 모든 iteration은 request_id / draft_id / validation result로 기록할 수 있어야 한다.

---

## 8. Example final-goal decomposition

사용자 자연어 예:

```text
10일 이내 120이평을 돌파하면서 new MACD Histogram이 5 이상인 종목 중,
현재일 동일 강도 이상으로 120이평을 재돌파하는 종목을 고르고,
15분봉에서 종가>EMA120 및 Histogram>=기준봉 값이며 MACD 상향돌파 또는 JMA 상승전환 시 매수,
JMA 하락전환 시 매도하되 일정 수익률 이전이고 EMA120 위면 매도금지,
수익확보 후 JMA 하락전환이면 매도.
```

구조화 결과의 책임 분해:

```text
AXIS 2 / precomputed point-in-time selection
- 최근 10일 EMA120 breakout event
- breakout reference Histogram strength
- current-day re-breakout
- current strength >= reference strength
- optional universe/regime/sector/beta filters
- Candidate Set + reference evidence

AXIS 3
- selected candidate에 적용할 strategy version
- reference value/context를 AXIS 1 request에 명시적으로 연결

AXIS 1 / 15m single-symbol deterministic strategy
- close > EMA120
- hist >= reference_hist
- MACD crossover OR JMA turn-up
- exit state/risk logic
- profit threshold / EMA120 hold permission
- JMA turn-down exit after profit secured
```

AXIS 1이 과거 universe를 검색하거나 다른 종목을 비교하지 않는다.

---

## 9. Unsupported capability behavior

외부 LLM에게 현재 DSL에 없는 기능을 억지 문법으로 표현하게 하지 않는다.

예:

```text
required: tuple destructuring
status: NOT_IMPLEMENTED
```

이면 draft는 다음처럼 반환해야 한다.

```text
needs_capability = ["dsl.tuple_destructuring"]
```

로컬 validator는 `BLOCKED_NEEDS_CAPABILITY`로 분류한다.

이 결과는 AXIS 1 backlog에 연결할 수 있지만 frozen `core/`를 수정하지 않는다.

---

## 10. Security / authority rule

외부 LLM 출력은 코드가 아니라 untrusted proposal이다.

금지:

```text
LLM response를 eval/exec
LLM이 지정한 URL/provider를 자동 호출
LLM이 발명한 function/feature를 자동 등록
validation 실패를 무시하고 live/backtest 실행
LLM 설명만으로 capability가 존재한다고 간주
```

오직 등록된 local contracts와 deterministic validator만 수용 여부를 결정한다.

---

## 11. Development track

이 authoring lane은 3축 migration과 병행한다.

```text
Track A: AXIS 1 migration + DSL capability development
Track B: AXIS 2 precomputed snapshot selection
Track C: AXIS 3 Strategy/Condition CRUD
Track D: External-LLM authoring lane
```

Track D의 최소 구현순서:

```text
1. repo-local SKILL.md v1
2. strict external_strategy_draft/v1 schema
3. prompt builder
4. response ingest/schema validator
5. capability/data-source validator
6. existing DSL Parser/Semantic validator adapter
7. correction-prompt builder
8. human-mediated iteration UI/workflow
9. generated skill/prompt from machine registries
```

Track D가 AXIS 1/2/3의 실행 권한을 소유하지 않는다.
