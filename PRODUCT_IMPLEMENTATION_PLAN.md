# Quant DSL 제품 상세 구현계획

Status: **AUTHORITATIVE PRODUCT ROADMAP / STAGE 1 EXECUTION PLAN / 2026-08-25 KST**

## 0. 문서 역할과 권위

이 문서는 `hoonoh57/dsl`의 **제품 방향, 단계별 개발 순서, Stage 1 구현 우선순위와 Victory 기준**을 고정한다.

이 문서는 다음 기존 권위를 대체하지 않는다.

1. `QUANT_DSL_PLAYBOOK.md` — LLM이 DSL을 생성·수정할 때 따르는 공식 언어 계약.
2. `DSL_ENGINE_AUDIT.md` — 엔진 신뢰경계, 정확성, 표현력, 주문/회계, 데이터/지표 결함과 기술적 통과 기준.
3. 본 문서 — 무엇을 어떤 순서로 제품화할지 결정하는 제품 로드맵과 Stage 1 실행계획.

현재 HEAD, 테스트 수, 열린 버그, 진행 중 micro-tranche 같은 변동 상태는 이 문서에 박제하지 않는다. 그런 정보는 별도 current-state/handoff 문서가 생기면 그 문서에서 관리한다.

이 문서가 확정하는 가장 중요한 순서는 다음과 같다.

```text
Stage 1  Single-Symbol Strategy Factory 완성
  -> Stage 2  Multi-Symbol Application
  -> Stage 3  Cross-Sectional Selection
  -> Stage 4  Market / Sector / Cascade
  -> Stage 5  Portfolio / Capital Competition
  -> Stage 6  Live / Autonomous Strategy Factory
```

**다종목·시장·섹터·포트폴리오는 전체 제품 설계에 처음부터 포함시키되, Stage 1보다 먼저 구현 우선순위를 가져가지 않는다.**

---

## 1. 최종 제품 정의

최종 제품은 단순한 자연어 전략 생성기가 아니다.

> **AI Quant Strategy Engineering & Optimization Studio**
>
> 자연어, Kiwoom 수식, PineScript 등으로 표현된 전략 아이디어를 검증 가능한 DSL로 컴파일하고, 결정적 실행 엔진으로 전략을 실행·측정하며, 파라미터 탐색과 LLM 구조 개선을 반복하여 전략 연구를 누적·재현·자동화하는 시스템.

최종 제품의 장기 흐름은 다음과 같다.

```text
Natural Language / Kiwoom / Pine
        ↓
Canonical Typed DSL  ← Strategy SSOT
        ↓
Deterministic Execution / Backtest
        ↓
Experiment Evidence
        ↓
Parameter Seeker
        ↓
LLM Structural Improvement
        ↓
Validation / Chart Audit
        ↓
Repeat
        ↓
Multi-Symbol / Relative / Portfolio / Live
```

자연어는 입력 UX이고, **DSL이 전략 의미의 유일한 실행 SSOT**다.

---

## 2. 제품 불변 원칙

### 2.1 DSL SSOT

- 자연어, Visual UI, Kiwoom 수식, PineScript는 모두 DSL의 입력 또는 표현이다.
- Backtest, chart signal, 향후 paper/live 실행은 동일한 DSL 전략 의미를 사용해야 한다.
- LLM이 생성한 임의 Python이나 임의 주문 로직이 DSL을 우회해서는 안 된다.

### 2.2 LLM과 결정적 엔진의 역할 분리

- LLM은 전략 작성자, 분석자, 개선 가설 제안자다.
- Parser/Semantic/Runtime/Backtest/Broker/Seeker는 결정적 프로그램이다.
- LLM은 전략을 바꿀 수 있지만 측정기를 바꿀 수 없다.

즉 향후 Agent에게 허용되는 기본 변경 범위는 다음이다.

```text
허용: DSL, 전략 parameter, optimization configuration, experiment configuration
금지: parser source, indicator reference implementation, backtest accounting,
      broker fill rule, validation assertion, test weakening
```

### 2.3 Fail-Closed

- 이해하지 못한 DSL, 데이터 누락, 미지원 기능, 실행 의미 불일치는 성공으로 간주하지 않는다.
- 조용한 무시, dummy data fallback, 미래 데이터 보정, 임의 nearest-time 대체로 성공을 만들지 않는다.

### 2.4 Experiment Immutability

- Baseline과 모든 개선 iteration은 덮어쓰지 않는다.
- 모든 새 결과는 Parent를 가진 새로운 Experiment/Snapshot이다.
- 성공뿐 아니라 실패, 악화, 과최적화, 모순 결과도 보존한다.

### 2.5 Parameter Search와 Structural Improvement 분리

**Parameter Seeker**는 같은 전략 구조 안에서 숫자를 탐색한다.

```text
period / phase / power / threshold / bars / multiplier / TP / SL ...
```

**LLM Improvement**는 전략 의미 구조를 바꾼다.

```text
entry/exit 구조 / filter / state transition / regime / 재진입 / risk semantics ...
```

LLM이 brute-force parameter search를 대신하거나 Seeker가 조건을 임의 제거·추가해서는 안 된다.

### 2.6 최고수익률 Seeker는 Stage 1 핵심기능

- Maximum Return 탐색은 연구 기능으로 **1급 objective**다.
- 동시에 MDD, trade count, PF, MFE/MAE, 비용 민감도 등 진단치를 반드시 함께 저장한다.
- 최고수익 결과를 자동으로 실전 적합 또는 수익성 보장으로 승격하지 않는다.

### 2.7 사람 개입형 연구가 먼저다

초기에는 사람이 LLM prompt와 결과를 중계한다.

```text
Program result
  -> Human
  -> LLM
  -> Human
  -> DSL input
  -> Program
```

이 단계의 목적은 임시 수작업이 아니라 **실제로 반복 가능한 전략 개선 방법론을 발견하는 것**이다.

방법론이 검증된 후에만 동일 프로토콜을 Agent가 실행하도록 자동화한다.

### 2.8 Chart는 검증 Evidence다

- 숫자 성과만으로 전략 개선을 확정하지 않는다.
- 신호 시점, 진입/청산, MFE/MAE, 지표 상태를 실제 chart time-axis에서 확인할 수 있어야 한다.
- Chart 라이브러리 구현을 DSL 제품에서 중복 소유하지 않는다. `cascading-feature-solution`의 generic Chart SSOT를 donor/shared surface로 재사용하는 방향을 우선한다.

### 2.9 수익 목표의 의미

`Target Return`은 개선 loop를 구동하는 목표가 될 수 있지만 수익을 보장하는 계약이 아니다.

Loop는 다음과 같은 상태로 종료될 수 있다.

```text
TARGET_REACHED
PLATEAU
OVERFIT_RISK
NO_ROBUST_IMPROVEMENT
ITERATION_LIMIT
DATA_OR_ENGINE_BLOCKED
```

---

# 3. 전체 제품 개발 단계

## Stage 1 — Single-Symbol Strategy Factory

한 종목과 한 전략을 대상으로 다음 전체 cycle을 사람의 소스코드 수정 없이 반복할 수 있게 만든다.

```text
Idea
 -> DSL
 -> Validate
 -> Backtest
 -> Snapshot
 -> Parameter Seeker
 -> Best Candidate
 -> Evidence Analysis
 -> LLM Feedback
 -> Revised DSL
 -> Revalidate
 -> Rebacktest
 -> Reoptimize
 -> Compare
 -> Accept / Reject / Stop
```

**현재 최우선 제품 목표다.**

## Stage 2 — Multi-Symbol Application

Stage 1에서 검증된 동일 전략을 여러 종목에 병렬 적용한다.

핵심 질문:

- 한 종목에서 얻은 edge가 다른 종목에서도 유지되는가?
- 전체 종목에 적용할 때 signal breadth는 어느 정도인가?
- 전략의 범용성/종목 의존성이 어떠한가?

Stage 1 엔진을 새로 만들지 않고 `SingleInstrumentContext`를 다수 context로 확장한다.

## Stage 3 — Cross-Sectional Selection

다종목 raw signal을 후보로 보고 상대 비교로 상위 후보만 선택한다.

예:

- KOSPI 고 Beta 상위 N / 상위 %
- 조건검색 포착종목 내 상위 N
- Relative Strength
- 거래대금/모멘텀 rank
- 주도섹터 내 종목 rank
- leader/follower rank

`hoonoh57/db`의 기존 Beta/조건검색/시장 데이터 자산은 이 단계의 donor/oracle로 활용한다.

## Stage 4 — Market / Sector / Cascade

```text
Market Regime
 -> Universe
 -> Sector / Group
 -> Instrument Alpha
 -> Relative Selection
```

시장 선행신호 후 종목 신호, 섹터 leadership 후 leader/follower 확산 같은 causal multi-context 전략을 DSL에 확장한다.

## Stage 5 — Portfolio / Capital Competition

동시 신호를 하나의 실제 자본에서 경쟁시킨다.

- max positions
- capital allocation
- sector concentration
- exposure
- position sizing
- portfolio risk
- 동시 주문 우선순위

개별 종목 backtest 합산이 아니라 global event loop로 평가한다.

## Stage 6 — Live / Autonomous Strategy Factory

검증된 연구 protocol을 Agent와 live/paper 환경으로 확장한다.

```text
Research
 -> Backtest
 -> Optimization
 -> Paper
 -> Live
 -> Live/Backtest divergence
 -> Evidence
 -> Improvement Agent
```

자동화는 Stage 1의 개선 loop가 실제로 반복 가능한 방법론이라는 evidence가 쌓인 뒤 진행한다.

---

# 4. Stage 1 Victory 정의

Stage 1은 기능 메뉴가 존재한다고 끝나지 않는다.

다음 cycle이 **코드 수정 없이** 반복되어야 한다.

```text
Natural language / pasted strategy source
 -> DSL generation or import
 -> fail-closed parse/semantic validation
 -> deterministic single-symbol execution
 -> immutable baseline snapshot
 -> parameter search
 -> best-candidate comparison
 -> evidence report
 -> LLM feedback package generation
 -> revised DSL import
 -> validation
 -> rerun / reseek
 -> accept/reject
 -> chart audit
 -> experiment memory
```

Stage 1 Victory의 필수 조건:

1. 동일 DSL + 동일 데이터 + 동일 execution setting은 동일 결과를 낸다.
2. 사용자가 source code를 고치지 않고 전략 iteration을 반복할 수 있다.
3. Seeker가 고정된 전략 구조의 parameter space를 재현 가능하게 탐색한다.
4. 최고수익 Candidate와 주변 parameter 결과, 거래/위험 진단을 함께 볼 수 있다.
5. LLM에게 전달할 Evidence Package를 프로그램이 자동 생성한다.
6. LLM 응답을 붙여넣으면 DSL extraction → validation → run까지 이어진다.
7. 개선 전/후가 Parent/Child Experiment로 모두 보존된다.
8. LLM이 제안한 변경이 실패해도 실패 episode가 지식으로 남는다.
9. Target Return/iteration/plateau 같은 stop condition으로 반복을 관리한다.
10. chart에서 신호·체결·주요 indicator/evidence를 exact time-axis로 검증할 수 있다.
11. Parser/Backtest/Indicator/Broker 같은 측정기 변경 없이 전략만 반복 개선할 수 있다.
12. 대표 전략군에서 이 cycle을 반복 실행하여 회귀 없이 복구/resume할 수 있다.

Stage 1 Victory는 **수익 보장**이나 특정 목표수익 달성을 의미하지 않는다. Victory는 **수익전략을 연구·개선하는 공정 자체가 결정적이고 재현 가능하며 반복 가능한 상태**를 의미한다.

---

# 5. Stage 1 목표 Architecture

```text
┌────────────────────────────────────────────┐
│ Strategy Input                             │
│ Natural Language / Kiwoom / Pine / DSL     │
└───────────────────┬────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ Prompt / Transpile Layer                   │
│ Playbook + Capability + prior diagnostics  │
└───────────────────┬────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ DSL Compiler                               │
│ Lexer/Parser -> Semantic -> Capability      │
└───────────────────┬────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ Deterministic Single-Symbol Runtime        │
│ State / MTF / Execution / Broker            │
└───────────────────┬────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ Backtest + Evidence Engine                 │
│ trades / equity / MFE-MAE / diagnostics    │
└───────────────────┬────────────────────────┘
                    ↓
             Baseline Snapshot
                    ↓
┌────────────────────────────────────────────┐
│ Parameter Seeker                           │
│ fixed structure -> parameter candidates    │
└───────────────────┬────────────────────────┘
                    ↓
              Best Candidate
                    ↓
┌────────────────────────────────────────────┐
│ Result Analyzer                            │
│ bottleneck / missed edge / failure reason  │
└───────────────────┬────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ LLM Feedback Package                       │
│ evidence + history + target + constraints  │
└───────────────────┬────────────────────────┘
                    ↓
          Human-mediated LLM first
                    ↓
              Revised DSL
                    └─────────────── LOOP
```

Chart Evidence와 Experiment Store는 위 전체 흐름을 가로지르는 cross-cutting subsystem이다.

---

# 6. Stage 1 구현 Workstream

## S1.0 — Authority / State Hygiene

목적: 제품 방향과 변동 상태를 분리하여 세션이 바뀌어도 개발 순서가 흔들리지 않게 한다.

구현:

- 본 문서를 제품 Roadmap authority로 유지.
- 별도 `CURRENT_STATE`/handoff 문서를 추가하여 HEAD, 현재 tranche, 열린 defect, 최근 검증을 관리.
- `DSL_ENGINE_AUDIT.md`의 장기 기술 기준과 현재 구현상태를 분리하는 후속 정리.
- Playbook은 생성 언어 계약으로만 유지하고 제품 Roadmap 내용을 섞지 않는다.

완료 기준:

- 새 세션이 `제품 목적 / 현재 위치 / 다음 tranche / 금지사항`을 repo만 읽고 복구할 수 있다.

---

## S1.1 — Engine Trust Boundary Remediation

목적: Seeker와 LLM Loop가 잘못된 측정기를 최적화하지 않도록 먼저 계산 신뢰도를 고정한다.

우선 검증/수정 대상:

- `next_open` 진입/청산 의미의 완전한 대칭성.
- DAY 주문 session expiry가 실제 Backtest event loop에 연결되는지 검증.
- `tif` 허용값 fail-closed 검증.
- DSL timeframe과 실제 data timeframe mismatch 차단.
- 진입/청산 비용 전체를 포함한 trade PnL, win/loss, equity reconciliation.
- Semantic Analyzer와 `on_bar` runtime 허용 문법 parity.
- Capability Manifest / Semantic signature / Runtime implementation drift 제거.
- 주문 lifecycle transition evidence.
- batch/streaming 확정봉 결과 determinism.

원칙:

- 테스트를 통과시키기 위한 compatibility exception이나 assertion 약화 금지.
- defect는 test defect / product defect / authority drift / environment issue / unknown으로 먼저 분류.

완료 기준:

- Golden execution fixtures에서 동일 전략이 계약한 체결 정책과 회계 결과를 재현.
- `sum(trade pnl)`과 equity change가 정의된 비용 회계 기준으로 reconciliation 가능.

---

## S1.2 — Single-Symbol DSL Capability Completion

목적: Stage 1 전략개발에 필요한 표현력을 DSL 하나로 안정화한다.

필수 범위:

- typed input/parameter.
- series/scalar/function signature 정합성.
- state/cascading logic.
- confirmed-only MTF.
- MARKET/LIMIT/STOP/STOP_LIMIT 주문 의미.
- 재진입/cooldown/state reset.
- strategy output과 visual/evidence output 분리.
- Capability Registry SSOT.

후순위 가능:

- 부분체결.
- 다중 동시 포지션.
- 복잡한 사용자 함수/반복.
- multi-symbol context.

단, 후순위 기능이 특정 Stage 1 reference strategy의 실제 요구를 막는다면 독립 micro-tranche로 승격한다.

완료 기준:

- 대표적인 trend/crossover, filter+state, MTF/stateful 전략을 source surgery 없이 DSL로 표현 가능.

---

## S1.3 — Data Contract / Provenance

목적: 전략 결과가 어떤 데이터로 만들어졌는지 재현 가능하게 한다.

Stage 1 canonical input metadata:

```text
instrument
market
timeframe
start/end
source
adjustment policy
session
bar count
data hash / version
knowledge cutoff where applicable
```

정책:

- data 부족 시 dummy/synthetic fallback 금지.
- 시간 중복/역전, OHLC invalid, timeframe mismatch를 fail-closed 처리.
- 현재 Kiwoom path와 향후 MySQL(`hoonoh57/db`) path는 동일 canonical bar contract로 수렴.

완료 기준:

- 동일 data hash를 가진 Experiment가 동일 입력 series를 재현할 수 있다.

---

## S1.4 — Backtest Evidence Engine

목적: 단순 total return 대신 LLM과 사람이 전략의 병목을 판단할 수 있는 증거를 만든다.

필수 결과:

### Account/Strategy

- total return
- equity curve
- MDD
- trade count
- win rate
- profit factor
- gross/net PnL
- fees/tax/slippage
- exposure/time-in-market

### Trade-level

- signal time
- order time
- fill time/price
- exit time/price
- entry/exit reason
- MFE
- MAE
- realized PnL
- holding bars/time
- execution cost

### Signal diagnostics

- raw condition counts
- entry qualified count
- actual order count
- rejected/skipped reason
- exit reason distribution
- cooldown/reentry suppression count

### Improvement diagnostics

- average MFE vs realized PnL gap
- winning/losing trade distribution
- worst trades
- largest missed moves where measurable without lookahead contamination of execution
- parameter sensitivity summary

완료 기준:

- LLM에게 전략 원문 없이 숫자 한두 개만 던지는 방식이 아니라, 병목을 구분할 수 있는 구조화 Evidence를 생성.

---

## S1.5 — Immutable Experiment Store

목적: 모든 개선 과정을 전략 연구 데이터셋으로 축적한다.

핵심 객체:

```text
ExperimentSnapshot
  experiment_id
  parent_experiment_id
  strategy_source
  normalized DSL
  DSL hash
  data provenance/hash
  execution settings
  parameters
  prompt provenance
  backtest result
  evidence summary
  chart evidence reference
  created_at
```

불변 정책:

- 기존 snapshot update 금지.
- 적용본과 candidate 분리.
- candidate validation 실패가 적용본을 덮어쓰지 않음.

완료 기준:

- 임의 Experiment에서 Parent chain을 따라 baseline까지 복구 가능.

---

## S1.6 — Parameter Seeker

목적: **고정된 전략 구조 안에서 최고수익 parameter와 parameter surface를 탐색**한다.

### UI 입력

각 DSL input/parameter에 대해:

```text
min
max
step or candidate list
search enabled
```

을 설정할 수 있게 한다.

### 1급 Objective

- `MAX_RETURN` — 최고수익률 Seeker.

동시에 모든 candidate에 다음 보조 metric을 저장한다.

- MDD
- trades
- win rate
- PF
- MFE/MAE
- cost

추가 objective는 이후 확장한다.

```text
RETURN_DRAWDOWN
ROBUST_SCORE
CUSTOM_SCORE
```

### Search method 순서

초기:

1. Grid — 정확성과 UI 검증에 유리.
2. Random — 넓은 공간 baseline.

후속:

3. Bayesian/SMBO — 비용이 큰 탐색.
4. Genetic/Evolutionary — 필요성이 evidence로 확인될 때.

방법을 먼저 늘리지 말고 **search result correctness + cache + reproducibility**를 우선한다.

### 필수 시스템 특성

- deterministic seed.
- candidate hash.
- duplicate evaluation cache.
- cancel/resume.
- best-so-far streaming.
- worker/parallelism은 deterministic result를 깨지 않아야 함.
- 동일 parameter set 재실행 결과 일치.

### Output

- Top N candidates.
- best candidate.
- parameter sensitivity.
- 주변 parameter neighborhood.
- run count / skipped duplicate / error count.

완료 기준:

- 사용자가 소스 수정 없이 parameter range를 지정하고 최고수익 candidate를 재현 가능하게 찾을 수 있다.

---

## S1.7 — Result Analyzer

목적: Seeker 결과를 LLM에게 전달하기 전에 프로그램이 구조화된 병목 evidence를 만든다.

Analyzer는 전략을 임의 수정하지 않는다.

예시 진단:

```text
ENTRY_TOO_SPARSE
ENTRY_LOW_DISCRIMINATION
EXIT_MFE_GIVEBACK
STOP_TOO_TIGHT
COST_SENSITIVE
PARAMETER_SPIKE
LOW_TRADE_COUNT
LONG_DRAWDOWN_CLUSTER
PLATEAU
```

각 진단은:

```text
evidence
confidence or rule basis
supporting metrics
contradicting metrics
```

를 가져야 한다.

초기에는 rule-based diagnostics로 시작하고, 충분한 Experiment가 쌓이면 통계/ML 보조를 검토한다.

완료 기준:

- LLM prompt가 `수익률이 낮으니 개선`이 아니라 `관찰된 병목과 근거`를 포함한다.

---

## S1.8 — Human-Mediated LLM Improvement Loop

목적: 완전자동 Agent를 만들기 전에 **전략 개선 방법론 자체를 검증**한다.

초기 workflow:

```text
Program
 -> "LLM 개선 프롬프트 생성"
 -> Human copy
 -> LLM
 -> Human paste response
 -> Program extracts DSL
 -> validate
 -> diff
 -> backtest
 -> seek
 -> compare
 -> snapshot
```

### Feedback Package 필수 내용

- 원래 사용자 intent/prompt.
- 현재 검증 DSL.
- current/baseline experiment.
- 현재 parameters.
- Seeker 범위와 결과.
- Best Candidate.
- trade/signal/MFE/MAE diagnostics.
- Result Analyzer findings.
- 이전 LLM prompt/response 중 관련 기록.
- accepted/rejected prior hypotheses.
- 목표수익률과 현재 gap.
- 변경 제약: **한 iteration에 하나의 주요 구조 가설**.

### LLM 응답 요구

```text
Problem observation
Hypothesis
Single bounded structural change
Expected effect
Full revised DSL
```

### Program side

- DSL extraction.
- fail-closed validation.
- structural diff summary.
- invalid response는 applied candidate를 변경하지 않음.

완료 기준:

- 사람은 LLM 중계와 승인만 수행하고, 실행/측정/저장/비교는 프로그램이 수행.

---

## S1.9 — Improvement Episode Memory

목적: chat history가 아니라 **전략 개선에 실제로 유효한 지식 단위**를 축적한다.

Episode:

```text
Before experiment
Observation
Hypothesis
LLM proposal
Actual DSL change
Expected effect
After-Seeker result
OOS/robustness result when available
Verdict
Reason
```

Verdict 예:

```text
ACCEPTED_IMPROVEMENT
REJECTED_NO_GAIN
REJECTED_REGRESSION
REJECTED_OVERFIT
INCONCLUSIVE
INVALID_DSL
ENGINE_BLOCKED
```

Raw prompt/response는 감사용으로 그대로 보존하고, LLM에는 압축된 Improvement Memory + 필요한 최근 raw evidence만 전달한다.

완료 기준:

- 동일하거나 사실상 동등한 실패 가설을 다음 iteration에서 식별할 수 있다.

---

## S1.10 — Target-Return Improvement Loop

목적: 사용자가 지정한 목표를 향해 반복 연구를 수행하되 무한/무의미한 overfit loop를 방지한다.

초기에는 Human-mediated orchestration이다.

```text
Baseline
 -> Seeker
 -> Analyze
 -> LLM structural change
 -> Validate
 -> Seeker
 -> Compare
 -> Accept/Reject
 -> Stop condition
 -> Repeat
```

### Target

초기 1급 목표:

- `target_return`.

동시에 guard metric을 기록한다.

- MDD
- trade count
- PF
- OOS when enabled
- parameter stability

### Stop Conditions

- target reached.
- iteration limit.
- backtest budget limit.
- N consecutive no-improvement.
- parameter/structure plateau.
- OOS/robustness degradation threshold.
- data/engine block.
- no genuinely new hypothesis.

### Candidate acceptance

LLM revision이 현재 best보다 나쁘면 자동으로 applied best를 덮어쓰지 않는다.

```text
CURRENT_BEST
CANDIDATE
```

를 분리하고 명시적 promote/accept를 거친다.

완료 기준:

- target 도달 여부와 무관하게 loop 종료 이유가 재현 가능하게 기록된다.

---

## S1.11 — Single-Symbol Chart Audit

목적: 숫자 성과와 실제 신호/체결 차트가 동일한 execution evidence를 공유하도록 한다.

우선 요구:

- candle / volume.
- DSL indicator lines.
- BUY/SELL signal.
- actual entry/exit fill marker.
- signal time vs fill time distinction.
- tooltip/inspection evidence.
- MFE/MAE 또는 trade range audit surface.
- baseline/current experiment 비교 진입점.

재사용 방향:

- `hoonoh57/cascading-feature-solution`의 ChartCore/Lightweight chart generic drawing SSOT와 Compare/strategy visualization 자산을 donor로 삼는다.
- DSL 쪽에 별도 chart library direct implementation을 만들지 않는다.
- DSL은 `Validation/Evidence Bundle`을 제공하고 Chart는 feature-blind primitive로 그린다.

완료 기준:

- 임의 trade를 클릭하여 해당 시점 DSL 조건, signal, order/fill, 주요 값과 백테스트 기록을 대조할 수 있다.

---

## S1.12 — Semi-Automation Product UX

목적: Stage 1 전체를 소스 수정 없는 사용자 workflow로 묶는다.

권장 화면:

### Strategy

- original request.
- current DSL.
- validation state.
- ticker/timeframe/date range.

### Run

- baseline/current result.
- chart.
- execution settings.

### Seeker

- parameter ranges.
- objective.
- progress.
- Top N.
- parameter surface/sensitivity.

### Analysis

- signal/trade funnel.
- MFE/MAE.
- diagnostics.

### AI Improvement

- generated feedback prompt.
- LLM response paste.
- proposed change summary.
- validate/run button.

### History

- Experiment lineage.
- accepted/rejected episodes.
- compare two experiments.

완료 기준:

- Stage 1 cycle을 UI/API 조합으로 끝까지 수행 가능.

---

## S1.13 — Methodology Validation

목적: `LLM feedback loop`가 단순히 iteration을 늘리는 것이 아니라 실제 개선에 기여하는지 검증한다.

비교군:

```text
A. Baseline only
B. Baseline + Parameter Seeker
C. Baseline + Seeker + LLM Structural Loop
```

측정:

- best IS improvement.
- OOS improvement when available.
- improvement success rate per structural iteration.
- regression rate.
- overfit rejection rate.
- iterations to improvement.
- backtest budget used.
- repeated/duplicate hypothesis rate.

Prompt protocol도 비교 대상이 될 수 있다.

```text
Result only
+ MFE/MAE
+ signal diagnostics
+ failed hypothesis memory
+ chart evidence summary
```

완료 기준:

- LLM loop가 언제 도움이 되고 언제 해로운지 제품 지식으로 설명 가능.
- Autonomous Agent로 넘길 protocol의 최소 입력/출력/guard가 evidence로 확정.

---

# 7. Stage 1 Automation 성숙도

## 1A — Manual Research Loop

사람이 LLM을 직접 중계한다.

목표:

- 개선에 유효한 Evidence가 무엇인지 발견.
- 좋은/나쁜 prompt pattern 축적.
- Improvement Episode format 확정.

## 1B — Guided Semi-Automation

프로그램이 prompt/evidence를 만들고 결과를 자동 파싱·검증·실행한다.

사람의 역할:

- LLM 중계.
- candidate 승인/거부.
- 목표/연구 방향 판단.

**Stage 1의 현실적 1차 제품 목표는 최소 1B 완성이다.**

## 1C — Autonomous Research Agent

검증된 protocol을 Agent가 실행한다.

Agent tool 권한 예:

```text
read experiment
run backtest
run seeker
read analysis
propose/write candidate DSL
validate DSL
create candidate experiment
```

금지:

```text
modify execution engine
modify accounting
modify validator
modify test oracle
silently promote candidate
```

## 1D — Verified Autonomous Factory

Agent가 장시간 반복 연구를 수행하되 연구예산, target, stop condition, promotion gate를 넘지 않는다.

이 단계는 1A/1B의 Methodology Validation이 성공한 뒤에만 진행한다.

---

# 8. 핵심 데이터 객체 계약

정확한 class/schema 이름은 구현 tranche에서 결정하되 의미 경계는 다음을 유지한다.

## StrategyArtifact

```text
original request/source
normalized DSL
DSL version
Playbook hash
Capability hash
validation result
```

## BacktestRun

```text
strategy artifact
instrument/data provenance
execution settings
parameter set
orders/fills/trades
equity/evidence
```

## SearchStudy

```text
parent experiment
parameter space
objective
method/seed
candidate runs
best candidate
sensitivity
```

## AnalysisReport

```text
metrics
diagnostics
supporting evidence
contradictions
```

## FeedbackPackage

```text
intent
current DSL
baseline/current/best
search summary
analysis
prior relevant episodes
target/gap
change constraints
```

## ImprovementEpisode

```text
before
hypothesis
proposal
change
after
verdict
reason
```

## ExperimentSnapshot

위 객체들을 immutable lineage로 묶는 최상위 연구 기록.

---

# 9. Reuse / Build / Reject Matrix

## `hoonoh57/dsl`

역할:

- **CORE / SSOT**
- DSL compiler/semantic/runtime.
- backtest/broker.
- artifact/validation history.
- Stage 1 Seeker/Improvement orchestration의 본거지.

## `hoonoh57/cascading-feature-solution`

역할:

- **DONOR / SHARED CHART VALIDATION SURFACE**
- generic ChartCore.
- pane/marker/indicator visualization.
- compare subject와 WYSIWYG evidence 경험.

금지:

- DSL repo에서 별도 chart drawing stack을 중복 구현.
- feature-specific drawing을 Chart core에 넣기.

## `hoonoh57/db`

역할:

- **DATA / RESEARCH DONOR & LATER CROSS-SECTIONAL ORACLE**
- 과거 일봉/분봉 데이터 활용 경로.
- 조건검색/백테스트 연구 자산.
- 고 Beta cohort와 향후 sector/relative 연구 donor.

초기 Stage 1에서는 canonical single-symbol Data Provider로 필요한 부분만 연결하고, Beta/Cross-sectional 기능은 Stage 3에서 본격 사용한다.

금지:

- prototype의 dummy fallback을 제품 연구 결과에 사용.
- 기존 monolithic UI/indicator/DB 코드를 그대로 제품 Runtime SSOT로 복제.

---

# 10. 테스트 / 검증 전략

Stage 1에서는 아래 검증 축을 분리한다.

## Compiler/Semantic

- parser fail-closed.
- type/signature.
- invalid order args.
- unsupported capability.

## Indicator

- reference differential fixture.
- prefix/batch parity.
- warmup/NaN.

## Runtime/Execution

- bar_close / next_open.
- state determinism.
- MTF confirmed-only.
- order lifecycle.

## Accounting

- entry/exit cost.
- realized/unrealized.
- trade sum vs equity reconciliation.

## Seeker

- deterministic seed.
- duplicate cache.
- same candidate same result.
- resume/cancel integrity.
- known synthetic objective surface에서 best selection correctness.

## Experiment Store

- immutability.
- lineage.
- candidate does not overwrite applied best.
- prompt/evidence provenance.

## LLM Loop

- invalid response fail-closed.
- one-change contract diagnostics.
- accepted/rejected episode preservation.

## Chart

- marker time == execution evidence.
- indicator values == runtime values.
- WYSIWYG exact-time audit.

## End-to-End Golden Strategies

서로 다른 의미의 대표 전략을 고정하고:

```text
source
 -> DSL
 -> backtest
 -> seeker
 -> feedback candidate
 -> rerun
 -> snapshot lineage
```

전체 경로를 회귀 테스트한다.

---

# 11. 권장 Micro-Tranche 실행 순서

큰 변경을 한 번에 하지 않는다.

## T01 — Product authority checkpoint

- 본 문서 등록.
- 이후 current-state/handoff authority 추가.

## T02 — Execution reconciliation

- `next_open`/비용/PnL/timeframe/TIF/DAY 의미 중 한 경계씩 수정.
- 각 항목별 golden test.

## T03 — Capability SSOT

- manifest/semantic/runtime signature 단일화.

## T04 — Evidence v1

- trade/order/signal/MFE/MAE/account evidence schema.

## T05 — Experiment Snapshot v1

- immutable lineage.

## T06 — Parameter declaration/search contract

- DSL input ↔ UI parameter range ↔ candidate hash.

## T07 — Seeker v1 Grid

- MAX_RETURN.
- Top N.
- deterministic/cancel/resume/cache.

## T08 — Seeker UI + sensitivity

- parameter range editor.
- neighborhood/surface evidence.

## T09 — Result Analyzer v1

- rule-based diagnostics.

## T10 — LLM Feedback Package v1

- prompt generator.
- human copy/paste workflow.

## T11 — Improvement Episode v1

- accepted/rejected knowledge.

## T12 — Target Loop v1

- target/iteration/plateau stop.
- human-mediated orchestration.

## T13 — Single-Symbol Chart Evidence integration

- donor Chart boundary를 재사용.
- exact signal/fill audit.

## T14 — Stage 1 UX integration

- 전략→실행→Seeker→AI 개선→History를 하나의 workflow로 연결.

## T15 — Methodology benchmark

- Baseline vs Seeker vs Seeker+LLM.
- improvement episode 분석.

## T16 — Stage 1 Victory audit

- End-to-End.
- regression.
- WYSIWYG.
- authority/current-state checkpoint.

각 tranche는 원칙적으로:

```text
한 경계 수정
 -> 자동 검증
 -> 필요 시 WYSIWYG
 -> diff/audit
 -> 문서 checkpoint
 -> 다음 tranche
```

순서를 따른다.

---

# 12. Stage 1에서 의도적으로 하지 않을 것

Stage 1의 핵심 loop가 완성되기 전에는 다음을 제품 우선순위로 끌어올리지 않는다.

- 3000종목 global portfolio engine.
- 고 Beta/sector Top-N의 본격 DSL 구현.
- 시장/섹터 multi-context execution.
- portfolio position competition.
- genetic strategy mass generation.
- live autonomous order Agent.
- strategy marketplace/social.
- indicator 개수 경쟁.

단, **Stage 1 architecture는 확장 가능해야 한다.**

즉 현재 구현은 `SingleInstrumentContext`를 쓰되 Stage 2에서 배열/collection context로 확장 가능한 경계를 만든다.

```text
Stage 1
SingleInstrumentContext

Stage 2
InstrumentContext[]

Stage 3+
MarketContext
UniverseContext
GroupContext
InstrumentContext[]
PortfolioContext
```

---

# 13. Stage 2 이후 확장 원칙

Stage 1 Victory 후에는 검증된 Strategy Factory를 버리거나 다시 작성하지 않는다.

확장 순서는:

```text
Single Symbol Strategy
   ↓
Same Strategy × Many Symbols
   ↓
Signal Breadth
   ↓
Cross-Sectional Rank / Top N
   ↓
Market / Sector Context
   ↓
Portfolio Competition
   ↓
Paper / Live
```

개별 종목 raw signal은 Stage 3부터 최종 주문이 아니라 candidate가 될 수 있으며, Point-in-Time universe/rank 원칙을 적용한다.

`cascading-feature-solution`의 multi-chart는 이 단계에서 Top N + near-miss + market/sector evidence viewer로 확장한다.

---

# 14. 최종 성공 형태

Stage 1이 성숙하면 사용자는 개념적으로 다음 작업만 수행한다.

```text
종목 / 기간 / timeframe 선택
전략 아이디어 입력
목표수익률 설정
parameter range 설정
```

시스템은:

```text
DSL 생성/검증
 -> 실행
 -> Baseline 박제
 -> 최고수익률 Seeker
 -> 결과 분석
 -> 개선 Prompt 생성
 -> LLM 응답 적용
 -> 재실행/재탐색
 -> 결과 비교
 -> chart 검증
 -> history 보존
```

을 반복한다.

초기에는 사람이 LLM을 중계하고, 이 순환이 실제 개선 방법론으로 검증되면 동일 protocol을 local execution 권한을 가진 Agent가 수행한다.

제품의 장기 경쟁력은 단순 자연어 생성이 아니라 다음 결합에서 나온다.

> **Typed DSL + Deterministic Backtest + Maximum-Return Seeker + Immutable Experiment Memory + Evidence-Driven LLM Improvement + Exact Chart Validation + 이후 Multi-Symbol/Cross-Sectional/Portfolio 확장**

---

# 15. 현재 다음 작업

본 문서 등록 이후 바로 대규모 기능 구현으로 가지 않는다.

다음 개발 tranche는 Stage 1에서 Seeker와 LLM loop가 신뢰할 수 있는 기반을 만들기 위해 **S1.1 Engine Trust Boundary Remediation을 작은 실행 의미 단위로 시작**한다.

첫 후보는 `next_open` 진입/청산 parity 및 trade/equity cost reconciliation 같이 Backtest 결과를 직접 왜곡할 수 있는 항목이다.

그 다음 Evidence → Snapshot → Parameter Seeker 순으로 올라간다.

**Stage 1 Victory 이전에 다종목/Cross-sectional 기능이 현재 개발 우선순위를 대체하지 않는다.**
