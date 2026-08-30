# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / DSL_CORE_PHASE1_TRUSTED / 2026-08-30 KST**

이 문서는 세션 전환 시 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact local PASS + 현재 `dsl-live-studio` branch 상태를 우선한다.

## 1. 개발철학

1. 메인 제품축은 `UI → LLM/인간매개 → DSL → deterministic Core → 결과 UI`다.
2. Parser/Semantic/Runtime/Backtest/Broker가 최종 권한을 가진다. LLM은 DSL 작성자이지 실행 권한자가 아니다.
3. hard equipment / hard guard가 학습·자율성보다 우선한다. adaptive/leader-follower는 optional sidecar다.
4. 기능 존재만으로 PASS가 아니다. 실제 예제 DSL이 Core 경로를 통과하고 필요한 실행계약을 증명해야 한다.
5. micro-tranche discipline을 유지한다. 실패는 먼저 `test defect / product defect / contract mismatch / environment / unknown`으로 분류한다.

## 2. 현재 제품 기준선

Branch:

```text
dsl-live-studio
```

Direct Core path:

```text
사용자/LLM DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime
 -> BacktestEngine
 -> BrokerEmulator
 -> trades / closed trades / diagnostics / metrics
```

Legacy `app_ui.py`는 제품 성능 권한이 아니다.

## 3. DSL Core 1차 완료 checkpoint

사용자 화면에서 확인된 최종 결과:

```text
기능 모드
75 total
75 PASS
0 FAIL

실행 계약 모드
23 total
23 PASS
0 FAIL
```

따라서 현재 정의된 **DSL Core Phase 1**은 trusted로 본다.

```text
registered feature catalog       75 / 75 PASS
registered execution invariants  23 / 23 PASS
Live Studio direct-Core path     TRUSTED
v2 + v3 + v4 invariant UI        TRUSTED
DSL Core Phase 1                 TRUSTED
```

## 4. 최근 중요 수정

Live Studio의 `/api/invariants/run-all`에서 `mtf.confirmed_only`의 첫 bucket이 의도적으로 `NaN`을 포함해 FastAPI JSON 직렬화가 실패한 적이 있다.

분류:

```text
UI/API product defect
```

MTF 계산과 invariant assertion은 바꾸지 않았다. reporting boundary에서 non-finite diagnostic 값을 JSON-safe `null`로 표현하도록 고쳤고, 이후 사용자 화면에서 `23 / 23 PASS, FAIL 0`을 확인했다.

## 5. trusted invariant set

### v2

```text
context.exact_binding
context.missing_fail_closed
execution.entry_gate_suppression
execution.next_open_timing
execution.entry_time_window
execution.max_entries_per_day
order.stop_fill
order.stop_limit_fill
order.day_expiry
order.stable_client_cancel
mtf.confirmed_only
```

### v3

```text
order.oco_sibling_cancel
order.gtc_persistence
order.close_long
order.close_short
order.close_position
execution.pending_suppressed_position_occupied
execution.same_bar_reentry
execution.risk_exit_precedence
```

### v4

```text
order.limit_fill
order.cancel_unknown_fail_closed
execution.take_profit_precedence
execution.trailing_stop
```

## 6. Phase 1 완료가 의미하지 않는 것

아래는 아직 Phase 2 / deferred expansion이다.

```text
partial fills
pyramiding
multi-position accounting
on_tick / on_fill + rollback
tuple / multi-output indicators
bounded loops
user-defined functions
full TA-Lib differential fixture coverage
```

따라서 “현재 1차 DSL Core는 완료”라고는 말할 수 있지만, “가능한 모든 DSL 2.0 기능이 완성”됐다고 말하면 안 된다.

## 7. 다음 우선순위

이제 invariant 개수 늘리기 자체를 목표로 하지 않는다.

권장 다음 순서:

```text
Phase 1 freeze
 -> 대표 기능의 화면 의미 검증
 -> production historical-data adapter / provenance
 -> richer chart / diagnostics / evaluation UI
 -> 실제 필요가 확인된 Phase 2 기능만 선택 확장
```

새 Core grammar/runtime 기능은 구체적인 제품 필요가 있을 때만 추가한다.

## 8. 데이터 주장 경계

```text
SYNTHETIC_ENGINE_FIXTURE
= 결정적 기능/계약 계측용

CALLER_SUPPLIED_MARKET
= caller 제공 OHLCV를 Core에서 평가
```

caller-supplied만으로 real-market provenance가 증명되는 것은 아니다. 사용자 소유 real data source 연결은 별도 provenance 단계다.

## 9. 보존된 sidecar 연구

CTX/LF/LFREAL 등 과거 연구 자산은 보존한다. 그러나 현재 메인축이 아니며 사용자 명시 요청 없이 확장하지 않는다. adaptive/soldier autonomy 때문에 Core를 반복 변경하지 않는다.

## 10. 세션복구 규칙

사용자가 `세션복구`라고 하면:

1. 이 문서를 먼저 읽는다.
2. 이후 프로젝트 대화의 더 최신 사용자 결정/PASS를 확인한다.
3. `dsl-live-studio` branch/head와 비교한다.
4. `CURRENT_STATE.md`를 확인한다.
5. 새 remote executable/test 변경에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다.
6. 첫 답변은 정확히 `개발철학 / 최근 한 일 / 앞으로 할 일` 3개 짧은 섹션으로 답한다.

## 11. 금지된 과장

다음을 임의로 주장하거나 시작하지 않는다.

- 모든 DSL 2.0 확장 기능 완료
- synthetic fixture를 실전 수익성으로 해석
- 출처 미검증 데이터를 real study라고 부르기
- live trading readiness
- 자동 leader selection/allocation/deployment gating
- repository-wide compliance PASS
- 연구 sidecar 때문에 Core grammar/runtime를 반복 변경

Broader repository compliance는 계속 `REMEDIATION_REQUIRED`다.
