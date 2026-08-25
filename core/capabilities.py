"""Canonical, machine-readable capabilities exposed to prompt generation."""
DSL_VERSION = "1.4.0"
TA_FUNCTIONS = {
 "ta.sma":"ta.sma(series, period[, bars]) -> series", "ta.ema":"ta.ema(series, period[, bars]) -> series",
 "ta.wma":"ta.wma(series, period[, bars]) -> series", "ta.ma":"ta.ma(series, period, method[, bars]) -> series",
 "ta.rma":"ta.rma(series, period[, bars]) -> series (Wilder)",
 "ta.rsi":"ta.rsi(series, period) 또는 ta.rsi(period) -> series", "ta.crossover":"ta.crossover(series_a, series_b) -> condition",
 "ta.crossunder":"ta.crossunder(series_a, series_b) -> condition", "ta.highest":"ta.highest(series, period[, bars]) -> series",
 "ta.lowest":"ta.lowest(series, period[, bars]) -> series", "ta.sum":"ta.sum(series[, period, bars]) -> series",
 "ta.stdev":"ta.stdev(series, period[, bars]) -> series", "ta.roc":"ta.roc(series, period) -> series",
 "ta.jma":"ta.jma(series, length, phase, power) 또는 ta.jma(length, phase, power) -> trend_series",
 "ta.supertrend":"ta.supertrend(period, multiplier) -> trend_series", "ta.supertrend_direction":"ta.supertrend_direction(period, multiplier) -> direction_series",
 "ta.macd":"ta.macd(series, short, long[, method]) -> series", "ta.atr":"ta.atr(period) -> series",
 "ta.adx":"ta.adx(period) -> series", "ta.trix":"ta.trix(period) -> series", "ta.cci":"ta.cci(period) -> series",
 "ta.nrange":"ta.nrange(period) -> series", "ta.williams_r":"ta.williams_r(period) -> series",
 "ta.abs_range":"ta.abs_range(period) -> series", "ta.sum_abs_r":"ta.sum_abs_r(period) -> series",
 "ta.vhf":"ta.vhf(period) -> series", "ta.shift":"ta.shift(series, bars) -> series",
 "ta.count_since":"ta.count_since(condition, condition) -> series", "ta.bars_since":"ta.bars_since(condition) -> series",
 "ta.highest_since":"ta.highest_since(condition, series) -> series", "ta.lowest_since":"ta.lowest_since(condition, series) -> series",
 "ta.value_when":"ta.value_when(occurrence, condition, series) -> series; occurrence 0=가장 최근",
}
MATH_FUNCTIONS=["math.pow","math.log","math.log10","math.abs","math.sqrt","math.sin","math.cos","math.tan","math.asin","math.acos","math.atan","math.max","math.min","logic.ifelse"]
STATE_FUNCTIONS={
 "state.edge":"조건이 false→true로 바뀐 첫 봉", "state.falling_edge":"조건이 true→false로 바뀐 첫 봉",
 "state.ready_after":"trigger 이후 지정 봉 동안 false", "state.hold":"신호를 지정 봉 동안 유지",
 "state.persist":"조건이 지정 봉 이상 연속 충족", "state.latch":"set/reset 상태 기억",
 "state.count":"reset 사이의 조건 발생 횟수", "state.regime":"bullish/bearish 조건으로 -1/0/1 상태 유지",
}
MTF_FUNCTIONS={"mtf.open":"확정된 상위주기 시가","mtf.high":"확정된 상위주기 고가","mtf.low":"확정된 상위주기 저가","mtf.close":"확정된 상위주기 종가","mtf.volume":"확정된 상위주기 거래량","mtf.sma":"확정된 상위주기 종가 SMA"}
ARTIFACT_TYPES={"indicator":"지표","signal":"신호","strength":"강세·약세","strategy":"전략","drawing":"사용자형식"}
def capability_markdown():
    functions="\n".join(f"- `{value}`" for value in TA_FUNCTIONS.values())
    math=", ".join(f"`{name}`" for name in MATH_FUNCTIONS)
    states="\n".join(f"- `{name}`: {description}" for name,description in STATE_FUNCTIONS.items())
    mtf="\n".join(f"- `{name}`: {description}" for name,description in MTF_FUNCTIONS.items())
    return f"""## 실행기 Capability Manifest
- DSL 버전: `{DSL_VERSION}`
- 시장 데이터: `open`, `high`, `low`, `close`, `volume`, `amount`, `open_interest`, `date`, `time`
- 과거 참조: `close[1]`, `high[2]` 형식만 허용하며 미래 참조는 금지
### TA 함수
{functions}
### 수학·논리 함수
{math}
### 상태 함수
{states}
### 멀티 타임프레임 (lookahead 금지, 완료된 상위 봉만 반환)
{mtf}
"""
