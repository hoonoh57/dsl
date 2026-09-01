# DSL Human Communication / Console Output Policy

Status: **ACTIVE HUMAN-INTERFACE AUTHORITY / 2026-09-01 KST**

이 문서는 내부 기계계약과 사용자 커뮤니케이션을 분리하는 출력 원칙을 정의한다.

핵심 원칙:

> **기계어는 내부적으로 정확하게 관리하고, 사람에게는 사람이 이해하는 용어로 필요한 내용만 보여준다.**

> **내부 정밀성은 유지하되 사용자 화면의 복잡성은 최소화한다.**

---

## 1. 내부 정보는 유지한다

다음 정보는 내부 machine-readable authority / evidence로 계속 관리한다.

```text
schema_version
request_id / draft_id
capability IDs
feature/data-source IDs
error codes
validator stage
provenance
commit/checkpoint identities
structured validation events
Bridge contracts
Parser/Semantic diagnostics
```

이 정보는 검증, 회귀, 디버깅, 지속개선을 위해 필요하다.

그러나 기본 사용자 커뮤니케이션에 그대로 노출하지 않는다.

---

## 2. 프롬프트/대화창 기본 출력

프로젝트 진행 보고는 기본적으로 다음 두 구분만 사용한다.

```text
한 일
할 일
```

표현 규칙:

```text
사람이 이해하는 기능/목적 중심 용어 사용
짧고 직접적으로 설명
현재 작업과 다음 작업만 제시
내부 schema 이름, hash, error code, class/module 이름은 기본 생략
이미 합의된 배경 설명 반복 금지
긴 구현 세부사항/검증 로그 나열 금지
```

예:

```text
한 일
- 기존 DSL의 JMA 사용 가능 범위를 확인했습니다.
- 부족한 기능과 단순 검증부족을 구분했습니다.

할 일
- 기존 DSL 기능을 새 AXIS 1 구조로 옮길 순서를 확정합니다.
```

다음 경우에만 기계 식별자를 사용자에게 표시할 수 있다.

```text
사용자가 직접 요청
실패 원인을 구분하는 데 반드시 필요
로컬 검증 명령/파일을 정확히 지정해야 함
버전/commit을 서로 맞춰야 하는 상황
```

그 경우에도 사람 설명을 먼저 쓰고 기계 식별자는 보조정보로 둔다.

---

## 3. 콘솔 기본 출력

정상 실행 콘솔은 디버깅에 필요하지 않은 정보를 출력하지 않는다.

기본 성공 출력:

```text
[PASS] 사람이 이해할 수 있는 한 줄 결과
```

가능하면 정상 성공은 한 줄로 끝낸다.

금지:

```text
정상 경로의 내부 단계별 trace 반복
request/schema/capability ID 전부 출력
긴 JSON dump
성공한 각 내부 검증단계별 PASS 연속 출력
중복된 시작/완료 메시지
```

---

## 4. 실패/디버깅 출력

실패 시에는 문제 해결에 필요한 최소 정보만 보인다.

우선순위:

```text
무엇이 실패했는가
사람이 이해할 수 있는 원인
어디를 확인해야 하는가
필요한 경우에만 error code / component / path
```

예:

```text
[FAIL] 15분 차트와 전략의 실행 주기가 다릅니다. 전략 주기를 15분으로 맞춰야 합니다.
```

필요할 때만:

```text
code=BAD_STRATEGY_TIMEFRAME
```

같은 기계정보를 보조로 붙인다.

상세 trace, structured event, request identity, stack 정보는 내부 로그에 남기고 기본 콘솔에는 노출하지 않는다.

---

## 5. 내부 로그와 사용자 출력은 분리한다

```text
Internal evidence/log
= 상세하고 기계판독 가능

Prompt/chat output
= 한 일 / 할 일 중심의 인간 친화 요약

Console output
= 정상 한 줄 / 실패 최소 진단
```

사용자 화면을 단순화하기 위해 내부 증거를 삭제하거나 축소하지 않는다.

즉:

```text
human simplicity != machine evidence loss
```

이다.

---

## 6. 지속개선과의 관계

LLM 반환 오류와 validator 실패는 사용자 화면에 전부 쏟아내지 않는다.

내부에서는 구조화 event로 누적하고, 사용자에게는 필요할 때만 사람이 이해할 수 있는 원인과 다음 행동을 보여준다.

```text
Detailed failure evidence
 -> internal validation event/log
 -> aggregate review / improvement

User-facing
 -> 필요한 원인 요약
 -> 다음 행동
```

---

## 7. 적용 범위

이 정책은 다음에 공통 적용한다.

```text
Chat / Prompt 진행 보고
Live Studio 사용자 메시지
CLI / console
start/restart/stop launcher
validator 결과
migration/parity scripts
external-LLM authoring workflow
AXIS 1/2/3 운영 UI
```

기능별 구현에서 별도 출력 형식을 만들더라도 이 정책보다 장황하게 만드는 것을 기본값으로 삼지 않는다.

---

## 8. 작업순서와의 관계

이 정책은 `DSL_NEXT_WORK_ORDER.md`의 작업순서를 변경하지 않는다.

중요 방침으로 즉시 적용하되, 기존 executable의 출력 정리는 현재 Step을 건너뛰어 별도 기능개발로 시작하지 않는다.

향후 각 Step에서 해당 코드/콘솔을 수정할 때 이 정책을 함께 적용한다.

현재 작업은 계속 `DSL_NEXT_WORK_ORDER.md`의 현재 포인터를 따른다.

---

## 9. 실행기 강제 규칙

정상 테스트와 정상 기동의 상세 stdout/stderr를 프롬프트 콘솔에 그대로 흘리지 않는다.

```text
성공
 -> 세부 출력은 내부 log/evidence에 보존
 -> 콘솔은 최종 [PASS] 한 줄

실패
 -> 실패한 명령/서비스 이름
 -> 실제 오류가 시작되는 구간만 제한된 길이로 콘솔 표시
 -> 전체 원시 출력은 내부 log 파일에 유지
```

실패와 무관한 성공 test case, TAP 진행행, startup 단계별 INFO/PASS는 오류 화면을 밀어내므로 기본 콘솔 출력 금지다.

오류 구간이 길어도 콘솔은 bounded tail / failure section만 보여야 하며, 원시 전체 로그를 보기 위해 사용자가 스크롤을 수백 줄 되돌리는 상황을 만들지 않는다.
