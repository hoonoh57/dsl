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
- 새 LFOUT1 remote executable checkpoint `f95d15f2f66533a616db5a86df9cbe9e1f7c418b`를 만들었지만 아직 local validation 전이다.

## 3. 현재 위치

```text
LF1 OBSERVATION_ONLY relation evidence
+ local deterministic setup / hard guard
 -> LF2 ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING evidence
 -> LFVAL1 TRAIN / VALIDATION / OOS / HARSH stability validation
 -> LFOUT1 exact frozen outcome validation (REMOTE_UNVALIDATED)
```

LFOUT1은 BacktestEngine을 직접 호출하지 않는다. 이미 생성된 LF2 evidence와 별도로 동결된 outcome row를 exact `evidence_hash`로 결합한다.

검증 축:

```text
ARM forward-return edge vs non-ARM
ARM MFE edge vs non-ARM
ARM MAE regression vs non-ARM
CANCEL avoided-loss magnitude
holdout ARM return-edge regression vs TRAIN
```

TRAIN / VALIDATION / OOS는 정확히 하나씩, HARSH는 adverse_reason과 함께 최소 하나가 필요하다. nearest match, fill-forward, interpolation, silent default는 없다.

Authority boundary:

```text
LF2:
  mode = OBSERVATION_ONLY
  operational_authority = false
  execution_authority = false

LFVAL1 / LFOUT1:
  mode = EVIDENCE_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
```

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

LFOUT1 local trust gate를 먼저 닫는다.

```powershell
python -m unittest test_stage1_multi_symbol_follower_outcome_validation.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

focused + Full이 모두 PASS해야 LFOUT1을 trusted로 승격한다.

LFOUT1 PASS도 production profitability나 deployment authority를 의미하지 않는다. 다음 권한을 자동으로 열지 않는다:

```text
automatic selection
allocation
adaptive learning
new DSL grammar
live deployment gate
```

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
