# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-28 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다.**

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`은 trusted Full PASS다.
- VSLICE1 checkpoint `72445456e86b695dc7288ab3a48856fa560463dd`에서 generic mechanical vertical slice가 닫혔다.
- 사용자 로컬 VSLICE1 증거는 `Ran 2 tests in 0.039s / OK` 및 `Tactical P1 Full PASS`다.
- 그 다음 Core를 확장하지 않고 LF2 Add-on orchestration을 원격 구현했다.
- LF2 executable checkpoint는 `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219`이며 아직 local trust 전이다.

## 3. 현재 위치

LF2는 trusted LF1 결과와 한 follower-local deterministic setup을 조합한다.

```text
LF1 OBSERVATION_ONLY relation result
+ selected/local follower
+ local setup pass/fail
+ local hard-guard pass/fail
+ explicit relation_still_valid
+ active pending identity when present
 -> ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING evidence
```

중요한 authority boundary:

```text
mode = OBSERVATION_ONLY
operational_authority = false
execution_authority = false
```

LF2는 Broker/Backtest/DSLRuntime/provider/network/database를 호출하지 않는다. 실제 주문/취소는 이미 trusted인 generic DSL/Broker 경계의 책임이다.

Hard guard는 학습보다 우선하며 deterministic veto다. hard guard 실패는 신규 ARM을 막고 이미 active인 pending에 `CANCEL_PENDING` 의도를 낸다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

LF2 local trust gate만 수행한다.

```powershell
python -m unittest test_stage1_multi_symbol_follower_pending_orchestration.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

둘 다 PASS하면 LF2를 trusted로 승격한다.

그 다음에도 즉시 deployment authority를 주지 않는다. 별도 Train/Validation/OOS/Harsh evidence tranche가 필요한지 먼저 판단한다. adaptive learning, ranking 확대, allocation, live selection, 새 DSL grammar는 자동으로 열지 않는다.

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
