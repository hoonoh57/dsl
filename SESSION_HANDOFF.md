# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / REALDATA1_LFREAL3_CAUSAL_DATASET_LOCALLY_TRUSTED / MULTI_SYMBOL_REALDATA_REQUIRED_FOR_LF1 / 2026-09-04 KST**

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
- 원본 483행은 LFREAL2 manifest `8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982`로 trusted다.
- 실제 LFREAL3 admission에서 `2024-10-14` 한 행이 `low=184624.15022681453 > close=183735.109375`로 약 `889.0408518145268` 위반하여 정상 fail-closed했다. 분류는 **external source/data defect**다.
- Core assertion이나 가격은 수정하지 않았다. 원본은 그대로 보존했다.
- edge에서 해당 한 행만 명시적으로 quarantine하고 causal `date/open/high/low/close/volume`만 직렬화한 별도 482행 dataset을 만들었다.
- 사용자 로컬 clean validation checkout `f770742b69137315b14f16ad92ea77ac5881db7c`에서 focused `Ran 22 tests in 0.016s / OK`, 실제 파생+LFREAL3 admission PASS, Tactical P1 Full PASS를 확보했다.
- **현재 trusted executable/test checkpoint는 `f770742b69137315b14f16ad92ea77ac5881db7c`다.** 이후 docs-only commit은 executable SHA를 바꾸지 않는다.
- 다음 공용계약 점검에서 MSA2/LF1은 `leader_count < len(universe.symbols)`를 강제하므로 `leader_count=1`인 LF1은 최소 2개 종목이 필요함을 확인했다. REALDATA1은 `000660.KS` 단일 종목이므로 현재 상태에서 LF1/LF2 생성은 금지한다.

실제 파생 identity:

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
  f770742b69137315b14f16ad92ea77ac5881db7c

ORIGINAL REALDATA1 LFREAL2
  exact bytes: 57541
  content SHA-256: fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba
  dataset_manifest_hash: 8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
  record_count: 483

TRUSTED CAUSAL DERIVED DATASET
  symbol: 000660.KS
  record_count: 482
  derived SHA-256: c97624cdc92632ec3e4fab637e37514aadb9e9f9e61b1a4f2dde3a2e6390b76c
  dataset_manifest_hash: 58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6
  row_bundle_hash: 1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2

LF1 admissibility:
  false until an independently identified second causal instrument is pinned and admitted

market_data_authenticity_verified = false
real_data_claim = false
```

연구 데이터 경로:

```text
external historical bytes
 -> original LFREAL2 immutable manifest                  [DONE / TRUSTED]
 -> explicit quarantine causal derived LFREAL2 manifest [DONE / TRUSTED]
 -> LFREAL3 manifest-bound causal rows                   [DONE / TRUSTED]
 -> additional independent causal instrument            [NEXT]
 -> static explicit multi-symbol universe
 -> existing MSA2 / LF1 / LF2
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

원본의 `return`, `next_close`, `direction`은 causal observation feature로 들어가지 않는다. nearest-time lookup, fill-forward, interpolation, 가격보정도 하지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

다음 micro-tranche는 **LF1 구현이 아니라 multi-symbol 데이터 경계 확보**다.

```text
at least one additional independently identified instrument/source
 -> exact caller bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> causal OHLCV-only edge derivation/admission
 -> existing LFREAL3
 -> explicit aligned static universe
```

구현 전 고정 경계:

```text
owner layer: tools/ research data edge outside Core
existing shared path:
  ExternalDatasetFreezer
  -> CausalRowProducer.admit/snapshot
  -> MSA1/MSA2
  -> MultiSymbolLeaderFollowerRelationAnalyzer
  -> MultiSymbolFollowerPendingOrchestrator
state SSOT:
  exact source identity
  + LFREAL2 manifest hash per source/dataset
  + LFREAL3 row bundle hash per instrument
  + explicit static universe topology
create authority: research data/evidence artifacts only
delete authority: none
forbidden:
  one series를 복제/shift하여 가짜 follower symbol 생성
  nearest-time/fill-forward/interpolation
  Parser/Runtime/Backtest/Broker provider/file/network authority
  hidden ranking/allocation
  execution/deployment authority
```

현재 `000660.KS` 하나로 LF1을 실행하지 않는다. 두 번째 종목은 별도의 source identity와 causal OHLCV 검증을 통과해야 한다.

이 multi-symbol 데이터 gate가 focused + Full PASS된 뒤에만 exact-as-of LF1/LF2 evidence producer로 간다.

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

현재 확인된 것은 `000660.KS` exact source-byte identity, original/derived LFREAL2 identity, LFREAL3 causal row admission까지다. multi-symbol real-data universe, market-data authenticity, 실제 LF1/LF2 relation edge는 아직 검증하지 않았다.

```text
market_data_authenticity_verified = false
real_data_claim = false
```

수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
