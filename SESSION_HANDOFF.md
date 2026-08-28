# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-29 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다. 실패는 먼저 분류하고 guard를 약화하지 않는다.**

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`, `LFOUT1`, `LFREAL1`은 trusted Full PASS다.
- LFREAL1 trusted executable checkpoint는 `5aa1da3268f1f3e031aa6d607a4d3a5921f03e58`이고 local evidence는 `Ran 7 tests in 0.002s / OK` + Tactical P1 Full PASS다.
- 저장소에 authoritative real-market LF dataset이 없으므로 fixture를 real data로 가장하지 않기로 유지했다.
- LFREAL2는 caller-provided bytes를 SHA-256으로 동결하는 external-dataset manifest contract다.
- LFREAL2 remote executable checkpoint는 `10861c232d03937c5ae77e2be32cd1873a5ff977`이며 아직 local validation 전이다.

## 3. 현재 위치

```text
LF1 OBSERVATION_ONLY relation evidence
+ local deterministic setup / hard guard
 -> LF2 ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING evidence
 -> LFVAL1 TRAIN / VALIDATION / OOS / HARSH stability validation
 -> LFOUT1 exact frozen outcome validation
 -> LFREAL1 non-fixture provenance/admission contract
 -> LFREAL2 external caller-bytes immutable dataset manifest (REMOTE_UNVALIDATED)
```

LFREAL2는 file I/O나 provider를 소유하지 않는다. 외부에서 얻은 bytes를 caller가 넘기면 다음만 수행한다.

```text
non-empty bytes
+ source_id/source_kind/media_format
+ timeframe
+ unique symbols
+ first/last observation
+ positive record_count
+ optional expected SHA-256
 -> exact content SHA-256
 -> stable dataset_manifest_hash
```

차단 source kind:

```text
SYNTHETIC
FIXTURE
GENERATED
MOCK
TEST
```

Authority/claim boundary:

```text
LFREAL2:
  mode = RESEARCH_DATASET_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
  provider_authority = false
  file_io_authority = false
  content_hash_verified = true
  market_data_authenticity_verified = false
  real_data_claim = false
```

`content_hash_verified=true`는 caller가 넘긴 bytes와 emitted SHA-256이 일치한다는 뜻뿐이다. 외부 시장데이터 출처의 진위까지 증명하지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

먼저 LFREAL2 local trust gate를 닫는다.

```powershell
python -m unittest test_stage1_multi_symbol_follower_external_dataset.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

focused + Full이 둘 다 PASS해야 LFREAL2를 trusted로 승격한다.

그 뒤에도 자동선별이나 deployment를 열지 않는다. 실제 다음 연구 단계는 **진짜 외부 historical bytes를 확보 → LFREAL2로 freeze → source origin 별도 검증 → 그 다음에만 좁은 causal parser/producer 설계**다.

fixture 복제, automatic selection, allocation, adaptive learning, new DSL grammar, live deployment gate는 계속 보류한다.

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

현재 external real-market dataset 확보, real-data LF study, 수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
