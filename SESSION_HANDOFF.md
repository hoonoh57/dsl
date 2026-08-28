# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-28 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다. 실패는 먼저 분류하고 guard를 약화하지 않는다.**

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`은 trusted Full PASS다.
- VSLICE1 checkpoint `72445456e86b695dc7288ab3a48856fa560463dd`에서 generic mechanical vertical slice가 닫혔다.
- LF2 trusted executable checkpoint는 `5a6e6e53c089ed108d19fa729cba84874e856388`이다.
- LFVAL1 trusted executable checkpoint는 `283af6e8ed046324698b9ff49e95f5044131f453`이다.
- LFVAL1 사용자 로컬 검증은 `Ran 7 tests in 0.002s / OK` 및 `[PASS] Tactical P1 verification completed: mode=Full.`이다.

## 3. 현재 위치

LF2는 trusted observation-only orchestration이고 LFVAL1은 그 frozen evidence를 TRAIN / VALIDATION / OOS / HARSH로 검증하는 trusted evidence-only 층이다.

```text
LF1 OBSERVATION_ONLY relation result
+ local deterministic setup / hard guard
 -> LF2 ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING evidence
 -> LFVAL1 TRAIN / VALIDATION / OOS / HARSH evidence validation
```

LFVAL1 explicit axes:

```text
selection qualified rate
ARM rate
hard-guard pass rate
relation-valid rate
invalid active pending cancellation safety
```

Authority boundary:

```text
LF2:
  mode = OBSERVATION_ONLY
  operational_authority = false
  execution_authority = false

LFVAL1:
  mode = EVIDENCE_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
```

Hard guard는 deterministic veto다. unsafe ARM은 fail closed이며, invalid active pending evidence는 `CANCEL_PENDING`이어야 LFVAL1을 통과한다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

LFVAL1 trust를 deployment authority로 확대하지 않는다.

다음 후보 tranche는 **별도 bounded outcome/backtest evidence**다.

```text
trusted LF1 relation evidence
+ trusted LF2 intent evidence
+ trusted LFVAL1 partition stability evidence
 -> bounded outcome/backtest measurement
 -> only then decide whether any further permission is justified
```

이 단계에서도 먼저 한 개의 deterministic evidence slice만 검증한다. 수익성/효용을 실제 outcome과 연결하더라도 Core DSL, Parser/Runtime/Broker semantics는 변경하지 않는 방향을 우선한다.

adaptive learning, ranking 확대, allocation, live selection, 새 DSL grammar, production deployment gate는 계속 보류한다.

## 5. 세션복구 규칙

새 프로젝트 세션에서 사용자가 `세션복구`라고 입력하면:

1. 이 문서를 먼저 읽는다.
2. 이전 프로젝트 대화 마지막 부분에서 이 문서 이후 exact local test evidence / 결정이 있는지 확인한다.
3. 마지막 trusted executable SHA와 GitHub `main` 사이 실행 변경분을 비교한다.
4. `CURRENT_STATE.md` 및 authority 문서를 적용한다.
5. 문서가 stale이면 실제 코드 + exact local evidence + 최근 대화 결정으로 보정한다.
6. 첫 답변은 개발철학 / 최근 한 일 / 앞으로 할 일 세 부분만 짧게 보여준다.

새 GitHub 실행 코드/테스트에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다.

## 6. 금지된 과장

현재 수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
