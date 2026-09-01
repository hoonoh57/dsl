# DSL AXIS 2 Precomputed Selection Policy

Status: **AUTHORITATIVE AXIS 2 DATA/SELECTION POLICY / ACTIVE / 2026-09-01 KST**

AXIS 2는 여러 종목을 비교하는 selection 계층이다. raw provider 계산이나 단일종목 DSL 실행을 요청 중에 수행하지 않고, 이미 준비된 point-in-time evidence를 immutable snapshot으로 소비한다.

## 1. Core rule

```text
precompute
 -> exact-as-of immutable snapshot
 -> validate cutoff/source/formula/ranking evidence
 -> filter
 -> sort by frozen evidence
 -> top-N
 -> CandidateSet + evidence
```

AXIS 2 request에서 미래값, nearest-time, fill-forward, interpolation, default synthesis를 사용하지 않는다.

## 2. Snapshot authority

현재 contract:

```text
axes/axis2_selection/snapshots/exact_asof.py
```

Snapshot은 최소 다음 identity를 가진다.

```text
schema_version
snapshot_id
as_of
knowledge_cutoff
universe_id
feature_version
source_refs
rows[]
  symbol
  feature_id
  value_type
  value
  validity
  provenance
  optional frozen ranking evidence
```

Ranking evidence:

```text
ranking_method
eligible_count
rank
percentile
peer_group_id
```

동일 peer group에서 ranking method와 eligible count가 섞이면 fail-closed다.

## 3. Feature preparation

다음과 같은 값은 AXIS 2 밖의 provider/precompute 단계에서 준비할 수 있다.

```text
market regime
beta / high-beta universe membership
sector strength / constituents / leader-follower evidence
EMA120 position/event evidence
normalized MACD Histogram value/rank
relative strength
turnover / capital-flow
```

AXIS 2는 provider/network를 호출해 이를 즉석 재계산하지 않는다.

## 4. Selection semantics

현재 engine:

```text
axes/axis2_selection/engine/selection.py
```

AXIS 2가 소유하는 의미:

```text
SelectionSpec
feature identity
validity requirement
filter operator/threshold
frozen rank/percentile/value metric 선택
sort direction
peer_group constraint
top-N
CandidateSet evidence
```

현재 제품 경로에서는 cross-sectional rank 자체를 selection 요청에서 새로 계산하지 않는다. rank/percentile이 필요하면 snapshot의 frozen ranking evidence를 사용한다.

```text
same snapshot + same SelectionSpec
 -> same CandidateSet order/hash
```

## 5. Condition ownership split

Condition 책임을 다음처럼 분리한다.

```text
AXIS 2
= Condition의 selection semantics
= 어떤 feature/evidence를 어떤 filter/rank/top-N 규칙으로 사용할지

AXIS 3
= Condition artifact lifecycle
= immutable version / lineage / promotion / rejection / archive
```

따라서 AXIS 2는 Condition CRUD repository나 lifecycle state를 소유하지 않는다. AXIS 3의 Condition artifact는 AXIS 2 `SelectionSpec` data를 versioned product artifact로 보존한다.

## 6. AXIS 1과의 관계

AXIS 1은 universe/sector/peer rank를 검색하거나 계산하지 않는다.

필요한 candidate evidence는 Bridge가 단일종목 실행에 필요한 값만 exact read-only context로 전달할 수 있다.

```text
ctx.<layer>.<feature>
```

금지:

```text
DSL Runtime이 universe 검색
DSL Runtime이 peer symbol 조회
DSL Runtime이 cross-sectional rank 생성
AXIS 2가 종목별 AXIS 1 DSL을 반복 호출해 selection feature 생성
```

## 7. AXIS 3 / Bridge와의 관계

```text
PointInTimeSnapshot + SelectionSpec
 -> AXIS 2 CandidateSet
 -> AXIS 3 exact promoted Condition/Strategy + StrategyRunPlan
 -> versioned Bridge
 -> AXIS 1 per-candidate execution
```

CandidateSet에는 selection/spec/snapshot identity와 후보별 evidence가 유지된다.

## 8. Backtest/live causality

과거 시점 selection은 그 시점에 알 수 있었던 exact snapshot만 사용한다.

```text
future constituent 정보 금지
현재 universe로 과거 universe 재구성 금지
현재 sector membership으로 과거 membership 대체 금지
nearest earlier snapshot 추정 금지
missing rank/value를 0/중립값으로 대체 금지
```

## 9. Final acceptance criteria

```text
exact as_of/cutoff only
mixed formula/cutoff/source contract fail-closed
frozen ranking evidence only for rank/percentile decisions
invalid/missing evidence explicit
same inputs -> same CandidateSet/hash
no AXIS1/AXIS3 internal import
no frozen repository-root core import
Condition semantics/lifecycle ownership separation preserved
```

문서 권한 충돌 시 `DSL_DOCUMENT_AUTHORITY_INDEX.md`와 `DSL_THREE_AXIS_MODULE_BOUNDARY.md`를 따른다.
