# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / TRUSTED_EXECUTABLE_e44f684 / REALDATA1_LFREAL3_CAUSAL_DATASET_LOCALLY_TRUSTED / REALDATA2_EXACT_SOURCE_LOCALLY_TRUSTED / REALDATA2_LFREAL2_FREEZE_NEXT / MULTI_SYMBOL_REALDATA_REQUIRED_FOR_LF1 / 2026-09-05 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **구현 전에 소유계층·기존 공용경로·state SSOT·객체 생성/삭제 권한·인접계층 금지사항을 확정하고, micro-tranche 구현 → focused 검증 → Full 검증 → checkpoint 순서를 지킨다.** 실패는 먼저 분류하고 guard/assertion을 약화하지 않는다.

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`, `LFOUT1`, `LFREAL1`, `LFREAL2`, `LFREAL3`는 trusted Full PASS다.
- REALDATA1 exact source bytes는 `57541`, SHA-256은 `fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba`로 고정됐다.
- REALDATA1 원본 483행은 LFREAL2 manifest `8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982`로 trusted다.
- 실제 LFREAL3 admission에서 `2024-10-14` 한 행이 `low=184624.15022681453 > close=183735.109375`로 약 `889.0408518145268` 위반하여 정상 fail-closed했다. 분류는 **external source/data defect**다.
- Core assertion이나 가격은 수정하지 않았다. 원본은 그대로 보존했다.
- edge에서 해당 한 행만 명시적으로 quarantine하고 causal `date/open/high/low/close/volume`만 직렬화한 별도 482행 dataset을 만들었다.
- 사용자 로컬 clean validation checkout `f770742b69137315b14f16ad92ea77ac5881db7c`에서 focused `Ran 22 tests in 0.016s / OK`, 실제 파생+LFREAL3 admission PASS, Tactical P1 Full PASS를 확보했다.
- MSA2/LF1은 `leader_count < len(universe.symbols)`를 강제하므로 `leader_count=1`인 LF1은 최소 2개 종목이 필요함을 확인했다. REALDATA1은 `000660.KS` 단일 종목이므로 현재 상태에서 LF1/LF2 생성은 금지한다.
- 두 번째 독립 source로 Samsung Electronics `005930.KS`의 exact GitHub source를 pin했다.
- REALDATA2 source identity:
  - repository `nileshiq/Samsung-Stock-Price`
  - commit `bcef6f27b803ce89000e2fc336201ddeef7df015`
  - file `Samsung Dataset.csv`
  - Git blob SHA-1 `68e3b6d861b4bfcf39d9c09c6a073c271369d3a9`
  - observations `2000-01-04 .. 2024-06-13`
  - records `6127`
- 사용자 로컬 clean validation checkout에서 REALDATA2 acquisition focused `Ran 3 tests in 0.001s / OK`를 통과했다.
- 실제 exact acquisition은 다음으로 고정됐다:

```text
bytes=511194
sha256=ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
Git blob SHA-1=68e3b6d861b4bfcf39d9c09c6a073c271369d3a9
```

- Stage1 preflight의 direct Python dependency probe가 PowerShell 5.1의 `$ErrorActionPreference='Stop'`와 충돌하는 **verification-harness defect**를 발견했다. Tactical에서 이미 쓰던 native stderr/exit capture pattern으로 Stage1 launcher만 수정했고 focused contract를 추가했다.
- focused launcher/native dependency tests는 `Ran 10 tests in 0.038s / OK`였다.
- clean validation venv에 `numpy`가 없었던 것은 **environment issue**로 분류했고, 새 venv를 만들지 않고 기존 venv에 `numpy 2.5.2`만 설치했다.
- 이후 Stage1 preflight는 다음으로 PASS했다:

```text
[PASS] Stage 1 preflight: Python Python 3.13.1, Node v24.19.0
```

- 첫 Full 재시도에서 `Stage 1 full stress failed (exit=-1)`가 한 번 발생했지만 product assertion 출력은 없었다.
- resumable seeker 단독, `factory_vertical -> resumable`, `deterministic -> factory -> resumable`, candidate-prefix, 실제 첫 7개 `Harness.check` 순서를 모두 재현했고 전부 PASS했다. threshold/Core 수정은 하지 않았다.
- exact SHA `e44f6846619f9ec6c7bb9725d517d77cc197c802`에서 최종 Tactical P1 Full 재실행이 PASS했다:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

- **현재 trusted executable/test checkpoint는 `e44f6846619f9ec6c7bb9725d517d77cc197c802`다.** 이후 documentation-only commit은 executable trust를 바꾸지 않는다.

REALDATA1 실제 파생 identity:

```text
record_count=482
quarantined=1
quarantined observation=20241014000000
derived_bytes=40493
derived_sha256=c97624cdc92632ec3e4fab637e37514aadb9e9f9e61b1a4f2dde3a2e6390b76c
derived dataset_manifest_hash=58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6
row_bundle_hash=1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2
```

## 3. 현재 위치

```text
TRUSTED_LOCAL_EXECUTABLE
  e44f6846619f9ec6c7bb9725d517d77cc197c802

ORIGINAL REALDATA1 LFREAL2
  exact bytes: 57541
  content SHA-256: fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba
  dataset_manifest_hash: 8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
  record_count: 483

TRUSTED REALDATA1 CAUSAL DERIVED DATASET
  symbol: 000660.KS
  record_count: 482
  derived SHA-256: c97624cdc92632ec3e4fab637e37514aadb9e9f9e61b1a4f2dde3a2e6390b76c
  dataset_manifest_hash: 58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6
  row_bundle_hash: 1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2

TRUSTED REALDATA2 EXACT SOURCE IDENTITY
  symbol: 005930.KS
  source commit: bcef6f27b803ce89000e2fc336201ddeef7df015
  Git blob SHA-1: 68e3b6d861b4bfcf39d9c09c6a073c271369d3a9
  exact bytes: 511194
  content SHA-256: ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
  record_count: 6127
  observations: 2000-01-04 .. 2024-06-13
  LFREAL2 manifest: NOT YET CREATED
  LFREAL3 rows: NOT YET ADMITTED

LF1 admissibility:
  false until REALDATA2 completes its LFREAL2/LFREAL3 causal admission and an explicit exact-date multi-symbol universe is established

market_data_authenticity_verified = false
real_data_claim = false
```

연구 데이터 경로:

```text
REALDATA1 exact source                             [DONE / TRUSTED]
 -> original LFREAL2 immutable manifest           [DONE / TRUSTED]
 -> explicit quarantine causal derived LFREAL2    [DONE / TRUSTED]
 -> LFREAL3 manifest-bound causal rows             [DONE / TRUSTED]

REALDATA2 exact source                             [DONE / TRUSTED]
 -> original LFREAL2 immutable manifest           [NEXT]
 -> causal OHLCV edge admission through LFREAL3   [LATER]

both independently admitted instruments
 -> exact shared observation dates only
 -> static explicit multi-symbol universe
 -> existing MSA2 / LF1 / LF2
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

REALDATA1 원본의 `return`, `next_close`, `direction`은 causal observation feature로 들어가지 않는다. REALDATA2의 `Adj Close`는 raw `Close`를 대체하지 않는다. nearest-time lookup, fill-forward, interpolation, 가격보정도 하지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

다음 micro-tranche는 **LF1 구현이 아니라 REALDATA2 exact original source의 LFREAL2 freeze**다.

```text
REALDATA2 exact original bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> immutable REALDATA2 original-source manifest
```

구현 전 고정 경계:

```text
owner layer: tools/ edge adapter outside Core
existing shared path: LFREAL2 ExternalDatasetFreezer
state SSOT:
  pinned REALDATA2 exact source identity
  -> immutable LFREAL2 manifest
create authority:
  caller-provided exact source bytes
  -> existing freezer only
delete authority: none
forbidden:
  Core/Parser/Runtime/Backtest/Broker provider/file/network authority
  source-specific semantics in Core
  Adj Close replacing raw Close
  causal-row derivation or LFREAL3 admission in the same tranche
  nearest-time/fill-forward/interpolation
```

그 LFREAL2 tranche가 고정해야 할 original-source identity:

```text
symbol: 005930.KS
timeframe: 1d
first_observation: 20000104000000
last_observation: 20240613000000
record_count: 6127
exact_bytes: 511194
content_sha256: ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
```

이 freeze가 focused + Full PASS된 뒤에만 다음 micro-tranche에서 raw `Date/Open/High/Low/Close/Volume`을 parsing하여 existing LFREAL3 admission을 시도한다.

LFREAL3에서 invalid OHLC가 나오면 먼저 external data defect 여부를 분류한다. original source/manifest는 보존하고, Core guard를 약화하거나 tolerance를 넣거나 가격을 clip/correct/interpolate하지 않는다.

REALDATA2 LFREAL3까지 trusted되기 전에는 multi-symbol universe도 LF1/LF2 evidence도 만들지 않는다. 두 종목의 later alignment는 exact shared observation date만 사용한다.

automatic selection, allocation, adaptive learning, new DSL grammar, live deployment gate는 계속 보류한다.

## 5. 세션복구 규칙

새 프로젝트 세션에서 사용자가 `세션복구`라고 입력하면:

1. 이 문서를 먼저 읽는다.
2. 이전 프로젝트 대화 마지막 부분에서 이 문서 이후 exact local test evidence / 결정이 있는지 확인한다.
3. 마지막 trusted executable SHA와 GitHub `main` 사이 실행 변경분을 비교한다.
4. `CURRENT_STATE.md` 및 authority 문서를 적용한다.
5. 문서가 stale이면 실제 코드 + exact local evidence + 최근 대화 결정으로 보정한다.
6. 첫 답변은 개발철학 / 최근 한 일 / 앞으로 할 일 세 부분만 짧게 보여준다.

새 GitHub 실행 코드/테스트에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다. docs-only HEAD와 trusted executable SHA를 혼동하지 않는다.

## 6. 금지된 과장

현재 확인된 것은 REALDATA1의 exact source-byte/original+derived LFREAL2/LFREAL3 causal admission과 REALDATA2의 exact source-byte identity까지다. REALDATA2 LFREAL2/LFREAL3, multi-symbol real-data universe, independent market-data authenticity, 실제 LF1/LF2 relation edge는 아직 검증하지 않았다.

```text
market_data_authenticity_verified = false
real_data_claim = false
```

수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
