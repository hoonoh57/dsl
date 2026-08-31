# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRATEGY-RESEARCH PHASE / 2026-08-31 KST**

이 문서는 세션 전환 시 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` branch 상태가 가장 높은 권한을 가진다.

**전략 연구 철학의 상세 권한 문서:** `DSL_STRATEGY_RESEARCH_PHILOSOPHY.md`

---

## 1. 세션을 이어갈 때 절대 놓치면 안 되는 핵심

현재 목표는 더 많은 DSL 기능을 무작정 추가하는 것이 아니다.

```text
검증된 DSL Core는 안정적으로 유지
 -> 실제 돈 되는 전략을 만들며 DSL 표현력의 부족을 발견
 -> 기존 DSL 조합으로 되면 Core 수정 금지
 -> 새로운 측정값만 부족하면 additive User Indicator
 -> 전략 자체는 Feature Catalog가 아니라 별도 Strategy CRUD
 -> 차트에서 중간값/threshold/permission을 직접 관찰
 -> 다른 종목/기간/timeframe에서 재검증
```

핵심 문장:

> **DSL은 전략을 결정하지 않는다. 전략가가 원하는 조합을 제한 없이 표현할 수 있게 한다.**

> **차트는 단순 결과 표시가 아니라 전략 개발 계측기다.**

---

## 2. 절대 보존할 Baseline과 오염금지 규칙

현재 차트에 성공적으로 삽입된 기본 `ta.macd` 교차 전략은 Baseline이다.

```text
MACD_BASELINE_V1
```

이 기본 전략과 Feature Catalog 예제를 수익성 개선 목적으로 수정하지 않는다.

```text
Feature Catalog = DSL 기능 검증 SSOT / 기준선 / 불변
Strategy CRUD   = 새로운 전략 실험 / 복제 / 버전 / 비교 / 삭제
```

기존 globally validated Core 로직에 다음과 같은 예외 조항을 넣지 않는다.

```text
if NXT
if _AL
if 5m
if 특정 종목
if 특정 전략
```

새 기능은 additive하게 추가한다. 기존 로직을 바꿔야 한다면 모든 입력/종목/실행경로에 균일하게 적용되는 일반 계약이어야 하며 full regression을 요구한다.

---

## 3. 현재 제품 권한 구조

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
 -> trades / diagnostics / metrics
```

4축 분리:

```text
Chart Core      = generic drawing/pane/geometry
Bridge/Runtime  = lifecycle/routing only
Add-on          = computation meaning/strategy state
JSON            = persistence only
```

Chart는 DSL 계산을 재구현하지 않는다.

---

## 4. DSL Core 기존 trusted checkpoint

Phase 1의 기존 trusted 사용자 화면 결과:

```text
registered feature catalog       75 / 75 PASS
registered execution invariants  23 / 23 PASS
Live Studio direct-Core path     TRUSTED
v2 + v3 + v4 invariant UI        TRUSTED
DSL Core Phase 1                 TRUSTED
```

이 checkpoint는 당시 정의된 Phase 1 기능에 대한 것이다. 이후 additive 기능은 각각 별도로 검증한다.

Broader repository compliance는 계속:

```text
REMEDIATION_REQUIRED
```

이다.

---

## 5. 최근 additive DSL 기능

### `user.macd_normalized`

기존 `ta.macd`는 수정하지 않고 새 사용자지표로 추가했다.

```dsl
user.macd_normalized(series, component[, short, long, signal, method])
```

현재 component:

```text
macd
signal
hist
hist_abs_pct
```

정의:

```text
hist_abs_pct = abs(MACD - Signal) / abs(price) * 100
```

사용자 로컬 focused test:

```text
4 / 4 PASS
```

### `session.day_return_pct()`

범용 정의:

```text
(close / session.day_open() - 1) * 100
```

NXT, `_AL`, live 여부 같은 특수 분기는 없다. 공급된 OHLCV에 동일하게 적용된다.

사용자 로컬 focused test:

```text
4 / 4 PASS
```

---

## 6. Timeframe 최신 결정

DSL은 1d 전용이 아니다. 등록 Feature Catalog 안의 `timeframe = "1d"`는 예제/fixture 기본값이다.

차트 삽입 시 실제 timeframe authority는 **현재 차트 timeframe**이다.

```text
1분 차트  -> DSL 1m
5분 차트  -> DSL 5m
15분 차트 -> DSL 15m
일봉 차트 -> DSL 1d
```

사용자 로컬 확인:

```text
chart_bridge/dsl_chart_timeframe_policy.test.mjs
5 / 5 PASS
```

이후 `chart_platform_server.test.mjs`의 1개 실패는 Guard가 실패한 것이 아니라 오류문구 `day -> 1일` 변경에 예전 테스트 기대문구가 남은 **TEST DEFECT**였고 테스트 기대값만 갱신했다. 최종 rerun 결과는 다음 세션에서 필요하면 확인한다.

사용자 화면에서 `ta.macd`가 현재 1m 차트에 삽입되어:

```text
DSL 차트 삽입 PASS · ta.macd · 1m
```

상태가 확인됐다.

---

## 7. 실행 UX 최신 결정

사용자가 Python/Node 실행명령을 기억하도록 하지 않는다.

루트 엔트리포인트:

```text
start.bat
restart.bat
stop.bat
```

의도:

```text
start.bat
= 관리 대상 서버 초기화 -> Live Studio -> Chart Bridge -> health -> 차트 실행

restart.bat
= 서버 재기동 없이 전용 차트 브라우저만 재실행

stop.bat
= 전용 차트 + 관리 대상 서버 종료
```

프로세스 관리는 `scripts/dsl_stack.ps1`이 담당하고 state/log는 `.runtime/dsl-stack/`에 둔다.

정적 test 파일:

```text
tests/test_dsl_stack_entrypoints.py
```

주의: `tests`는 Python package가 아니므로 잘못된 명령:

```text
python -m unittest tests.test_dsl_stack_entrypoints -v
```

을 사용하지 않는다.

올바른 명령:

```powershell
python -m unittest discover -s tests -p "test_dsl_stack_entrypoints.py" -v
```

이 정적 test의 최종 사용자 PASS는 아직 보고되지 않았다. 차트 실행 화면 자체는 현재 정상 확인됐다.

---

## 8. 현재 전략 연구의 출발점

현재 기본 MACD 교차전략은 횡보/하락추세 구간에서도 상승교차가 발생한다.

이를 없애기 위해 MACD 파라미터를 특정 화면에 맞춰 계속 조정하는 것은 과최적화 위험이 크다.

현재 연구 가설은:

```text
Trigger
= MACD bullish crossover

Permission 후보
= normalized Histogram strength
= JMA normalized slope strength
= 둘의 AND / OR / 선택 조합
= 필요하면 session.day_return_pct 기반 position requirement
```

`0.5` 등의 Histogram 값은 **후보 수평선**이지 최종 상수가 아니다.

정확히 crossover가 발생한 봉에서 어떤 Histogram 값을 평가할지, 현재/최근/확장속도 중 무엇을 사용할지는 아직 결정하지 않았다. 차트를 먼저 보고 결정한다.

---

## 9. JMA 활용 의도

현재 사용하는 JMA 계열에서 전략이 활용하려는 세 관측값:

```text
상승추세 값
하락추세 값
정규화된 slope strength
```

특히 세 번째 slope strength는 normalized trend-strength 후보로 본다.

DSL 전략이 다음을 자유롭게 표현할 수 있어야 한다.

```text
MACD crossover AND hist_strength >= H
MACD crossover AND jma_strength >= J
MACD crossover AND (hist_strength >= H OR jma_strength >= J)
MACD crossover AND hist_strength >= H AND jma_strength >= J
```

Core가 조합을 선택하지 않는다. Strategy CRUD가 선택한다.

---

## 10. 차트 계측 철학

Normalized Histogram과 JMA strength 같은 정규화 값의 중요한 역할은 단순 코드 비교가 아니다.

```text
동일 종목의 이전 수익구간
다른 종목의 수익구간
잡음/횡보 교차구간
```

을 동일 척도로 차트에 그리고 **수평 threshold line**과 비교할 수 있게 하는 것이다.

따라서 전략 판단에 쓰인 값은 DSL/Runtime에서 계산한 그대로 차트로 보내야 한다.

```text
DSL/Runtime
 -> MACD
 -> Signal
 -> Histogram
 -> normalized Histogram
 -> JMA strength
 -> position pct
 -> required threshold
 -> permission bool
 -> trigger
        ↓
Chart = 재계산 없이 표시
```

차트가 보여줘야 할 핵심:

```text
actual strength series
threshold horizontal line
동적 required-strength line
ALLOW / BLOCK / BUY / SELL marker
```

무차별 grid search보다 **차트 관찰 -> 가설 -> 후보 threshold -> 여러 종목 재검증 -> 통계검증** 순서를 우선한다.

---

## 11. 궁극적 종목선별 전략 방향

장기 목표의 한 형태:

```text
지수 고베타 종목
+ 주도섹터 / 대장주 / 추종종목 관계
+ Close > EMA120
+ Normalized Histogram strength/rank
        ↓
강세 후보군 선별
        ↓
MACD + JMA 조합으로 신호 압축
        ↓
종목당 2~3회의 고품질 진입
```

장기적으로 구분:

```text
DSL SYMBOL
= 한 종목 내부 indicator / trigger / permission / execution

DSL UNIVERSE
= 여러 종목 사이 filter / rank / top-N / relative selection
```

하지만 처음부터 Universe 문법을 복잡하게 만들지 않는다. 실제 전략 필요가 확인될 때 일반적인 cross-sectional 기능으로 추가한다.

---

## 12. Strategy CRUD 원칙

수익전략은 Feature Catalog DSL 예제를 수정해 관리하지 않는다.

최소 개념:

```text
strategy_id
name
parent_strategy_id
version
dsl_code
rationale
timeframe
parameters
created_at
validation_status
```

예상 계보:

```text
MACD_BASELINE_V1        [불변]
 -> MACD_HIST_V1
 -> MACD_JMA_V1
 -> MACD_HIST_JMA_V1
 -> MACD_HIST_JMA_POSITION_V1
```

Baseline을 그대로 보존해야 어떤 변경이 실제로 성능을 개선했는지 원인을 추적할 수 있다.

---

## 13. 다음 세션의 즉시 작업

**새 전략을 바로 코딩하지 않는다.** 먼저 현재 DSL의 조합능력을 실제 코드/테스트로 audit한다.

Audit 항목:

```text
1. normalized Histogram 값을 전략이 직접 받을 수 있는가
2. JMA 상승/하락/slope strength를 각각 받을 수 있는가
3. session.day_return_pct()를 받을 수 있는가
4. 위 값들 간 + - * / 및 비교가 가능한가
5. AND / OR / NOT으로 자유롭게 결합 가능한가
6. threshold를 strategy parameter/input으로 변경 가능한가
7. 중간값과 threshold를 차트에 그대로 반환/표시 가능한가
8. Strategy CRUD가 Feature Catalog와 완전히 분리되어 있는가
```

판정 규칙:

```text
모두 가능 -> Core 수정 없음, Strategy CRUD 연구로 이동
일반 문법 부족 -> 전체 DSL에 적용되는 최소 문법 보완
측정값 부족 -> additive User Indicator
차트 observability 부족 -> generic projection/series 계약 보완
Strategy persistence 부족 -> 별도 CRUD 계층 추가
```

---

## 14. `세션이어가!` 복구 규칙

사용자가 새 세션에서 정확히 또는 사실상 같은 의미로:

```text
세션이어가!
```

라고 하면 다음 순서로 즉시 복구한다.

1. `SESSION_HANDOFF.md`를 가장 먼저 읽는다.
2. `DSL_STRATEGY_RESEARCH_PHILOSOPHY.md`를 읽는다.
3. `CURRENT_STATE.md`를 확인한다.
4. `dsl-live-studio` branch의 최신 HEAD를 확인한다.
5. 이 문서의 **13. 다음 세션의 즉시 작업**부터 그대로 이어간다.
6. 이미 문서에 결정된 철학을 다시 처음부터 토론하거나 사용자에게 설명을 요구하지 않는다.
7. 새 executable 변경에 사용자 local PASS가 없으면 `REMOTE_UNVALIDATED`로 표시한다.
8. 기본 `ta.macd` Baseline과 기존 globally validated Core를 수정하지 않는다.

첫 응답은 짧게 다음 3개를 제시하고 바로 작업을 이어간다.

```text
현재 단계
보존할 기준선
바로 할 일
```

---

## 15. 금지된 과장 / 자동 확장

다음을 임의로 주장하거나 시작하지 않는다.

- 현재 전략이 수익성이 검증됐다고 주장
- `0.5` 등 후보 threshold를 검증된 최적값으로 확정
- synthetic fixture를 실전 수익성 근거로 사용
- 출처 미검증 데이터를 real study라고 부르기
- 특정 종목/venue/timeframe 예외를 Core에 삽입
- Strategy 실험 때문에 Feature Catalog baseline을 수정
- adaptive/leader-follower 연구 때문에 Core를 반복 변경
- 모든 DSL 2.0 확장 완료 주장
- live trading readiness 주장

코딩은 로직이 결정된 후 한다.
