# DSL Three-Axis Final Target

Status: **FINAL PRODUCT ARCHITECTURE TARGET / ACTIVE / 2026-08-31 KST**

이 문서는 현재 DSL 프로젝트의 최종 확장 목표를 정의한다. 목표는 단일 전략 하나를 잘 실행하는 엔진이 아니라, **제약이 적은 DSL 표현력 + 종목군 조건선별 + 전략별 맞춤형 수익화**를 하나의 결정론적 파이프라인으로 연결하는 것이다.

핵심 흐름:

```text
조건선별
 -> 전략
 -> 맞춤형 수익화
```

단, 세 단계의 구현 권한은 분리한다. 하나의 기능을 이유로 다른 축의 Core 로직을 오염시키지 않는다.

---

## AXIS 1. DSL Capability Engine

### 목적

DSL 자체가 독립적으로도 완전한 전략 표현언어가 되어야 한다.

```text
낮은 표현 제약
+ deterministic execution
+ MTF
+ cascading/context knowledge
+ built-in indicators
+ additive user indicators
+ arithmetic/comparison/boolean composition
+ state/order/execution/risk
+ chart-observable intermediate values
```

DSL은 특정 전략을 하드코딩하는 장소가 아니다. 전략가가 원하는 조합을 가능한 한 제한 없이 표현할 수 있어야 한다.

예:

```text
MTF trend
AND close > EMA120
AND normalized MACD Histogram strength >= H
AND/OR JMA normalized slope strength >= J
AND parent/cascading context condition
AND position permission
 -> trigger
 -> order / risk / exit
```

### 확장 규칙

1. 기존 DSL 조합으로 표현 가능하면 Core 수정 금지.
2. 새로운 측정값만 부족하면 additive User Indicator.
3. 일반 문법 자체가 부족할 때만 모든 전략에 적용되는 범용 문법을 최소 tranche로 추가.
4. 특정 종목/venue/timeframe/전략 예외 분기 금지.
5. Feature Catalog는 기능 검증 SSOT이며 수익성 연구로 수정하지 않는다.

### cascading knowledge

상위/외부 지식이 필요한 경우 Core 내부에 숨은 판단을 넣지 않는다.

```text
external/context provider
 -> exact deterministic binding
 -> DSL-visible context
 -> Strategy에서 명시적으로 사용
```

즉 cascading 지식은 DSL의 입력 능력을 확장하지만 DSL 실행 권한을 대체하지 않는다.

---

## AXIS 2. Semi-Condition Selection

### 목적

전략 실행 전에 **매매할 가치가 있는 후보군을 좁히는 cross-sectional selection 계층**을 둔다.

이 축은 단일 종목 진입신호를 만드는 DSL SYMBOL과 구분한다.

예상 조건:

```text
지수 고베타 종목
주도섹터 강세
대장주 / 추종종목 관계
Close > EMA120
당일 position
Normalized Histogram strength / rank
상대강도
거래대금 / 자금유입
기타 검증된 semi-condition
```

결과는 주문이 아니라 **Candidate Set**이다.

```text
Universe
 -> filter
 -> rank
 -> top-N
 -> candidate evidence/reasons
 -> Candidate Set
```

### 핵심 원칙

Semi-Condition Selection은 Strategy DSL을 오염시키지 않는다.

```text
Selector = 누구를 볼 것인가
Strategy = 그 종목에서 언제/어떻게 거래할 것인가
```

선별 엔진은 일반적인 filter/rank/top-N/relative-selection 능력을 우선한다. 특정 전략을 위해 고베타/섹터/EMA120 조합을 Core에 한 덩어리 함수로 하드코딩하지 않는다.

조건식은 향후 별도 CRUD/registry를 가질 수 있다.

```text
Condition CRUD
!= Feature Catalog
!= Strategy CRUD
```

필요하면 selector 결과와 근거를 DSL context로 전달할 수 있지만, 그 binding은 명시적이고 재현 가능해야 한다.

---

## AXIS 3. Strategy Monetization

### 목적

선별된 후보군에 대해 다양한 DSL 전략을 적용하고, 전략별로 검증·버전·비교하여 맞춤형 수익구조를 만든다.

```text
Candidate Set
 -> Strategy CRUD
 -> DSL compile/execute
 -> chart observability
 -> backtest / validation
 -> compare / promote / reject
 -> tailored monetization
```

### Strategy CRUD

기본 Feature Catalog 예제를 수정하지 않는다.

```text
Feature Catalog = DSL 기능 검증 / 불변
Condition CRUD  = 후보선별 규칙 / 버전
Strategy CRUD   = 수익전략 / 복제 / 버전 / 비교 / 폐기
```

Baseline:

```text
MACD_BASELINE_V1 [불변]
```

예상 전략 계보:

```text
MACD_BASELINE_V1
 -> MACD_HIST_V1
 -> MACD_JMA_V1
 -> MACD_HIST_JMA_V1
 -> MACD_HIST_JMA_POSITION_V1
 -> selected-universe variants
```

### 맞춤형 수익화의 의미

모든 종목에 동일한 전략 하나를 강제하는 것이 목표가 아니다.

```text
후보군 특성
+ timeframe
+ normalized strength
+ trend regime
+ position/context
 -> 적합한 Strategy version 선택
 -> 소수의 고품질 진입
```

전략 성능 차이는 반드시 Baseline과 비교 가능해야 한다.

---

## 3축 통합 실행 구조

최종 구조:

```text
[Market / Context / Cascading Knowledge]
                |
                v
[AXIS 2: Semi-Condition Selection]
 filter / rank / top-N / evidence
                |
                v
          Candidate Set
                |
                v
[AXIS 1: DSL Capability Engine]
 MTF / indicators / user indicators / context / logic / execution
                |
                v
[AXIS 3: Strategy Monetization]
 Strategy CRUD / chart / backtest / compare / promote
                |
                v
      Tailored Profit Strategy
```

실제 구현에서는 AXIS 1이 실행 엔진이고, AXIS 2와 AXIS 3이 그 위에서 독립적으로 조합되는 제품 계층이다.

---

## Chart의 역할

차트는 세 축을 연결하는 인간 검증 계측기다.

```text
Selector evidence
Strategy intermediate values
Normalized Histogram
JMA strength
position pct
threshold / required line
permission
trigger
BUY / SELL
```

을 가능한 한 동일 화면에서 추적할 수 있어야 한다.

중요:

```text
Chart는 계산하지 않는다.
Selector/DSL/Strategy가 계산한 값을 projection으로 표시한다.
```

정규화된 값은 특히 종목 간 비교와 동일 종목 과거 수익구간 비교를 위해 수평선/series로 관찰 가능해야 한다.

---

## 연구 및 최적화 철학

무차별 parameter search부터 시작하지 않는다.

```text
차트 관찰
 -> 반복 구조 발견
 -> 정규화 측정값 확인
 -> 후보 threshold/condition 가설
 -> Condition CRUD / Strategy CRUD 새 버전
 -> 다른 종목/기간/timeframe 검증
 -> 통계/백테스트 확대
 -> 채택 또는 폐기
```

이를 통해 특정 화면에 맞춘 과최적화보다 설명 가능한 구조적 개선을 우선한다.

---

## 최종 단계 완료 기준

프로젝트의 최종 확장단계는 다음 세 축이 각각 독립적으로 유효하고 함께 실행될 때 완료로 본다.

### AXIS 1 완료

```text
DSL이 전략 작성에 필요한 일반 조합을 큰 제약 없이 표현
MTF 사용 가능
cascading/context 명시적 사용 가능
새 지표 additive 등록 가능
중간값 chart projection 가능
결정론적 Backtest/Broker 계약 유지
```

### AXIS 2 완료

```text
여러 종목 universe 입력
일반 filter/rank/top-N
cross-sectional normalized metrics
고베타/강세/sector/leader-follower 등 외부·계산 feature 사용
선별근거 evidence 출력
Candidate Set 재현 가능
```

### AXIS 3 완료

```text
Condition CRUD와 Strategy CRUD 분리
Baseline 불변
전략 lineage/version/compare
Candidate Set -> Strategy 실행
차트 시각검증
백테스트/통계검증
채택/폐기 가능한 전략 연구 workflow
```

### End-to-End 완료

```text
조건선별
 -> 후보군
 -> DSL 전략
 -> 차트 이유 검증
 -> 백테스트/비교
 -> 전략별 맞춤형 수익화
```

이 End-to-End가 동일한 deterministic authority와 provenance 아래에서 재현 가능해야 한다.

---

## 절대 금지

다음을 이유로 3축을 섞지 않는다.

```text
특정 전략을 DSL Core 함수로 하드코딩
특정 종목/venue/timeframe 예외를 기존 검증 Core에 추가
Selector가 직접 주문 의미를 소유
Chart가 지표/조건을 재계산
Strategy 연구 때문에 Feature Catalog baseline 수정
adaptive/AI가 DSL/runtime를 숨게 변경
```

3축의 강점은 기능 수가 아니라 **분리된 권한을 유지하면서 자유롭게 결합할 수 있다는 것**이다.

---

## 현재 단계에서의 다음 작업

최종 목표가 상향되었어도 현재 micro-tranche는 바뀌지 않는다.

먼저 AXIS 1의 현재 조합능력 audit를 끝낸다.

```text
1. normalized Histogram direct strategy access
2. JMA up/down/normalized slope direct access
3. session.day_return_pct direct access
4. arithmetic/comparison
5. AND/OR/NOT
6. strategy parameter/input thresholds
7. intermediate values/threshold -> chart projection
8. Strategy CRUD vs Feature Catalog separation
```

그 결과를 기반으로 부족한 AXIS 1 능력만 보완한 뒤, AXIS 2의 최소 generic selection contract를 설계한다.
