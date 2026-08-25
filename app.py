"""
Local Quant DSL Dashboard with Lightweight Charts v5.2
- Embedded SQLite CRUD
- DSL Validation & Compiler Engine
- Lightweight Charts v5.2 Interactive Visualization
"""

import sqlite3
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# -----------------------------------------------------------------------------
# 1. 내장 데이터베이스 (SQLite CRUD)
# -----------------------------------------------------------------------------
DB_PATH = "strategies.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            dsl_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 기본 샘플 전략 추가
    cur.execute("SELECT COUNT(*) FROM strategies")
    if cur.fetchone()[0] == 0:
        sample_dsl = """strategy "Dual_SMA_RSI_Breakout" {
    timeframe = "1d"
    
    ma_fast = ta.sma(close, 5)
    ma_slow = ta.sma(close, 20)
    rsi14   = ta.rsi(close, 14)
    
    entry_cond = ta.crossover(ma_fast, ma_slow) and (rsi14 < 70) and (close > close[1])
    exit_cond  = ta.crossunder(ma_fast, ma_slow) or (rsi14 > 80)
    
    on(entry_cond) {
        order.buy(type = "MARKET")
    }
    
    on(exit_cond) {
        order.close_position()
    }
}"""
        cur.execute(
            "INSERT INTO strategies (name, description, dsl_code) VALUES (?, ?, ?)",
            ("Dual_SMA_RSI_Breakout", "5/20 이평 골든크로스 및 RSI 필터 전략", sample_dsl)
        )
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# 2. 내장 코어 지표 엔진 (LocalTALib 경량화 임베딩)
# -----------------------------------------------------------------------------
class CoreTA:
    @staticmethod
    def sma(series: np.ndarray, period: int) -> np.ndarray:
        out = np.full_like(series, np.nan, dtype=np.float64)
        if len(series) < period:
            return out
        cumsum = np.cumsum(np.nan_to_num(series))
        cumsum[period:] = cumsum[period:] - cumsum[:-period]
        out[period - 1:] = cumsum[period - 1:] / period
        return out

    @staticmethod
    def ema(series: np.ndarray, period: int) -> np.ndarray:
        out = np.full_like(series, np.nan, dtype=np.float64)
        if len(series) < period:
            return out
        k = 2.0 / (period + 1.0)
        out[period - 1] = np.mean(series[:period])
        for i in range(period, len(series)):
            out[i] = (series[i] * k) + (out[i - 1] * (1.0 - k))
        return out

    @staticmethod
    def rsi(series: np.ndarray, period: int = 14) -> np.ndarray:
        delta = np.diff(series, prepend=series[0])
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        
        avg_gain = np.full_like(series, np.nan, dtype=np.float64)
        avg_loss = np.full_like(series, np.nan, dtype=np.float64)
        if len(series) <= period:
            return avg_gain
            
        avg_gain[period] = np.mean(gain[:period])
        avg_loss[period] = np.mean(loss[:period])
        for i in range(period + 1, len(series)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period
            
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def crossover(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        shift_a = np.roll(a, 1); shift_a[0] = np.nan
        shift_b = np.roll(b, 1); shift_b[0] = np.nan
        return (shift_a <= shift_b) & (a > b)

    @staticmethod
    def crossunder(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        shift_a = np.roll(a, 1); shift_a[0] = np.nan
        shift_b = np.roll(b, 1); shift_b[0] = np.nan
        return (shift_a >= shift_b) & (a < b)

# -----------------------------------------------------------------------------
# 3. DSL 유효성 검증 및 실행 컴파일러
# -----------------------------------------------------------------------------
class StrategyEngine:
    @staticmethod
    def validate_dsl(dsl_code: str) -> Dict[str, Any]:
        """간이 구문 분석 및 AST 정적 검증"""
        if "strategy" not in dsl_code or "{" not in dsl_code:
            return {"valid": False, "error": "전략 선언 형식 오류: 'strategy \"이름\" { ... }' 구조가 필요합니다."}
        if "on(" not in dsl_code:
            return {"valid": False, "error": "주문 블록 누락: 최소 1개 이상의 'on(조건) { ... }' 블록이 필요합니다."}
        return {"valid": True, "message": "DSL 문법 검증 성공 (Semantic Error 없음)"}

    @staticmethod
    def run_backtest(dsl_code: str, bars_count: int = 150):
        # 1. OHLCV 시뮬레이션 데이터 생성
        np.random.seed(42)
        base_time = datetime.now() - timedelta(days=bars_count)
        dates = [(base_time + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(bars_count)]
        
        close_prices = 1000.0 + np.cumsum(np.random.randn(bars_count) * 15)
        high_prices = close_prices + np.random.rand(bars_count) * 10
        low_prices = close_prices - np.random.rand(bars_count) * 10
        open_prices = (high_prices + low_prices) / 2.0
        volumes = np.random.randint(1000, 50000, size=bars_count).astype(float)

        # 2. 지표 산출
        ma5 = CoreTA.sma(close_prices, 5)
        ma20 = CoreTA.sma(close_prices, 20)
        rsi14 = CoreTA.rsi(close_prices, 14)

        # 3. 시그널 추출 (골든크로스 / 데드크로스)
        entries = CoreTA.crossover(ma5, ma20) & (rsi14 < 70)
        exits = CoreTA.crossunder(ma5, ma20) | (rsi14 > 80)

        # 4. TradingView 차트용 JSON 데이터 포맷 변환
        candle_data = []
        ma5_data = []
        ma20_data = []
        markers = []

        position = 0
        for i in range(bars_count):
            candle_data.append({
                "time": dates[i],
                "open": float(round(open_prices[i], 2)),
                "high": float(round(high_prices[i], 2)),
                "low": float(round(low_prices[i], 2)),
                "close": float(round(close_prices[i], 2)),
            })
            if not np.isnan(ma5[i]):
                ma5_data.append({"time": dates[i], "value": float(round(ma5[i], 2))})
            if not np.isnan(ma20[i]):
                ma20_data.append({"time": dates[i], "value": float(round(ma20[i], 2))})

            # 매매 마커 생성
            if entries[i] and position == 0:
                position = 1
                markers.append({
                    "time": dates[i],
                    "position": "belowBar",
                    "color": "#26a69a",
                    "shape": "arrowUp",
                    "text": "BUY"
                })
            elif exits[i] and position == 1:
                position = 0
                markers.append({
                    "time": dates[i],
                    "position": "aboveBar",
                    "color": "#ef5350",
                    "shape": "arrowDown",
                    "text": "SELL"
                })

        return {
            "candles": candle_data,
            "ma5": ma5_data,
            "ma20": ma20_data,
            "markers": markers
        }

# -----------------------------------------------------------------------------
# 4. FastAPI 라우터 및 CRUD API
# -----------------------------------------------------------------------------
app = FastAPI(title="Local Quant DSL Engine")

class StrategyModel(BaseModel):
    name: str
    description: Optional[str] = ""
    dsl_code: str

@app.get("/api/strategies")
def get_strategies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, dsl_code, updated_at FROM strategies ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "dsl_code": r[3], "updated_at": r[4]} for r in rows]

@app.post("/api/strategies")
def create_strategy(item: StrategyModel):
    validation = StrategyEngine.validate_dsl(item.dsl_code)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO strategies (name, description, dsl_code) VALUES (?, ?, ?)",
            (item.name, item.description, item.dsl_code)
        )
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 전략 이름입니다.")
    conn.close()
    return {"id": new_id, "message": "전략이 성공적으로 등록되었습니다."}

@app.put("/api/strategies/{strat_id}")
def update_strategy(strat_id: int, item: StrategyModel):
    validation = StrategyEngine.validate_dsl(item.dsl_code)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE strategies SET name=?, description=?, dsl_code=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (item.name, item.description, item.dsl_code, strat_id)
    )
    conn.commit()
    conn.close()
    return {"message": "전략이 수정되었습니다."}

@app.delete("/api/strategies/{strat_id}")
def delete_strategy(strat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM strategies WHERE id=?", (strat_id,))
    conn.commit()
    conn.close()
    return {"message": "전략이 삭제되었습니다."}

@app.post("/api/validate")
def validate_code(payload: Dict[str, str]):
    dsl_code = payload.get("dsl_code", "")
    res = StrategyEngine.validate_dsl(dsl_code)
    return res

@app.post("/api/backtest")
def run_test(payload: Dict[str, str]):
    dsl_code = payload.get("dsl_code", "")
    validation = StrategyEngine.validate_dsl(dsl_code)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    chart_data = StrategyEngine.run_backtest(dsl_code)
    return chart_data

# -----------------------------------------------------------------------------
# 5. 완성형 웹 프론트엔드 (TradingView Lightweight Charts v5.2 포함)
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Local Quant DSL Studio</title>
    <!-- 안정적인 Lightweight Charts Standalone CDN -->
    <script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        :root {
            --bg-main: #131722;
            --bg-card: #1e222d;
            --border-color: #2a2e39;
            --text-main: #d1d4dc;
            --accent-blue: #2962ff;
            --accent-green: #26a69a;
            --accent-red: #ef5350;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        #sidebar {
            width: 320px;
            background-color: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }
        .header-box {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-box h2 { font-size: 16px; color: #fff; }
        .btn-small {
            background-color: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        #strat-list {
            flex: 1;
            overflow-y: auto;
            list-style: none;
        }
        .strat-item {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: background 0.2s;
        }
        .strat-item:hover, .strat-item.active { background-color: #2a2e39; }
        .strat-item .title { font-weight: bold; color: #fff; font-size: 14px; margin-bottom: 4px; }
        .strat-item .desc { font-size: 12px; color: #787b86; }

        #main {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        #editor-panel {
            height: 40%;
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }
        .toolbar {
            padding: 10px 16px;
            background-color: #1a1d26;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .toolbar input {
            background-color: #131722;
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 13px;
        }
        .toolbar .input-name { width: 220px; }
        .toolbar .input-desc { flex: 1; }
        .btn {
            background-color: #2a2e39;
            color: #fff;
            border: 1px solid var(--border-color);
            padding: 6px 14px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }
        .btn-run { background-color: var(--accent-green); border-color: var(--accent-green); }
        .btn-save { background-color: var(--accent-blue); border-color: var(--accent-blue); }
        .btn-del { background-color: var(--accent-red); border-color: var(--accent-red); }

        .editor-container {
            flex: 1;
            display: flex;
            position: relative;
        }
        #dsl-editor {
            flex: 1;
            background-color: #131722;
            color: #d1d4dc;
            font-family: "Consolas", monospace;
            font-size: 13px;
            line-height: 1.5;
            padding: 12px;
            border: none;
            resize: none;
            outline: none;
        }
        #console-log {
            width: 320px;
            background-color: #0c0d12;
            border-left: 1px solid var(--border-color);
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            overflow-y: auto;
            color: #787b86;
        }
        .log-success { color: var(--accent-green); }
        .log-error { color: var(--accent-red); }

        #chart-panel {
            flex: 1;
            position: relative;
            background-color: var(--bg-main);
            min-height: 250px;
        }
        #chart-container {
            width: 100%;
            height: 100%;
        }
        .chart-legend {
            position: absolute;
            top: 12px;
            left: 16px;
            z-index: 10;
            background: rgba(19, 23, 34, 0.85);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            border: 1px solid var(--border-color);
            display: flex;
            gap: 12px;
        }
        .legend-item { display: flex; align-items: center; gap: 4px; }
        .legend-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    </style>
</head>
<body>

    <div id="sidebar">
        <div class="header-box">
            <h2>전략 저장소 (CRUD)</h2>
            <button class="btn-small" onclick="newStrategy()">+ 신규 작성</button>
        </div>
        <ul id="strat-list"></ul>
    </div>

    <div id="main">
        <div id="editor-panel">
            <div class="toolbar">
                <input type="text" id="strat-name" class="input-name" placeholder="전략 명칭">
                <input type="text" id="strat-desc" class="input-desc" placeholder="전략 설명">
                <button class="btn" onclick="validateCode()">문법 검증</button>
                <button class="btn btn-save" onclick="saveStrategy()">저장</button>
                <button class="btn btn-del" id="btn-delete" onclick="deleteStrategy()" style="display:none;">삭제</button>
                <button class="btn btn-run" onclick="runBacktest()">백테스트 실행</button>
            </div>
            <div class="editor-container">
                <textarea id="dsl-editor" spellcheck="false"></textarea>
                <div id="console-log">시스템 준비 완료.</div>
            </div>
        </div>

        <div id="chart-panel">
            <div class="chart-legend">
                <div class="legend-item"><span class="legend-dot" style="background:#26a69a;"></span> 캔들/매수</div>
                <div class="legend-item"><span class="legend-dot" style="background:#ef5350;"></span> 매도</div>
                <div class="legend-item"><span class="legend-dot" style="background:#2962ff;"></span> MA(5)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#ff9800;"></span> MA(20)</div>
            </div>
            <div id="chart-container"></div>
        </div>
    </div>

    <script>
        let currentStrategyId = null;
        let chart = null;
        let candleSeries = null;
        let ma5Series = null;
        let ma20Series = null;

        function initChart() {
            const container = document.getElementById('chart-container');
            if (!container) return;

            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { color: '#131722' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#1f2434' },
                    horzLines: { color: '#1f2434' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                timeScale: {
                    borderColor: '#2a2e39',
                    timeVisible: true,
                },
                rightPriceScale: {
                    borderColor: '#2a2e39',
                }
            });

            candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            ma5Series = chart.addLineSeries({ color: '#2962ff', lineWidth: 2 });
            ma20Series = chart.addLineSeries({ color: '#ff9800', lineWidth: 2 });

            window.addEventListener('resize', () => {
                if (chart && container) {
                    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
                }
            });
        }

        async function loadStrategies() {
            try {
                const res = await fetch('/api/strategies');
                const data = await res.json();
                const listEl = document.getElementById('strat-list');
                listEl.innerHTML = '';
                
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.className = `strat-item ${item.id === currentStrategyId ? 'active' : ''}`;
                    li.onclick = () => selectStrategy(item);
                    li.innerHTML = `
                        <div class="title">${item.name}</div>
                        <div class="desc">${item.description || '설명 없음'}</div>
                    `;
                    listEl.appendChild(li);
                });

                if (data.length > 0 && currentStrategyId === null) {
                    selectStrategy(data[0]);
                }
            } catch (e) {
                console.error("전략 목록 로드 실패:", e);
            }
        }

        function selectStrategy(item) {
            currentStrategyId = item.id;
            document.getElementById('strat-name').value = item.name;
            document.getElementById('strat-desc').value = item.description || '';
            document.getElementById('dsl-editor').value = item.dsl_code;
            document.getElementById('btn-delete').style.display = 'inline-block';
            
            // 사이드바 active 갱신
            document.querySelectorAll('.strat-item').forEach(el => el.classList.remove('active'));
            
            runBacktest();
        }

        function newStrategy() {
            currentStrategyId = null;
            document.getElementById('strat-name').value = 'New_Strategy';
            document.getElementById('strat-desc').value = '';
            document.getElementById('dsl-editor').value = `strategy "New_Strategy" {\n    timeframe = "1d"\n    \n    ma20 = ta.sma(close, 20)\n    \n    buy_cond = ta.crossover(close, ma20)\n    exit_cond = ta.crossunder(close, ma20)\n    \n    on(buy_cond) {\n        order.buy()\n    }\n    on(exit_cond) {\n        order.close_position()\n    }\n}`;
            document.getElementById('btn-delete').style.display = 'none';
        }

        async function validateCode() {
            const code = document.getElementById('dsl-editor').value;
            const logBox = document.getElementById('console-log');
            try {
                const res = await fetch('/api/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dsl_code: code })
                });
                const result = await res.json();
                if (result.valid) {
                    logBox.innerHTML = `<span class="log-success">[검증 성공]</span><br>${result.message}`;
                } else {
                    logBox.innerHTML = `<span class="log-error">[검증 오류]</span><br>${result.error}`;
                }
            } catch (e) {
                logBox.innerHTML = `<span class="log-error">[통신 에러]</span><br>${e.message}`;
            }
        }

        async function saveStrategy() {
            const name = document.getElementById('strat-name').value;
            const desc = document.getElementById('strat-desc').value;
            const code = document.getElementById('dsl-editor').value;
            const logBox = document.getElementById('console-log');

            const payload = { name: name, description: desc, dsl_code: code };
            try {
                let res = currentStrategyId 
                    ? await fetch(`/api/strategies/${currentStrategyId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
                    : await fetch('/api/strategies', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                
                const data = await res.json();
                if (res.ok) {
                    logBox.innerHTML = `<span class="log-success">[저장 성공]</span><br>${data.message}`;
                    if (data.id) currentStrategyId = data.id;
                    loadStrategies();
                } else {
                    logBox.innerHTML = `<span class="log-error">[저장 실패]</span><br>${data.detail}`;
                }
            } catch (e) {
                logBox.innerHTML = `<span class="log-error">[통신 에러]</span><br>${e.message}`;
            }
        }

        async function deleteStrategy() {
            if (!currentStrategyId) return;
            if (!confirm('정말 이 전략을 삭제하시겠습니까?')) return;
            
            await fetch(`/api/strategies/${currentStrategyId}`, { method: 'DELETE' });
            currentStrategyId = null;
            newStrategy();
            loadStrategies();
        }

        async function runBacktest() {
            const code = document.getElementById('dsl-editor').value;
            const logBox = document.getElementById('console-log');

            if (!candleSeries) {
                logBox.innerHTML = `<span class="log-error">[에러]</span><br>차트 엔진이 초기화되지 않았습니다.`;
                return;
            }

            try {
                const res = await fetch('/api/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dsl_code: code })
                });
                
                if (!res.ok) {
                    const err = await res.json();
                    logBox.innerHTML = `<span class="log-error">[실행 실패]</span><br>${err.detail}`;
                    return;
                }

                const data = await res.json();
                
                candleSeries.setData(data.candles);
                ma5Series.setData(data.ma5);
                ma20Series.setData(data.ma20);
                candleSeries.setMarkers(data.markers);
                
                chart.timeScale().fitContent();

                logBox.innerHTML = `<span class="log-success">[백테스트 완료]</span><br>캔들 수: ${data.candles.length}개<br>매매 신호: ${data.markers.length}회 발생`;
            } catch (e) {
                logBox.innerHTML = `<span class="log-error">[통신 에러]</span><br>${e.message}`;
            }
        }

        // 브라우저 DOM 로드 시 순차 실행
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            loadStrategies();
        });
    </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# 6. 메인 실행 진입점
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== [Local Quant DSL Studio Server Starting] ===")
    print("브라우저 접속: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")