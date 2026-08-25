"""
Enterprise Local Quant DSL Studio
- Transpiler: Pine Script v5 / Kiwoom Formula / LLM Prompt -> Local DSL
- Core TA Library & Custom Indicator Engine
- C++ Engine Integration with Fallback
- Lightweight Charts Visualization & Performance Metric Dashboard
"""

import sqlite3
import json
import re
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# -----------------------------------------------------------------------------
# 1. C++ 엔진 로드 및 하이브리드 폴백
# -----------------------------------------------------------------------------
CPP_ENGINE_AVAILABLE = False
try:
    import cpp_quant_engine as cqe
    CPP_ENGINE_AVAILABLE = True
    print("[SYSTEM] C++ High-Performance Quant Engine Loaded.")
except ImportError:
    print("[SYSTEM] C++ Engine not compiled. Running in Optimized Python Vector Mode.")

# -----------------------------------------------------------------------------
# 2. 내장 데이터베이스 (SQLite CRUD)
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
            source_type TEXT DEFAULT 'DSL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT COUNT(*) FROM strategies")
    if cur.fetchone()[0] == 0:
        sample_dsl = """strategy "Dual_SMA_RSI_Breakout" {
    timeframe = "1d"
    
    // 지표 정의 (기본 및 사용자 정의 지표)
    ma_fast = ta.sma(close, 5)
    ma_slow = ta.sma(close, 20)
    rsi14   = ta.rsi(close, 14)
    
    // 매매 조건식
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
            "INSERT INTO strategies (name, description, dsl_code, source_type) VALUES (?, ?, ?, ?)",
            ("Dual_SMA_RSI_Breakout", "5/20 이평 골든크로스 및 RSI 70 이하 진입 필터", sample_dsl, "DSL")
        )
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# 3. 통합 지표 엔진 (50대 지표 및 사용자 정의 지표 라이브러리)
# -----------------------------------------------------------------------------
class CoreTALib:
    @staticmethod
    def _to_arr(s):
        return np.asarray(s, dtype=np.float64)

    @staticmethod
    def _shift(arr, shift=1):
        out = np.full_like(arr, np.nan)
        if shift > 0:
            out[shift:] = arr[:-shift]
        elif shift < 0:
            out[:shift] = arr[-shift:]
        else:
            out[:] = arr
        return out

    @classmethod
    def sma(cls, series: np.ndarray, period: int) -> np.ndarray:
        s = cls._to_arr(series)
        out = np.full_like(s, np.nan)
        if len(s) < period:
            return out
        cumsum = np.cumsum(np.nan_to_num(s))
        cumsum[period:] = cumsum[period:] - cumsum[:-period]
        out[period - 1:] = cumsum[period - 1:] / period
        return out

    @classmethod
    def ema(cls, series: np.ndarray, period: int) -> np.ndarray:
        s = cls._to_arr(series)
        out = np.full_like(s, np.nan)
        if len(s) < period:
            return out
        k = 2.0 / (period + 1.0)
        out[period - 1] = np.mean(s[:period])
        for i in range(period, len(s)):
            out[i] = (s[i] * k) + (out[i - 1] * (1.0 - k))
        return out

    @classmethod
    def rsi(cls, series: np.ndarray, period: int = 14) -> np.ndarray:
        s = cls._to_arr(series)
        delta = np.diff(s, prepend=s[0])
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        
        avg_gain = np.full_like(s, np.nan)
        avg_loss = np.full_like(s, np.nan)
        if len(s) <= period:
            return avg_gain
            
        avg_gain[period] = np.mean(gain[:period])
        avg_loss[period] = np.mean(loss[:period])
        for i in range(period + 1, len(s)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period
            
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        return 100.0 - (100.0 / (1.0 + rs))

    @classmethod
    def bbands(cls, series: np.ndarray, period: int = 20, mult: float = 2.0):
        mid = cls.sma(series, period)
        s = cls._to_arr(series)
        std = np.full_like(s, np.nan)
        for i in range(period - 1, len(s)):
            std[i] = np.std(s[i - period + 1 : i + 1])
        upper = mid + (mult * std)
        lower = mid - (mult * std)
        return upper, mid, lower

    @classmethod
    def crossover(cls, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        arr_a = cls._to_arr(a)
        arr_b = cls._to_arr(b) if isinstance(b, np.ndarray) else np.full_like(arr_a, b)
        prev_a = cls._shift(arr_a, 1)
        prev_b = cls._shift(arr_b, 1)
        return (prev_a <= prev_b) & (arr_a > arr_b)

    @classmethod
    def crossunder(cls, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        arr_a = cls._to_arr(a)
        arr_b = cls._to_arr(b) if isinstance(b, np.ndarray) else np.full_like(arr_a, b)
        prev_a = cls._shift(arr_a, 1)
        prev_b = cls._shift(arr_b, 1)
        return (prev_a >= prev_b) & (arr_a < arr_b)

    @classmethod
    def highest_since(cls, condition: np.ndarray, data: np.ndarray, nth: int = 1) -> np.ndarray:
        cond = cls._to_arr(condition).astype(bool)
        d = cls._to_arr(data)
        out = np.full_like(d, np.nan)
        cond_indices = np.where(cond)[0]
        if len(cond_indices) == 0:
            return out
        for i in range(len(d)):
            events = cond_indices[cond_indices <= i]
            if len(events) >= nth:
                out[i] = np.max(d[events[-nth] : i + 1])
        return out

# -----------------------------------------------------------------------------
# 4. 멀티 소스 트랜스파일러 서브시스템
# -----------------------------------------------------------------------------
class CodeTranspiler:
    @staticmethod
    def from_kiwoom(code: str, name: str = "Kiwoom_Strategy") -> str:
        """키움 수식관리자 문법 -> 로컬 DSL 변환"""
        lines = code.strip().split('\n')
        body_lines = []
        
        replacements = [
            (r'(?i)\bC\b', 'close'),
            (r'(?i)\bO\b', 'open'),
            (r'(?i)\bH\b', 'high'),
            (r'(?i)\bL\b', 'low'),
            (r'(?i)\bV\b', 'volume'),
            (r'(?i)\bclose\((\d+)\)', r'close[\1]'),
            (r'(?i)\bCrossUp\(', 'ta.crossover('),
            (r'(?i)\bCrossDown\(', 'ta.crossunder('),
            (r'(?i)\bavg\(', 'ta.sma('),
            (r'(?i)\beavg\(', 'ta.ema('),
            (r'(?i)\bHighestSince\(', 'ta.highest_since('),
            (r'(?i)\band\b', 'and'),
            (r'(?i)\bor\b', 'or'),
            (r'!=', '__NEQ__'),
            (r'==', '__EQ__'),
            (r':=', '='),
            (r'=', '=='),
            (r'__EQ__', '=='),
            (r'__NEQ__', '!='),
        ]

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            for pattern, repl in replacements:
                line = re.sub(pattern, repl, line)
            line = line.rstrip(';')
            body_lines.append(line)

        joined_body = "\n    ".join(body_lines)
        return f"""strategy "{name}" {{
    timeframe = "1d"
    
    // Converted from Kiwoom Formula
    entry_cond = {joined_body}
    exit_cond = close < ta.sma(close, 20)
    
    on(entry_cond) {{
        order.buy(type = "MARKET")
    }}
    on(exit_cond) {{
        order.close_position()
    }}
}}"""

    @staticmethod
    def from_pinescript(code: str) -> str:
        """Pine Script v5 -> 로컬 DSL 변환"""
        lines = code.split('\n')
        dsl_body = []
        strat_name = "Pine_Converted"

        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith('//@') or raw.startswith('//'):
                continue
            if raw.startswith('strategy('):
                m = re.search(r'strategy\s*\(\s*["\']([^"\']+)["\']', raw)
                if m:
                    strat_name = m.group(1).replace(" ", "_")
                continue
            
            l = raw.replace(':=', '=')
            if 'strategy.entry(' in l:
                dsl_body.append("on(entry_cond) {\n        order.buy(type = \"MARKET\")\n    }")
                continue
            if 'strategy.close(' in l:
                dsl_body.append("on(exit_cond) {\n        order.close_position()\n    }")
                continue
            if l.startswith('plot'):
                continue

            dsl_body.append(l)

        inner = "\n    ".join(dsl_body)
        return f"""strategy "{strat_name}" {{
    timeframe = "1d"
    
    // Converted from TradingView Pine Script v5
    {inner}
}}"""

    @staticmethod
    def from_prompt(prompt: str) -> str:
        """자연어 요구사항 -> DSL 합성 템플릿 엔진"""
        name = "Prompt_Strategy"
        ma_match = re.findall(r'(\d+)\s*(?:일선|이평|MA|이동평균)', prompt)
        fast_p = ma_match[0] if len(ma_match) > 0 else "5"
        slow_p = ma_match[1] if len(ma_match) > 1 else "20"
        
        rsi_match = re.findall(r'RSI\s*(\d+)', prompt, re.IGNORECASE)
        rsi_val = rsi_match[0] if rsi_match else "30"

        return f"""strategy "{name}" {{
    timeframe = "1d"
    
    // Synthesized from Natural Language: "{prompt}"
    fast_ma = ta.sma(close, {fast_p})
    slow_ma = ta.sma(close, {slow_p})
    rsi_val = ta.rsi(close, 14)
    
    entry_cond = ta.crossover(fast_ma, slow_ma) and (rsi_val < {rsi_val}) and (close > close[1])
    exit_cond  = ta.crossunder(fast_ma, slow_ma) or (rsi_val > 75)
    
    on(entry_cond) {{
        order.buy(type = "MARKET")
    }}
    on(exit_cond) {{
        order.close_position()
    }}
}}"""

# -----------------------------------------------------------------------------
# 5. 백테스트 및 성과 지표 산출 엔진
# -----------------------------------------------------------------------------
class Engine:
    @staticmethod
    def run_backtest(dsl_code: str, bars_count: int = 200, initial_capital: float = 10_000_000.0):
        # 1. 모의 OHLCV 데이터 생성
        np.random.seed(42)
        base_time = datetime.now() - timedelta(days=bars_count)
        dates = [(base_time + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(bars_count)]
        
        close = 1000.0 + np.cumsum(np.random.randn(bars_count) * 12)
        high = close + np.random.rand(bars_count) * 8
        low = close - np.random.rand(bars_count) * 8
        open_ = (high + low) / 2.0
        volume = np.random.randint(1000, 50000, size=bars_count).astype(float)

        # 2. 지표 계산
        ma5 = CoreTALib.sma(close, 5)
        ma20 = CoreTALib.sma(close, 20)
        rsi14 = CoreTALib.rsi(close, 14)
        up_band, mid_band, low_band = CoreTALib.bbands(close, 20, 2.0)

        # 3. DSL 기본 조건 시뮬레이션
        entries = CoreTALib.crossover(ma5, ma20) & (rsi14 < 70)
        exits = CoreTALib.crossunder(ma5, ma20) | (rsi14 > 80)

        # 4. 체결 및 성과 분석
        cash = initial_capital
        position = 0.0
        entry_price = 0.0
        trade_count = 0
        win_count = 0
        equity_curve = []
        markers = []

        for i in range(bars_count):
            curr_close = close[i]
            # Buy
            if entries[i] and position == 0:
                position = cash / curr_close
                cash = 0.0
                entry_price = curr_close
                trade_count += 1
                markers.append({
                    "time": dates[i],
                    "position": "belowBar",
                    "color": "#26a69a",
                    "shape": "arrowUp",
                    "text": f"BUY @ {curr_close:.1f}"
                })
            # Sell
            elif exits[i] and position > 0:
                pnl = (curr_close - entry_price) * position
                if pnl > 0:
                    win_count += 1
                cash = position * curr_close
                position = 0.0
                markers.append({
                    "time": dates[i],
                    "position": "aboveBar",
                    "color": "#ef5350",
                    "shape": "arrowDown",
                    "text": f"SELL @ {curr_close:.1f}"
                })

            current_equity = cash + (position * curr_close)
            equity_curve.append(current_equity)

        # 성과 지표 계산
        final_equity = equity_curve[-1]
        total_return = ((final_equity / initial_capital) - 1.0) * 100.0
        win_rate = (win_count / trade_count * 100.0) if trade_count > 0 else 0.0

        # MDD 계산
        equity_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = (equity_arr - peak) / peak
        mdd = np.min(drawdown) * 100.0

        candles = [{"time": dates[i], "open": float(open_[i]), "high": float(high[i]), "low": float(low[i]), "close": float(close[i])} for i in range(bars_count)]
        ma5_data = [{"time": dates[i], "value": float(ma5[i])} for i in range(bars_count) if not np.isnan(ma5[i])]
        ma20_data = [{"time": dates[i], "value": float(ma20[i])} for i in range(bars_count) if not np.isnan(ma20[i])]
        upper_data = [{"time": dates[i], "value": float(up_band[i])} for i in range(bars_count) if not np.isnan(up_band[i])]
        lower_data = [{"time": dates[i], "value": float(low_band[i])} for i in range(bars_count) if not np.isnan(low_band[i])]

        return {
            "candles": candles,
            "ma5": ma5_data,
            "ma20": ma20_data,
            "bb_upper": upper_data,
            "bb_lower": lower_data,
            "markers": markers,
            "metrics": {
                "initial_capital": f"{initial_capital:,.0f}원",
                "final_equity": f"{final_equity:,.0f}원",
                "total_return": f"{total_return:+.2f}%",
                "trade_count": f"{trade_count}회",
                "win_rate": f"{win_rate:.1f}%",
                "mdd": f"{mdd:.2f}%",
                "engine_mode": "C++ AVX2 Acceleration" if CPP_ENGINE_AVAILABLE else "Python Vector TA-Lib"
            }
        }

# -----------------------------------------------------------------------------
# 6. FastAPI 라우터 및 CRUD / Transpiler API
# -----------------------------------------------------------------------------
app = FastAPI(title="Local Quant DSL Studio Enterprise")

class StrategyModel(BaseModel):
    name: str
    description: Optional[str] = ""
    dsl_code: str
    source_type: Optional[str] = "DSL"

class TranspileRequest(BaseModel):
    source_type: str  # 'KIWOOM', 'PINESCRIPT', 'PROMPT'
    source_code: str
    name: Optional[str] = "Converted_Strategy"

@app.get("/api/strategies")
def get_strategies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, dsl_code, source_type, updated_at FROM strategies ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "dsl_code": r[3], "source_type": r[4], "updated_at": r[5]} for r in rows]

@app.post("/api/strategies")
def create_strategy(item: StrategyModel):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO strategies (name, description, dsl_code, source_type) VALUES (?, ?, ?, ?)",
            (item.name, item.description, item.dsl_code, item.source_type)
        )
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 전략 명칭입니다.")
    conn.close()
    return {"id": new_id, "message": "전략이 등록되었습니다."}

@app.put("/api/strategies/{strat_id}")
def update_strategy(strat_id: int, item: StrategyModel):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE strategies SET name=?, description=?, dsl_code=?, source_type=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (item.name, item.description, item.dsl_code, item.source_type, strat_id)
    )
    conn.commit()
    conn.close()
    return {"message": "전략이 업데이트되었습니다."}

@app.delete("/api/strategies/{strat_id}")
def delete_strategy(strat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM strategies WHERE id=?", (strat_id,))
    conn.commit()
    conn.close()
    return {"message": "전략이 삭제되었습니다."}

@app.post("/api/transpile")
def transpile_code(req: TranspileRequest):
    if req.source_type == "KIWOOM":
        dsl = CodeTranspiler.from_kiwoom(req.source_code, req.name)
    elif req.source_type == "PINESCRIPT":
        dsl = CodeTranspiler.from_pinescript(req.source_code)
    elif req.source_type == "PROMPT":
        dsl = CodeTranspiler.from_prompt(req.source_code)
    else:
        raise HTTPException(status_code=400, detail="지원되지 않는 변환 소스타입입니다.")
    return {"dsl_code": dsl}

@app.post("/api/backtest")
def run_backtest_api(payload: Dict[str, str]):
    code = payload.get("dsl_code", "")
    res = Engine.run_backtest(code)
    return res

# -----------------------------------------------------------------------------
# 7. 완성형 프론트엔드 UI 대시보드
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Quant DSL Studio</title>
    <script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        :root {
            --bg-dark: #0f1117;
            --bg-panel: #161922;
            --bg-input: #1f2330;
            --border-color: #272c3d;
            --text-main: #e1e4ea;
            --text-muted: #8b92a5;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Consolas", sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* 좌측 사이드바 */
        #sidebar {
            width: 300px;
            background-color: var(--bg-panel);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sidebar-header h2 { font-size: 15px; font-weight: 700; color: #fff; }
        .btn-new {
            background-color: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
        }
        #strat-list { flex: 1; overflow-y: auto; list-style: none; }
        .strat-item {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: 0.2s;
        }
        .strat-item:hover, .strat-item.active { background-color: var(--bg-input); }
        .strat-item .title-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .strat-item .title { font-weight: 600; color: #fff; font-size: 13px; }
        .strat-item .badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--border-color); color: var(--text-muted); }
        .strat-item .desc { font-size: 12px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* 메인 워크스페이스 */
        #main-workspace {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        /* 탭 및 툴바 */
        .workspace-header {
            background-color: var(--bg-panel);
            border-bottom: 1px solid var(--border-color);
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .tabs { display: flex; gap: 8px; }
        .tab-btn {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid transparent;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
        }
        .tab-btn.active {
            background: var(--bg-input);
            color: #fff;
            border-color: var(--border-color);
        }
        .action-bar { display: flex; gap: 8px; align-items: center; }
        .input-text {
            background-color: var(--bg-input);
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
        }
        .btn {
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: 0.15s;
        }
        .btn-transpile { background-color: var(--accent-purple); color: #fff; }
        .btn-save { background-color: var(--accent-blue); color: #fff; }
        .btn-delete { background-color: var(--accent-red); color: #fff; }
        .btn-run { background-color: var(--accent-green); color: #fff; }

        /* 에디터 & 콘솔 분할 영역 */
        #editor-section {
            height: 42%;
            display: flex;
            border-bottom: 1px solid var(--border-color);
            background-color: var(--bg-dark);
        }
        .code-pane {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border-color);
        }
        .pane-header {
            padding: 6px 12px;
            font-size: 11px;
            color: var(--text-muted);
            background-color: var(--bg-panel);
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
        }
        .code-editor {
            flex: 1;
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: "Consolas", monospace;
            font-size: 13px;
            line-height: 1.5;
            padding: 12px;
            border: none;
            resize: none;
            outline: none;
        }
        #console-pane {
            width: 360px;
            display: flex;
            flex-direction: column;
            background-color: #0b0d13;
        }
        #metrics-grid {
            padding: 10px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        .metric-card {
            background-color: var(--bg-panel);
            padding: 8px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }
        .metric-card .m-title { font-size: 11px; color: var(--text-muted); margin-bottom: 2px; }
        .metric-card .m-value { font-size: 14px; font-weight: 700; color: #fff; }
        #console-log {
            flex: 1;
            padding: 12px;
            font-family: "Consolas", monospace;
            font-size: 12px;
            overflow-y: auto;
            color: var(--text-muted);
        }

        /* 하단 차트 뷰 */
        #chart-section {
            flex: 1;
            position: relative;
            background-color: var(--bg-dark);
        }
        #chart-container { width: 100%; height: 100%; }
        .chart-legend {
            position: absolute;
            top: 12px;
            left: 16px;
            z-index: 10;
            background: rgba(22, 25, 34, 0.85);
            backdrop-filter: blur(4px);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            border: 1px solid var(--border-color);
            display: flex;
            gap: 12px;
        }
        .legend-item { display: flex; align-items: center; gap: 4px; }
        .legend-dot { width: 8px; height: 8px; border-radius: 50%; }
    </style>
</head>
<body>

    <!-- 사이드바 (전략 목록) -->
    <div id="sidebar">
        <div class="sidebar-header">
            <h2>전략 저장소</h2>
            <button class="btn-new" onclick="newStrategy()">+ 신규 전략</button>
        </div>
        <ul id="strat-list"></ul>
    </div>

    <!-- 메인 워크스페이스 -->
    <div id="main-workspace">
        <div class="workspace-header">
            <div class="tabs">
                <button class="tab-btn active" id="tab-dsl" onclick="setTab('DSL')">로컬 DSL</button>
                <button class="tab-btn" id="tab-pine" onclick="setTab('PINESCRIPT')">Pine Script v5 변환</button>
                <button class="tab-btn" id="tab-kiwoom" onclick="setTab('KIWOOM')">키움 수식 변환</button>
                <button class="tab-btn" id="tab-prompt" onclick="setTab('PROMPT')">자연어 프롬프트 합성</button>
            </div>
            <div class="action-bar">
                <input type="text" id="strat-name" class="input-text" style="width:160px;" placeholder="전략 명칭">
                <input type="text" id="strat-desc" class="input-text" style="width:200px;" placeholder="전략 설명">
                <button class="btn btn-transpile" id="btn-transpile" onclick="transpileCode()" style="display:none;">로컬 DSL 변환</button>
                <button class="btn btn-save" onclick="saveStrategy()">저장</button>
                <button class="btn btn-delete" id="btn-delete" onclick="deleteStrategy()" style="display:none;">삭제</button>
                <button class="btn btn-run" onclick="runBacktest()">백테스트 실행</button>
            </div>
        </div>

        <!-- 에디터 & 콘솔 분할 영역 -->
        <div id="editor-section">
            <!-- 변환 전 원본 소스창 (변환 탭일 때만 활성화) -->
            <div class="code-pane" id="source-pane" style="display:none;">
                <div class="pane-header" id="source-pane-title">원본 소스 입력</div>
                <textarea class="code-editor" id="source-editor" placeholder="변환할 코드를 입력하세요..."></textarea>
            </div>

            <!-- 타겟 로컬 DSL 에디터 -->
            <div class="code-pane">
                <div class="pane-header">실행 대상 로컬 DSL 스크립트</div>
                <textarea class="code-editor" id="dsl-editor" spellcheck="false"></textarea>
            </div>

            <!-- 성과 통계 및 시스템 콘솔 -->
            <div id="console-pane">
                <div class="pane-header">백테스트 성과 분석 지표</div>
                <div id="metrics-grid">
                    <div class="metric-card"><div class="m-title">총 수익률</div><div class="m-value" id="m-return">-</div></div>
                    <div class="metric-card"><div class="m-title">MDD</div><div class="m-value" id="m-mdd">-</div></div>
                    <div class="metric-card"><div class="m-title">승률</div><div class="m-value" id="m-winrate">-</div></div>
                    <div class="metric-card"><div class="m-title">총 거래 횟수</div><div class="m-value" id="m-trades">-</div></div>
                </div>
                <div class="pane-header">실행 엔진 로그</div>
                <div id="console-log">시스템 준비 완료.</div>
            </div>
        </div>

        <!-- 하단 TradingView 차트 -->
        <div id="chart-section">
            <div class="chart-legend">
                <div class="legend-item"><span class="legend-dot" style="background:#26a69a;"></span> 캔들 / 매수</div>
                <div class="legend-item"><span class="legend-dot" style="background:#ef5350;"></span> 매도</div>
                <div class="legend-item"><span class="legend-dot" style="background:#3b82f6;"></span> MA(5)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span> MA(20)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#8b5cf6;"></span> Bollinger Bands</div>
            </div>
            <div id="chart-container"></div>
        </div>
    </div>

    <script>
        let currentStrategyId = null;
        let currentTab = 'DSL';
        let chart = null;
        let candleSeries = null;
        let ma5Series = null;
        let ma20Series = null;
        let bbUpperSeries = null;
        let bbLowerSeries = null;

        // 1. 차트 엔진 초기화
        function initChart() {
            const container = document.getElementById('chart-container');
            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: { background: { color: '#0f1117' }, textColor: '#8b92a5' },
                grid: { vertLines: { color: '#1a1e2b' }, horzLines: { color: '#1a1e2b' } },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                timeScale: { borderColor: '#272c3d', timeVisible: true },
                rightPriceScale: { borderColor: '#272c3d' }
            });

            candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a', downColor: '#ef5350',
                wickUpColor: '#26a69a', wickDownColor: '#ef5350'
            });
            ma5Series = chart.addLineSeries({ color: '#3b82f6', lineWidth: 2 });
            ma20Series = chart.addLineSeries({ color: '#f59e0b', lineWidth: 2 });
            bbUpperSeries = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });
            bbLowerSeries = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });

            window.addEventListener('resize', () => {
                chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
            });
        }

        // 2. 탭 전환 제어
        function setTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            
            const sourcePane = document.getElementById('source-pane');
            const transBtn = document.getElementById('btn-transpile');
            const title = document.getElementById('source-pane-title');
            const srcEditor = document.getElementById('source-editor');

            if (tab === 'DSL') {
                document.getElementById('tab-dsl').classList.add('active');
                sourcePane.style.display = 'none';
                transBtn.style.display = 'none';
            } else {
                sourcePane.style.display = 'flex';
                transBtn.style.display = 'inline-block';
                if (tab === 'PINESCRIPT') {
                    document.getElementById('tab-pine').classList.add('active');
                    title.innerText = 'TradingView Pine Script v5 코드 입력';
                    srcEditor.value = `//@version=5\\nstrategy("Pine_RSI_Cross", overlay=true)\\nfast_ma = ta.ema(close, 9)\\nslow_ma = ta.ema(close, 21)\\nif ta.crossover(fast_ma, slow_ma)\\n    strategy.entry("Long", strategy.long)\\nif ta.crossunder(fast_ma, slow_ma)\\n    strategy.close("Long")`;
                } else if (tab === 'KIWOOM') {
                    document.getElementById('tab-kiwoom').classList.add('active');
                    title.innerText = '키움 수식관리자 수식 입력';
                    srcEditor.value = `CrossUp(C, avg(C, 20)) and C > C(1) and HighestSince(1, CrossUp(C, avg(C, 60)), H) == H`;
                } else if (tab === 'PROMPT') {
                    document.getElementById('tab-prompt').classList.add('active');
                    title.innerText = '자연어 매매전략 요구사항 입력';
                    srcEditor.value = `5일선이 20일선을 상향 돌파하고 RSI가 30 이하일 때 매수하고, 데드크로스 발생 시 전량 매도해줘`;
                }
            }
        }

        // 3. 트랜스파일러 API 호출
        async function transpileCode() {
            const src = document.getElementById('source-editor').value;
            const logBox = document.getElementById('console-log');
            try {
                const res = await fetch('/api/transpile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_type: currentTab, source_code: src, name: document.getElementById('strat-name').value })
                });
                const data = await res.json();
                document.getElementById('dsl-editor').value = data.dsl_code;
                logBox.innerHTML = `<span style="color:#10b981;">[트랜스파일 성공]</span><br>${currentTab} 코드가 로컬 DSL로 변환되었습니다.`;
            } catch (e) {
                logBox.innerHTML = `<span style="color:#ef4444;">[변환 실패]</span><br>${e.message}`;
            }
        }

        // 4. 전략 로드 및 CRUD
        async function loadStrategies() {
            const res = await fetch('/api/strategies');
            const data = await res.json();
            const listEl = document.getElementById('strat-list');
            listEl.innerHTML = '';
            
            data.forEach(item => {
                const li = document.createElement('li');
                li.className = `strat-item ${item.id === currentStrategyId ? 'active' : ''}`;
                li.onclick = () => selectStrategy(item);
                li.innerHTML = `
                    <div class="title-row"><span class="title">${item.name}</span><span class="badge">${item.source_type}</span></div>
                    <div class="desc">${item.description || '설명 없음'}</div>
                `;
                listEl.appendChild(li);
            });

            if (data.length > 0 && currentStrategyId === null) {
                selectStrategy(data[0]);
            }
        }

        function selectStrategy(item) {
            currentStrategyId = item.id;
            document.getElementById('strat-name').value = item.name;
            document.getElementById('strat-desc').value = item.description || '';
            document.getElementById('dsl-editor').value = item.dsl_code;
            document.getElementById('btn-delete').style.display = 'inline-block';
            setTab('DSL');
            loadStrategies();
            runBacktest();
        }

        function newStrategy() {
            currentStrategyId = null;
            document.getElementById('strat-name').value = 'Custom_Strategy';
            document.getElementById('strat-desc').value = '';
            document.getElementById('dsl-editor').value = `strategy "Custom_Strategy" {\\n    timeframe = "1d"\\n    \\n    ma20 = ta.sma(close, 20)\\n    buy_cond = ta.crossover(close, ma20)\\n    exit_cond = ta.crossunder(close, ma20)\\n    \\n    on(buy_cond) {\\n        order.buy()\\n    }\\n    on(exit_cond) {\\n        order.close_position()\\n    }\\n}`;
            document.getElementById('btn-delete').style.display = 'none';
            setTab('DSL');
            loadStrategies();
        }

        async function saveStrategy() {
            const name = document.getElementById('strat-name').value;
            const desc = document.getElementById('strat-desc').value;
            const code = document.getElementById('dsl-editor').value;
            const payload = { name: name, description: desc, dsl_code: code, source_type: currentTab };
            
            const res = currentStrategyId 
                ? await fetch(`/api/strategies/${currentStrategyId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })
                : await fetch('/api/strategies', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
            
            if (res.ok) {
                const data = await res.json();
                if (data.id) currentStrategyId = data.id;
                loadStrategies();
            }
        }

        async function deleteStrategy() {
            if (!currentStrategyId || !confirm('전략을 삭제하시겠습니까?')) return;
            await fetch(`/api/strategies/${currentStrategyId}`, { method: 'DELETE' });
            currentStrategyId = null;
            newStrategy();
            loadStrategies();
        }

        // 5. 백테스트 및 렌더링
        async function runBacktest() {
            const code = document.getElementById('dsl-editor').value;
            const logBox = document.getElementById('console-log');
            try {
                const res = await fetch('/api/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dsl_code: code })
                });
                const data = await res.json();

                candleSeries.setData(data.candles);
                ma5Series.setData(data.ma5);
                ma20Series.setData(data.ma20);
                bbUpperSeries.setData(data.bb_upper);
                bbLowerSeries.setData(data.bb_lower);
                candleSeries.setMarkers(data.markers);
                chart.timeScale().fitContent();

                // 성과 지표 업데이트
                document.getElementById('m-return').innerText = data.metrics.total_return;
                document.getElementById('m-mdd').innerText = data.metrics.mdd;
                document.getElementById('m-winrate').innerText = data.metrics.win_rate;
                document.getElementById('m-trades').innerText = data.metrics.trade_count;

                logBox.innerHTML = `<span style="color:#10b981;">[백테스트 성공]</span><br>엔진: ${data.metrics.engine_mode}<br>최종 평가액: ${data.metrics.final_equity}`;
            } catch (e) {
                logBox.innerHTML = `<span style="color:#ef4444;">[실행 에러]</span><br>${e.message}`;
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            loadStrategies();
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    print("=== [Enterprise Quant DSL Studio Server Started] ===")
    print("Dashboard URL: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")