# Three-Axis Transition Checkpoint — 2026-08-31

Status: **ACTIVE SESSION RECOVERY CHECKPOINT / READ WITH CURRENT_STATE + SESSION_HANDOFF**

이 문서는 2026-08-31 세션에서 확정된 3축 전환의 최신 결정만 기록한다. 기존 `CURRENT_STATE.md` / `SESSION_HANDOFF.md`의 과거 설명과 충돌하면 아래 새 권한 문서를 우선한다.

우선순위 문서:

```text
DSL_FROZEN_CORE_MIGRATION_POLICY.md
DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
DSL_THREE_AXIS_FINAL_TARGET.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
```

## 1. Frozen legacy core

Repository-root:

```text
core/
```

는 영구 read-only golden reference로 전환했다.

Freeze identity:

```text
source commit: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree:     8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정
core/ 이동
core/ 삭제
core/ 신규 파일 추가
새 기능을 core/에 역이식
```

자동 guard:

```text
tests/test_frozen_legacy_core_guard.py
```

## 2. New physical roots created

```text
axes/axis1_dsl/
axes/axis2_selection/
axes/axis3_monetization/
bridges/contracts/
```

현재는 README/권한 골격만 생성했으며 기능 코드를 대규모 복사하지 않았다.

이유:

```text
정확한 capability audit
 -> 한 경계씩 이식
 -> frozen Core parity
 -> checkpoint
 -> 신규 기능 계속 개발
```

## 3. AXIS 1 capability backlog is NOT deferred by migration

현재 code audit로 확인한 주요 gap:

```text
TOP: tuple / multi-output typed return + destructuring
user-defined functions
bounded loops
on_tick / on_fill rollback/commit lifecycle
partial fills / partial exits
pyramiding / multi-position accounting
full TA-Lib/reference differential fixtures
capability metadata completeness
full-engine batch/streaming parity
generic projection completeness
```

3축 전환은 위 기능 개발 중단 사유가 아니다.

원칙:

```text
legacy core 수정 중단 != DSL 기능 개발 중단
```

새 AXIS 1 migration parity 직후 tuple/multi-output부터 우선 개발한다.

## 4. AXIS 2 uses precomputed point-in-time snapshots

시장레짐/다중종목 비교를 Instrument DSL 문법이나 Runtime에 밀어 넣지 않는다.

기존 provider 원칙을 유지한다.

```text
precompute
 -> freeze immutable as_of snapshot
 -> AXIS 2 filter/rank/top-N
 -> CandidateSetResponse
```

필수 개발대상:

```text
market regime snapshots
beta/high-beta universe snapshots
sector strength + constituents
normalized MACD Histogram per-symbol snapshots
high-beta universe Histogram rank/top-N
leading-sector members Histogram rank/top-N
relative strength
turnover / capital-flow
leader/follower bounded evidence
generic Condition CRUD
historical point-in-time replay validation
```

예:

```text
고베타 종목군
 -> 동일 as_of normalized Histogram
 -> cross-sectional rank
 -> top-N

상위 주도섹터
 -> historical constituent snapshot
 -> sector 내부 Histogram rank
 -> top-N per sector
```

AXIS 1은 필요 시 일부 결과를 read-only `ctx.*`/execution input으로 소비할 뿐 universe 검색/peer ranking을 수행하지 않는다.

## 5. Immediate next micro-tranche

다음 작업은 대규모 migration이 아니다.

```text
1. AXIS 1 기존 조합능력 exact audit 잔여항목 완료
   - JMA up/down/normalized slope direct access
   - projection completeness
   - Strategy CRUD separation

2. AXIS 1 migration manifest 작성
   - 어떤 frozen core 파일이 새 axis1의 어떤 책임으로 이식되는지 mapping
   - 파일을 그대로 복사할지 재구성할지 구분

3. 첫 migration boundary 1개만 이식
   - automated parity
   - frozen guard
   - checkpoint

4. AXIS 2 snapshot schema v1 설계는 AXIS 1과 독립 병행 가능
```

첫 migration boundary가 무엇인지 문서 audit로 결정하기 전에는 무작정 전체 `core/`를 복사하지 않는다.

## 6. Current compliance wording

```text
frozen-core transition documents/roots: established
frozen guard: added, local execution PASS not yet reported
AXIS 1 migration: NOT STARTED
AXIS 2 implementation: NOT STARTED
Bridge v1 schema: DESIGN PENDING
repository-wide compliance: REMEDIATION_REQUIRED
```

부분 진척을 전체 3축 완료나 repository-wide PASS로 표현하지 않는다.
