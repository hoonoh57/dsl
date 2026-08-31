# DSL AXIS 2 Precomputed Selection Policy

Status: **AUTHORITATIVE AXIS 2 DATA/SELECTION POLICY / 2026-08-31 KST**

이 문서는 3축 구조에서 시장레짐, 고베타 종목군, 섹터 강도, 다중종목 상대비교/랭킹을 어떻게 계산하고 소비할지 정의한다.

이 문서는 `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`의 다음 기존 원칙을 그대로 계승한다.

```text
parent / cross-market / cross-symbol features
= Instrument DSL 밖에서 계산
= point-in-time evidence로 동결
= downstream은 read-only로 소비
```

핵심 규칙:

> **AXIS 2의 요청 처리 중 AXIS 1 DSL을 종목별로 호출해 시장레짐·고베타·섹터강도·cross-sectional rank를 즉석 계산하지 않는다. 가능한 feature는 먼저 계산하여 as_of 기준 immutable snapshot으로 동결하고, AXIS 2는 그 snapshot을 filter/rank/top-N에 사용한다.**

---

## 1. 왜 사전 계산을 기본으로 하는가

시장레짐과 다중종목 비교는 단일종목 DSL의 책임과 계산 형태가 다르다.

```text
Instrument DSL
= 한 종목의 deterministic tactical execution

Cross-sectional selection
= 같은 as_of에서 여러 종목/섹터/시장 feature를 비교
```

이를 DSL 문법/Runtime 안으로 넣으면 다음 문제가 생긴다.

```text
peer universe discovery가 DSL 실행에 침투
종목별 실행 순서에 따라 ranking 결과가 흔들릴 위험
provider/network/DB dependency가 Runtime에 침투
전략 한 번 실행할 때 동일 시장 feature를 반복 계산
backtest/live cutoff 일치 검증이 복잡해짐
AXIS 1과 AXIS 2가 직접 결합됨
```

따라서 selection용 feature는 **precompute -> freeze -> consume**을 기본으로 한다.

---

## 2. 표준 데이터 흐름

```text
Market / Sector / Symbol raw data
        |
        v
[Feature preparation / provider jobs]
  market regime
  beta
  sector strength
  leader/follower evidence
  normalized indicator values
  turnover / capital-flow
        |
        v
Immutable Point-in-Time Feature Snapshot
        |
        v
[AXIS 2 Selection]
  filter
  cross-sectional rank
  top-N
  condition composition
        |
        v
CandidateSetResponse + evidence
```

중요:

```text
AXIS 2 selection request != raw feature calculation request
```

실시간 운용에서 feature snapshot 갱신 주기가 필요하면 별도 provider/precompute job이 정해진 cutoff마다 snapshot을 갱신한다.

---

## 3. 반드시 개발대상에 포함할 feature/selection 능력

### 3.1 Market regime

개발대상:

```text
시장 상승/하락/횡보 regime
trend strength
volatility/range regime
risk-on/risk-off 성격의 검증된 deterministic feature
필요 시 index/market breadth 기반 feature
```

시장레짐은 하나의 거대한 hardcoded 판정함수가 아니라 versioned feature set으로 관리한다.

예:

```text
market.regime_id
market.trend_score
market.range_score
market.volatility_score
market.breadth_score
```

각 값은 `as_of`, source, version, knowledge_cutoff를 가진다.

### 3.2 High-beta universe

개발대상:

```text
benchmark 대비 beta
beta lookback/version
high-beta threshold 또는 percentile
high-beta candidate universe snapshot
```

예:

```text
high_beta_universe(as_of=T)
 -> symbols[]
 -> beta / percentile / evidence
```

### 3.3 Cross-symbol normalized MACD Histogram ranking

필수 사용례:

```text
고베타 종목군
 -> 각 종목의 normalized MACD Histogram snapshot
 -> 동일 as_of 기준 rank
 -> top-N / percentile
```

예:

```text
HIGH_BETA universe
AND hist_normalized rank <= N
```

또는:

```text
hist_normalized_percentile >= P
```

여기서 개별 종목의 normalized Histogram 값도 가능하면 사전에 계산된 snapshot을 사용한다.

AXIS 2가 rank를 만들 때 모든 종목 값의 `as_of/knowledge_cutoff/formula_version`이 동일한 비교 가능 계약을 만족해야 한다.

### 3.4 Leading-sector membership + Histogram ranking

필수 사용례:

```text
시장 전체 sector strength snapshot
 -> 상위 주도섹터 선택
 -> 해당 섹터 constituent universe
 -> normalized MACD Histogram rank
 -> sector 내 top-N 후보
```

예:

```text
TOP_SECTORS(K)
 -> members
 -> hist rank within sector
 -> TOP_N_PER_SECTOR
```

시장 전체 rank와 섹터 내부 rank는 별도 evidence로 보존한다.

### 3.5 Relative strength / turnover / capital-flow

다음도 동일한 precomputed snapshot 방식의 개발대상이다.

```text
relative strength
turnover rank
amount rank
capital-flow proxy
leader/follower bounded evidence
EMA120 position 같은 deterministic per-symbol feature
```

---

## 4. Snapshot 최소 계약

모든 selection feature snapshot은 최소 다음을 가진다.

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
  value
  validity
  provenance
```

cross-sectional rank snapshot은 추가로:

```text
ranking_method
eligible_count
rank
percentile
peer_group_id
```

을 가진다.

fail-closed 원칙:

```text
future value 금지
nearest-time 추정 금지
서로 다른 cutoff 값 혼합 금지
formula version 혼합 금지
필수값 missing 시 임의 0/중립값 대체 금지
```

---

## 5. AXIS 2가 하는 일 / 하지 않는 일

AXIS 2가 하는 일:

```text
immutable feature snapshot 로드
point-in-time validity 확인
filter
rank 또는 이미 동결된 rank 사용
peer-group/sector-group 비교
top-N
Condition CRUD 조합
selection evidence 생성
CandidateSetResponse 반환
```

AXIS 2가 하지 않는 일:

```text
DSL Parser/Runtime 호출로 feature를 반복 계산
Broker 주문 생성
Strategy 실행
Chart 계산
frozen legacy core/ 직접 import
AXIS 1 내부 DB/state 직접 읽기
```

rank도 사전 계산되어 동결할 수 있으면 그 결과를 우선 사용한다. 단, 요청의 Condition CRUD가 top-N/threshold만 다르게 적용하는 경우 동일 frozen feature snapshot 위에서 deterministic rank/filter를 재사용할 수 있다.

---

## 6. AXIS 1과의 관계

AXIS 1은 시장레짐/고베타/섹터/peer ranking을 계산하지 않는다.

필요한 전략은 AXIS 2/provider가 이미 동결한 값을 표준 입력으로 받을 수 있다.

예:

```text
ctx.market.regime_score
ctx.market.trend_score
ctx.selection.beta_percentile
ctx.selection.hist_percentile
ctx.sector.strength
```

단, `ctx.*`는 read-only consumption이고 다음은 금지한다.

```text
ctx가 universe를 검색
ctx가 peer symbols를 조회
DSL Runtime이 rank 계산
DSL Runtime이 sector membership discovery
```

CandidateSet 자체는 AXIS 3가 전략 적용 대상을 정하는 표준 입력이며, AXIS 1에는 필요한 단일종목 execution request만 전달한다.

---

## 7. Backtest / live 동일성

selection snapshot은 live와 backtest 모두 같은 cutoff 원칙을 따른다.

```text
Backtest bar T의 selection
 -> T 시점에 알 수 있었던 snapshot만 사용

next_open execution
 -> prior completed cutoff snapshot만 사용
```

과거 universe constituent, sector membership, beta, rank를 현재 정보로 재구성하면 lookahead이므로 허용하지 않는다.

---

## 8. 개발 우선순위

AXIS 1 migration과 병행 가능한 AXIS 2 설계 backlog:

```text
S0 snapshot schema + provenance/cutoff rules
S1 market regime snapshot
S2 beta/high-beta universe snapshot
S3 normalized Histogram per-symbol snapshot
S4 cross-sectional Histogram rank snapshot
S5 sector strength + constituent snapshot
S6 sector-within Histogram rank
S7 generic Condition CRUD filter/rank/top-N
S8 CandidateSetResponse v1
S9 historical point-in-time replay validation
```

AXIS 1 기능 이식 때문에 이 설계를 폐기하거나 DSL 문법으로 흡수하지 않는다.

---

## 9. 성공 기준

다음 예가 재현 가능하면 핵심 목표를 충족한다.

```text
as_of = T

market regime = TREND_UP
high-beta universe = U1
histogram normalized snapshot = H1
histogram rank snapshot = R1
sector strength snapshot = S1

Condition A:
  U1 중 histogram top 10

Condition B:
  sector strength top 3 소속 종목 중
  sector 내부 histogram top 3

-> CandidateSetResponse
-> 각 후보의 beta / sector / hist value / rank / cutoff evidence 포함
```

동일 snapshot + 동일 Condition version은 언제 실행해도 동일 Candidate Set을 반환해야 한다.

Broader repository compliance가 `REMEDIATION_REQUIRED`이면 이 selection 기능의 focused PASS와 repository-wide compliance PASS를 혼동하지 않는다.
