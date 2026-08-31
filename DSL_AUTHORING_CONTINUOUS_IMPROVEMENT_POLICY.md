# DSL Authoring Continuous Improvement / Error Learning Policy

Status: **AUTHORING-IMPROVEMENT AUTHORITY / ACTIVE / 2026-08-31 KST**

이 문서는 External-LLM Authoring Lane에서 반복적으로 발생하는 오류를 장기적으로 수집·분석하여 Prompt / Skill / Validator / DSL Capability를 지속 보완하는 폐쇄루프를 정의한다.

핵심 원칙:

```text
완성 후에도 시스템은 고정되지 않는다.
반복 실패는 버리지 않고 evidence로 축적한다.
개별 오류를 즉시 예외처리하지 않는다.
일정 기간/충분한 표본 후 오류 패턴을 집계한다.
원인을 분류한 뒤 가장 좁은 경계를 개선한다.
개선 후 regression + 재발률 비교로 효과를 검증한다.
```

---

## 1. 왜 필요한가

자연어 전략 요청의 다양성은 사전에 완전히 열거할 수 없다.

따라서 최종 강점은 모든 자연어를 처음부터 완벽히 파싱하는 것이 아니라 다음 루프에 있다.

```text
사용
 -> 실패/교정 발생
 -> 구조화 로그 축적
 -> 반복 패턴 발견
 -> 원인 분류
 -> Prompt / Skill / Parser / Semantic / Capability 중 필요한 최소 경계 보완
 -> regression
 -> 다시 사용
```

이 루프는 제품 운영의 일부이며 임시 디버깅 절차가 아니다.

---

## 2. 모든 Authoring iteration은 evidence event를 남긴다

최소 event identity:

```text
schema_version
event_id
request_id
draft_id
iteration
occurred_at
user_request_hash
skill_version
prompt_builder_version
prompt_template_version
external_model_label
validator_version
axis_contract_versions
```

검증 결과:

```text
validation_stage
status
error_code
error_message
source_location
capability_id
feature_id
data_source_id
timeframe
```

교정 결과:

```text
correction_prompt_generated
next_draft_id
resolved
resolution_class
resolution_note
```

원문 전략과 LLM 응답 전체를 무조건 영구 저장하는 것을 전제로 하지 않는다. 보존 정책은 별도 privacy/operations 정책으로 관리하며, 분석에 필요한 식별자/해시/구조화 오류 evidence를 우선한다.

---

## 3. 오류는 먼저 원인 class로 분류한다

허용되는 1차 분류:

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

중요:

```text
같은 error code의 반복 != 같은 root cause
```

예를 들어 `DSL_PARSE_ERROR` 반복은 다음 중 하나일 수 있다.

```text
Prompt가 허용 syntax를 충분히 설명하지 못함
Skill 예제가 잘못됨
LLM이 forbidden syntax를 계속 생성함
Parser가 일반적으로 필요한 문법을 지원하지 않음
Validator error message가 교정에 필요한 정보를 제공하지 못함
```

따라서 parser 수정은 root cause 판정 후에만 한다.

---

## 4. 개선 우선순위는 가장 좁은 경계부터

권장 순서:

```text
1. Prompt wording / relevant example 보완
2. Skill manifest / capability 설명 보완
3. Correction prompt quality 보완
4. Error diagnostics 보완
5. Schema / validator contract 보완
6. Generic DSL parser/semantic 보완
7. Generic DSL capability 신규 개발
```

특정 자연어 한 문장을 통과시키기 위한 DSL 특수문법/예외는 금지한다.

DSL 변경은 여러 전략에 일반적으로 필요한 표현력 gap이 증거로 확인될 때만 수행한다.

---

## 5. Periodic review

개별 실패마다 architecture를 변경하지 않는다.

Review trigger는 다음 중 하나 이상으로 둘 수 있다.

```text
정기 시간 주기
충분한 신규 failure event 수집
특정 error_code 빈도 임계치 초과
동일 correction loop 평균 iteration 증가
BLOCKED_NEEDS_CAPABILITY 누적
사용자가 반복적으로 같은 표현을 요청
```

Review 산출물:

```text
오류 빈도/비율
stage별 실패율
top error codes
평균 correction iterations
first-pass acceptance rate
blocked capability frequency
prompt/skill version별 실패율
동일 intent cluster의 반복 패턴
recommended remediation tranche
```

---

## 6. 개선 결정을 숫자로 검증한다

최소 운영 metric 후보:

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

개선 전후 동일/유사 request corpus를 재실행하여 효과를 비교한다.

예:

```text
Prompt v7
first-pass 61%
mean correction 2.4

Prompt v8
first-pass 79%
mean correction 1.3
```

이런 evidence 없이 "프롬프트가 좋아졌다"고 판정하지 않는다.

---

## 7. DSL Parser/Capability 보완으로 승격하는 기준

다음 조건을 만족할수록 DSL 개선 후보의 우선순위가 높다.

```text
여러 서로 다른 자연어 intent에서 동일 표현력 gap 발생
Prompt/Skill 보완으로 해결되지 않음
현재 DSL 조합으로 우회하면 복잡성/오류율이 과도함
특정 전략이 아닌 generic language capability임
결정론적으로 정의 가능함
Parser/Semantic/Runtime 전체 계약과 테스트가 가능함
```

예:

```text
tuple/multi-output destructuring
bounded loop
user-defined function
```

같은 기능은 이러한 generic capability 후보가 될 수 있다.

반대로 특정 종목/전략 전용 shortcut syntax는 허용하지 않는다.

---

## 8. Prompt/Skill 개선과 DSL 개선을 분리한다

```text
Prompt/Skill 개선
= 외부 LLM이 이미 존재하는 capability를 더 정확히 사용하도록 도움

DSL 개선
= 현재 capability로 표현할 수 없는 일반 기능을 새로 추가
```

두 문제를 섞지 않는다.

외부 LLM이 존재하는 `ta.crossover`를 자꾸 잘못 호출한다면 우선 Prompt/Skill 문제다.

반대로 사용자가 일반적인 다중출력 destructuring을 반복 요청하고 현재 DSL에 해당 기능이 없다면 DSL capability gap이다.

---

## 9. Frozen legacy Core는 개선 대상이 아니다

Authoring failure evidence가 누적되더라도 frozen repository-root `core/`는 수정하지 않는다.

모든 신규 DSL parser/semantic/runtime/capability 개선은 migration 완료 후 `axes/axis1_dsl/`에서 수행한다.

```text
failure evidence
 -> remediation decision
 -> new AXIS 1 micro-tranche
 -> focused test
 -> full regression
 -> capability manifest update
 -> generated Skill/Prompt material update
```

---

## 10. Machine-readable event contract

구조화된 로그 이벤트는 다음 schema를 사용한다.

```text
authoring/contracts/authoring_validation_event.v1.schema.json
```

향후 aggregation/reporting engine은 이 event contract를 소비한다.

원칙:

```text
raw console text scraping에 의존하지 않음
error code는 stable identity
free-text message는 설명용
version identity를 반드시 보존
request_id/draft_id로 correction lineage 추적
```

---

## 11. 최종 목표

Authoring Lane의 장기 목표는 다음이다.

```text
사용량이 늘어날수록
 -> 오류 evidence가 축적되고
 -> Prompt/Skill 정확도가 올라가며
 -> 실제 generic DSL gap이 더 명확히 드러나고
 -> AXIS 1 표현력이 증거 기반으로 확장되고
 -> correction iteration이 점차 감소한다.
```

즉 시스템 완성은 변화가 멈추는 시점이 아니라, **변화를 안전하게 흡수하는 구조가 완성되는 시점**이다.
