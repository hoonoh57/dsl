# Console Operations Policy

Status: **GOVERNING OPERATOR POLICY / COMPACT SUCCESS + ERROR-FIRST OUTPUT / 2026-09-05 KST**

이 문서는 DSL/Chart 개발·검증 과정의 콘솔 출력 운영 원칙을 정의한다. 새 세션에서도 반드시 `SESSION_HANDOFF.md`와 함께 적용한다.

## 1. 목적

콘솔은 성공 이력을 나열하는 장소가 아니라 **현재 실패를 즉시 발견하고 전달할 수 있는 디버깅 인터페이스**다.

성공 로그가 길어져 실패 로그를 밀어내거나 사용자가 오류 부분을 전달하지 못하게 만드는 상태는 검증 운영 결함으로 취급한다.

## 2. 기본 출력 계약

### 성공

한 명령/한 검증 tranche의 성공 출력은 원칙적으로 **1줄**이다.

```text
[PASS] <검증명> passed (<test-count>).
```

허용:

- 최종 PASS 1줄
- 필요 시 SHA/작업공간 식별 1줄 추가

금지:

- 성공한 개별 테스트 이름 나열
- `✔ ...` 수십 줄 출력
- `ok 1`, `ok 2` 식 성공 TAP 전체 출력
- 성공한 하위 단계의 stdout/stderr 그대로 전달
- 디버깅 가치가 없는 progress/status 반복 출력

## 3. 실패 출력 계약

실패 시에는 **실패한 내용만** 기본 콘솔에 남긴다.

권장 형식:

```text
[ERROR] <검증명> failed (<failure-count>).
[FAIL] <failing test or stage>
  at <file:line>
  <AssertionError / exception / 핵심 message>
```

원칙:

1. 성공한 하위 테스트 로그는 실패 출력에서 제거한다.
2. 실패 test/stage 이름, 위치, assertion/exception message를 우선한다.
3. stack trace는 원인 파악에 필요한 부분만 출력한다.
4. 기본 콘솔 diagnostic은 최대 약 30~40줄을 넘기지 않는다.
5. 더 긴 원본 로그가 필요하면 파일로 보존하고 콘솔에는 그 경로만 출력한다.
6. raw/verbose 출력은 **실패 후 명시적인 2차 디버깅 단계**에서만 사용한다.

## 4. 운영 명령 규칙

### Python focused tests

직접 실행 금지:

```text
python -m unittest -v ...
```

기본 실행:

```text
python scripts/run_focused_tests.py <test_module> [<test_module> ...]
```

### Chart / Node focused tests

직접 실행 금지:

```text
node --test ...
```

Chart repo의 compact runner를 사용한다.

```text
npm test -- <test-file> [<test-file> ...]
```

Chart `scripts/run-tests.mjs`는 성공 시 1줄 PASS, 실패 시 failure diagnostics만 출력하는 것이 계약이다.

### Full verification

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 ...
```

Full verifier는 child output을 캡처해야 하며:

- 성공: 최종 PASS 1줄
- 실패: 성공 로그를 제거한 핵심 오류만

을 출력한다.

## 5. 사용자에게 전달하는 명령 원칙

Assistant가 사용자에게 검증 명령을 줄 때도 같은 원칙을 적용한다.

금지:

- `python -m unittest -v`
- 직접 `node --test`
- 성공 로그 전체를 paste하도록 요구

허용/권장:

- compact runner 명령만 제공
- PASS면 `패스` 또는 PASS 1줄만 전달
- FAIL이면 compact error block만 전달

사용자가 긴 로그 때문에 오류 전달이 어렵다고 말하면, 먼저 **출력 정책 위반**으로 분류하고 기능 디버깅보다 console contract를 복구한다.

## 6. 작업공간 식별

명령 블록 앞에는 반드시 실행 위치를 구분한다.

```text
DSL workspace
E:\2026\gemini\dsl-main-validation-20260904

Chart workspace
E:\2026\gemini\cascade-chart-validation-20260904
```

다른 repo의 명령을 현재 repo에서 실행시키지 않는다.

## 7. 검증 불변조건

```text
compact output != weaker verification
```

출력량을 줄이기 위해 다음을 해서는 안 된다.

- 테스트 수 감소
- assertion 제거/완화
- guard 우회
- 실패 무시
- stderr 폐기

검증은 동일하게 수행하고 **표시만 요약**한다.

## 8. 세션복구

새 세션은 다음 순서를 적용한다.

```text
SESSION_HANDOFF.md
-> CONSOLE_OPERATIONS_POLICY.md
-> STRATEGY_PRODUCT_FLOW_TODO.md
-> current trusted/unvalidated checkpoints
```

콘솔 명령을 제시하기 전에 compact runner 사용 여부를 확인한다.
