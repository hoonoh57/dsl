# Step 5-4 User-Defined Functions Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-08-31 KST**

## 결과

사용자 정의 함수 기능을 검증된 AXIS 1 실행 Core 밖의 compile-time lowering 층으로 추가했고 user-local 회귀검사를 통과했다.

지원 계약:

```text
strategy top-level function 선언
위치 인수
ordered local assignment
마지막 return expression
builtin 및 다른 user function 합성
직접/간접 재귀 fail-closed
free variable / mutation / nested control block fail-closed
```

실행 경계:

```text
user function source
 -> deterministic inline lowering
 -> multi-output lowering
 -> migrated Parser/Semantic/Runtime/Backtest
```

Runtime에 동적 사용자 함수 registry/eval 권한을 추가하지 않았다.

## User-local evidence

사용자 보고:

```text
test_axis1_user_functions.py = OK
test_axis1_multi_output.py = OK
test_axis1_generic_projection.py = OK
test_axis1_capability_metadata.py = OK
test_frozen_legacy_core_guard.py = OK
```

판정:

```text
PASS
root cause issue = NONE
```

## 보존 확인

```text
frozen legacy core 수정 없음
migrated execution core 대수술 없음
기존 multi-output / projection / capability metadata 회귀 없음
```

다음 순서는 `5-5 bounded loops`이며 이 checkpoint 이후에만 시작한다.
