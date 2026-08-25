"""Kiwoom/Pine source transpilers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


class TranspileError(ValueError):
    pass


@dataclass
class KiwoomStrategy:
    name: str = "Kiwoom_Strategy"
    timeframe: str = "1d"
    long_entry: str = ""
    long_exit: str = ""
    short_entry: str = ""
    short_exit: str = ""
    variables: Dict[str, float] = field(default_factory=dict)


SECTION_NAMES = {
    "매수진입": "long_entry", "매수": "long_entry", "LONG_ENTRY": "long_entry",
    "매수청산": "long_exit", "LONG_EXIT": "long_exit",
    "매도진입": "short_entry", "공매도진입": "short_entry", "SHORT_ENTRY": "short_entry",
    "매도청산": "short_exit", "SHORT_EXIT": "short_exit",
    "변수": "variables", "VARIABLES": "variables",
}
FUNCTION_MAP = {
    "avg": "ta.sma", "평균": "ta.sma", "wavg": "ta.wma", "가중평균": "ta.wma",
    "ma": "ta.ma", "eavg": "ta.ema", "지수평균": "ta.ema",
    "crossup": "ta.crossover", "crossdown": "ta.crossunder",
    "상향돌파": "ta.crossover", "하향돌파": "ta.crossunder",
    "highest": "ta.highest", "최고값": "ta.highest", "lowest": "ta.lowest", "최저값": "ta.lowest",
    "sum": "ta.sum", "합계": "ta.sum", "stdev": "ta.stdev", "표준편차": "ta.stdev",
    "rsi": "ta.rsi", "roc": "ta.roc", "atr": "ta.atr", "adx": "ta.adx", "trix": "ta.trix",
    "cci": "ta.cci", "jma": "ta.jma", "macd": "ta.macd",
    "nrange": "ta.nrange", "williamsr": "ta.williams_r", "absrange": "ta.abs_range",
    "sumabsr": "ta.sum_abs_r", "vhf": "ta.vhf",
    "if": "logic.ifelse", "만일": "logic.ifelse", "shift": "ta.shift",
    "countsince": "ta.count_since", "barssince": "ta.bars_since",
    "highestsince": "ta.highest_since", "lowestsince": "ta.lowest_since", "valuewhen": "ta.value_when",
    "dayopen": "session.day_open", "dayhigh": "session.day_high", "daylow": "session.day_low",
    "predayopen": "session.prev_open", "predayhigh": "session.prev_high",
    "predaylow": "session.prev_low", "predayclose": "session.prev_close",
    "pow": "math.pow", "log10": "math.log10", "log": "math.log", "abs": "math.abs",
    "sqrt": "math.sqrt", "asin": "math.asin", "acos": "math.acos", "atan": "math.atan",
    "sin": "math.sin", "cos": "math.cos", "tan": "math.tan", "max": "math.max", "min": "math.min",
}


def _strip_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def _split_statements(source: str) -> List[str]:
    statements, buf, depth = [], [], 0
    for char in _strip_comments(source):
        if char == "(": depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0: raise TranspileError("닫는 괄호가 너무 많습니다.")
        if char in ";\n" and depth == 0:
            value = "".join(buf).strip()
            if value: statements.append(value)
            buf = []
        else:
            buf.append(char)
    if depth: raise TranspileError("괄호가 닫히지 않았습니다.")
    value = "".join(buf).strip()
    if value: statements.append(value)
    return statements


def _translate_expression(expr: str) -> str:
    data_names = {"거래대금":"amount", "ACCOUNT":"amount", "거래량":"volume", "VOLUME":"volume",
                  "시가":"open", "OPEN":"open", "고가":"high", "HIGH":"high", "저가":"low", "LOW":"low",
                  "종가":"close", "CLOSE":"close", "미결제약정":"open_interest", "OI":"open_interest",
                  "일자":"date", "DATE":"date", "시간":"time", "TIME":"time",
                  "C":"close", "O":"open", "H":"high", "L":"low", "V":"volume"}
    for source, target in data_names.items():
        expr = re.sub(rf"(?i)\b{source}\s*\(\s*(\d+)\s*\)", rf"{target}[\1]", expr)
        expr = re.sub(rf"(?i)\b{source}\b", target, expr)
    for source, target in sorted(FUNCTION_MAP.items(), key=lambda item: -len(item[0])):
        expr = re.sub(rf"(?i)\b{re.escape(source)}\s*(?=\()", target, expr)
    expr = re.sub(r"(?i)\bAND\b|&&", " and ", expr)
    expr = re.sub(r"(?i)\bOR\b|\|\|", " or ", expr)
    expr = re.sub(r"(?i)\bNOT\b|!(?!=)", " not ", expr)
    expr = expr.replace("％", "%").replace("^", "**")
    expr = re.sub(r"(?i)\b(단순|SIMPLE)\b", '"simple"', expr)
    expr = re.sub(r"(?i)\b(지수|EXPONENTIAL)\b", '"exponential"', expr)
    expr = re.sub(r"(?i)\b(가중|WEIGHTED)\b", '"weighted"', expr)
    expr = re.sub(r"(?<![<>=!])=(?!=)", "==", expr)
    return re.sub(r"\s+", " ", expr).strip()


def _translate_formula(source: str, prefix: str) -> tuple[List[str], str]:
    assignments: List[str] = []
    local_names: List[str] = []
    result = "false"
    for statement in _split_statements(source):
        assignment = re.match(r"^([A-Za-z_가-힣][\w가-힣]*)\s*(?::=|=)\s*(.+)$", statement)
        if assignment and assignment.group(1).upper() not in {"C", "O", "H", "L", "V"}:
            name, expression = assignment.groups()
            translated = _translate_expression(expression)
            for local in local_names:
                translated = re.sub(rf"\b{re.escape(local)}\b", f"{prefix}_{local}", translated)
            assignments.append(f"{prefix}_{name} = {translated}")
            local_names.append(name)
            result = f"{prefix}_{name}"
        else:
            result = _translate_expression(statement)
            for local in local_names:
                result = re.sub(rf"\b{re.escape(local)}\b", f"{prefix}_{local}", result)
    return assignments, result


def parse_kiwoom_sections(code: str, name: str = "Kiwoom_Strategy") -> KiwoomStrategy:
    strategy = KiwoomStrategy(name=name or "Kiwoom_Strategy")
    matches = list(re.finditer(r"(?im)^\s*\[([^\]]+)\]\s*$", code))
    if not matches:
        strategy.long_entry = code
        return strategy
    for index, match in enumerate(matches):
        label = match.group(1).strip()
        key = SECTION_NAMES.get(label.upper()) or SECTION_NAMES.get(label)
        if not key: continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(code)
        value = code[match.end():end].strip()
        if key == "variables":
            for statement in _split_statements(value):
                item = re.match(r"^([\w가-힣]+)\s*=\s*(-?\d+(?:\.\d+)?)$", statement)
                if item: strategy.variables[item.group(1)] = float(item.group(2))
        else:
            setattr(strategy, key, value)
    return strategy


class CodeTranspiler:
    @staticmethod
    def from_kiwoom(code: str, name: str = "Kiwoom_Strategy") -> str:
        return CodeTranspiler.from_kiwoom_strategy(parse_kiwoom_sections(code, name))

    @staticmethod
    def from_kiwoom_strategy(strategy: KiwoomStrategy) -> str:
        declarations, conditions = [], {}
        for key in ("long_entry", "long_exit", "short_entry", "short_exit"):
            source = getattr(strategy, key)
            if source:
                lines, result = _translate_formula(source, key)
                declarations.extend(lines)
                conditions[key] = result
            else:
                conditions[key] = "false"
        body = [f"input {key} = {value:g}" for key, value in strategy.variables.items()]
        body += declarations + [f"{key} = {value}" for key, value in conditions.items()]
        body_text = "\n    ".join(body)
        return f'''strategy "{strategy.name}" {{
    timeframe = "{strategy.timeframe}"

    // Converted from Kiwoom Formula Manager
    {body_text}

    on(long_entry) {{ order.buy(type = "MARKET") }}
    on(long_exit) {{ order.close_long() }}
    on(short_entry) {{ order.sell_short(type = "MARKET") }}
    on(short_exit) {{ order.close_short() }}
}}'''

    @staticmethod
    def from_pinescript(code: str) -> str:
        lines, strat_name = [], "Pine_Converted"
        for raw_line in code.splitlines():
            raw = raw_line.strip()
            if not raw or raw.startswith("//"): continue
            if raw.startswith("strategy("):
                match = re.search(r'''strategy\s*\(\s*["']([^"']+)["']''', raw)
                if match: strat_name = match.group(1).replace(" ", "_")
            elif not raw.startswith("plot"):
                lines.append(raw.replace(":=", "="))
        body = "\n    ".join(lines)
        return f'''strategy "{strat_name}" {{
    timeframe = "1d"
    // Converted from TradingView Pine Script v5
    {body}
}}'''
