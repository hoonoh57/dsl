"""Static semantic and series-type analysis for Quant DSL."""
from __future__ import annotations
import ast
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from core.dsl_parser import IfNode, SetNode, StrategyNode

class ValueType(str, Enum):
    SCALAR_NUMBER="scalar<number>"; SCALAR_BOOL="scalar<bool>"; STRING="string"
    SERIES_NUMBER="series<number>"; SERIES_BOOL="series<bool>"

class DSLSemanticError(ValueError):
    def __init__(self,message,line=1,column=1,code="SEMANTIC_ERROR"):
        self.line,self.column,self.code=line,column,code
        super().__init__(f"line {line}, column {column}: {message}")

@dataclass(frozen=True)
class FunctionSpec:
    minimum:int; maximum:int; returns:ValueType

FUNCTIONS={
 **{name:FunctionSpec(1,1,ValueType.SERIES_NUMBER) for name in ("mtf.open","mtf.high","mtf.low","mtf.close","mtf.volume")},
 "mtf.sma":FunctionSpec(2,2,ValueType.SERIES_NUMBER),
 **{name:FunctionSpec(2,3,ValueType.SERIES_NUMBER) for name in ("ta.sma","ta.ema","ta.wma","ta.rma","ta.highest","ta.lowest","ta.stdev")},
 "ta.ma":FunctionSpec(2,4,ValueType.SERIES_NUMBER), "ta.rsi":FunctionSpec(1,2,ValueType.SERIES_NUMBER),
 "ta.crossover":FunctionSpec(2,2,ValueType.SERIES_BOOL), "ta.crossunder":FunctionSpec(2,2,ValueType.SERIES_BOOL),
 "ta.sum":FunctionSpec(1,3,ValueType.SERIES_NUMBER), "ta.roc":FunctionSpec(2,2,ValueType.SERIES_NUMBER),
 "ta.jma":FunctionSpec(3,4,ValueType.SERIES_NUMBER), "ta.supertrend":FunctionSpec(0,2,ValueType.SERIES_NUMBER),
 "ta.supertrend_direction":FunctionSpec(0,2,ValueType.SERIES_NUMBER), "ta.macd":FunctionSpec(1,5,ValueType.SERIES_NUMBER),
 **{name:FunctionSpec(0,1,ValueType.SERIES_NUMBER) for name in ("ta.atr","ta.adx","ta.trix","ta.cci")},
 **{name:FunctionSpec(1,1,ValueType.SERIES_NUMBER) for name in ("ta.nrange","ta.williams_r","ta.abs_range","ta.sum_abs_r","ta.vhf","ta.bars_since")},
 "ta.shift":FunctionSpec(2,2,ValueType.SERIES_NUMBER), "ta.count_since":FunctionSpec(2,2,ValueType.SERIES_NUMBER),
 "ta.highest_since":FunctionSpec(2,2,ValueType.SERIES_NUMBER), "ta.lowest_since":FunctionSpec(2,2,ValueType.SERIES_NUMBER),
 "ta.value_when":FunctionSpec(3,3,ValueType.SERIES_NUMBER), "logic.ifelse":FunctionSpec(3,3,ValueType.SERIES_NUMBER),
 **{name:FunctionSpec(1,1,ValueType.SERIES_NUMBER) for name in ("math.log","math.log10","math.abs","math.sqrt","math.sin","math.cos","math.tan","math.asin","math.acos","math.atan")},
 **{name:FunctionSpec(2,2,ValueType.SERIES_NUMBER) for name in ("math.pow","math.max","math.min")},
 **{name:FunctionSpec(0,0,ValueType.SERIES_NUMBER) for name in ("session.day_open","session.day_high","session.day_low","session.prev_open","session.prev_high","session.prev_low","session.prev_close")},
 "state.edge":FunctionSpec(1,1,ValueType.SERIES_BOOL), "state.falling_edge":FunctionSpec(1,1,ValueType.SERIES_BOOL),
 "state.ready_after":FunctionSpec(2,2,ValueType.SERIES_BOOL), "state.hold":FunctionSpec(2,2,ValueType.SERIES_BOOL),
 "state.persist":FunctionSpec(2,2,ValueType.SERIES_BOOL), "state.latch":FunctionSpec(2,3,ValueType.SERIES_BOOL),
 "state.count":FunctionSpec(2,2,ValueType.SERIES_NUMBER), "state.regime":FunctionSpec(2,3,ValueType.SERIES_NUMBER),
}

def _series(value): return value in {ValueType.SERIES_NUMBER,ValueType.SERIES_BOOL}
def _boolean(value): return value in {ValueType.SCALAR_BOOL,ValueType.SERIES_BOOL}
def _number(value): return value in {ValueType.SCALAR_NUMBER,ValueType.SERIES_NUMBER}

class ExpressionTypeChecker(ast.NodeVisitor):
    def __init__(self,symbols:Dict[str,ValueType],line:int): self.symbols,self.line=symbols,line
    def check(self,text):
        text=re.sub(r"\btrue\b","True",text,flags=re.I);text=re.sub(r"\bfalse\b","False",text,flags=re.I)
        return self.visit(ast.parse(text,mode="eval").body)
    def visit_Name(self,node):
        if node.id in self.symbols:return self.symbols[node.id]
        if node.id in {"True","False"}:return ValueType.SCALAR_BOOL
        raise DSLSemanticError(f"정의되지 않은 변수: {node.id}",self.line,node.col_offset+1,"UNDEFINED_SYMBOL")
    def visit_Constant(self,node):
        if isinstance(node.value,bool):return ValueType.SCALAR_BOOL
        if isinstance(node.value,(int,float)):return ValueType.SCALAR_NUMBER
        if isinstance(node.value,str):return ValueType.STRING
        raise DSLSemanticError("지원하지 않는 상수 형식",self.line,node.col_offset+1,"BAD_CONSTANT")
    def visit_Attribute(self,node):
        if isinstance(node.value,ast.Name):return f"{node.value.id}.{node.attr}"
        raise DSLSemanticError("지원하지 않는 속성 접근",self.line,node.col_offset+1,"BAD_ATTRIBUTE")
    def visit_Call(self,node):
        name=self.visit(node.func)
        if name not in FUNCTIONS:raise DSLSemanticError(f"지원하지 않는 함수: {name}",self.line,node.col_offset+1,"UNSUPPORTED_FUNCTION")
        spec=FUNCTIONS[name];count=len(node.args)+len(node.keywords)
        if not spec.minimum<=count<=spec.maximum:raise DSLSemanticError(f"{name} 인수 개수 오류: {count}개 (허용 {spec.minimum}~{spec.maximum})",self.line,node.col_offset+1,"BAD_ARITY")
        args=[self.visit(item) for item in node.args]+[self.visit(item.value) for item in node.keywords]
        if name in {"ta.crossover","ta.crossunder"} and not all(_number(value) for value in args):
            raise DSLSemanticError(f"{name}에는 숫자형 인수가 필요합니다.",self.line,node.col_offset+1,"BAD_ARGUMENT_TYPE")
        if name=="logic.ifelse" and not _boolean(args[0]):
            raise DSLSemanticError("logic.ifelse 첫 인수는 boolean이어야 합니다.",self.line,node.col_offset+1,"BAD_ARGUMENT_TYPE")
        if name.startswith("state."):
            boolean_count=1 if name in {"state.edge","state.falling_edge","state.ready_after","state.hold","state.persist"} else 2
            if not all(_boolean(value) for value in args[:boolean_count]):
                raise DSLSemanticError(f"{name}의 조건 인수는 boolean이어야 합니다.",self.line,node.col_offset+1,"BAD_ARGUMENT_TYPE")
        if name.startswith("math.") and args and not any(_series(value) for value in args):
            return ValueType.SCALAR_NUMBER
        if name=="logic.ifelse":
            return ValueType.SERIES_NUMBER if any(_series(value) for value in args) else args[1]
        return spec.returns
    def visit_Subscript(self,node):
        value=self.visit(node.value)
        if not _series(value):raise DSLSemanticError("과거 참조는 series에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_HISTORY_TARGET")
        return value
    def visit_UnaryOp(self,node):
        value=self.visit(node.operand)
        if isinstance(node.op,ast.Not):
            if not _boolean(value):raise DSLSemanticError("not은 boolean에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_UNARY_TYPE")
            return value
        if not _number(value):raise DSLSemanticError("부호 연산은 숫자형에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_UNARY_TYPE")
        return value
    def visit_BinOp(self,node):
        left,right=self.visit(node.left),self.visit(node.right)
        if not _number(left) or not _number(right):raise DSLSemanticError("산술 연산은 숫자형에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_BINARY_TYPE")
        return ValueType.SERIES_NUMBER if _series(left) or _series(right) else ValueType.SCALAR_NUMBER
    def visit_BoolOp(self,node):
        values=[self.visit(value) for value in node.values]
        if not all(_boolean(value) for value in values):raise DSLSemanticError("and/or는 boolean에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_BOOLEAN_TYPE")
        return ValueType.SERIES_BOOL if any(_series(value) for value in values) else ValueType.SCALAR_BOOL
    def visit_Compare(self,node):
        values=[self.visit(node.left)]+[self.visit(value) for value in node.comparators]
        if not all(_number(value) for value in values):raise DSLSemanticError("비교 연산은 숫자형에만 사용할 수 있습니다.",self.line,node.col_offset+1,"BAD_COMPARE_TYPE")
        return ValueType.SERIES_BOOL if any(_series(value) for value in values) else ValueType.SCALAR_BOOL
    def generic_visit(self,node):raise DSLSemanticError(f"허용되지 않는 표현식: {type(node).__name__}",self.line,getattr(node,"col_offset",0)+1,"BAD_EXPRESSION_NODE")

class DSLSemanticAnalyzer:
    MARKET={name:ValueType.SERIES_NUMBER for name in ("open","high","low","close","volume","amount","open_interest","date","time")}
    @classmethod
    def analyze(cls,document:StrategyNode):
        symbols=dict(cls.MARKET)
        for item in document.assignments:
            value=ExpressionTypeChecker(symbols,item.line).check(item.expression)
            if item.is_input and value not in {ValueType.SCALAR_NUMBER,ValueType.SCALAR_BOOL,ValueType.STRING}:
                raise DSLSemanticError(f"input은 scalar만 허용합니다: {item.name}",item.line,code="SERIES_INPUT")
            symbols[item.name]=value
        state_names=set()
        for item in document.states:
            value=ExpressionTypeChecker(symbols,item.line).check(item.expression)
            if value not in {ValueType.SCALAR_NUMBER,ValueType.SCALAR_BOOL}:
                raise DSLSemanticError(f"state 초기값은 scalar 숫자/boolean만 허용합니다: {item.name}",item.line,code="BAD_STATE_INITIALIZER")
            symbols[item.name]=value;state_names.add(item.name)
        event_symbols=dict(symbols)
        def analyze_bar(items):
            for item in items:
                if isinstance(item,IfNode):
                    condition=ExpressionTypeChecker(symbols,item.line).check(item.condition)
                    if not _boolean(condition):raise DSLSemanticError("if 조건은 boolean이어야 합니다.",item.line,code="BAD_IF_TYPE")
                    analyze_bar(item.body);analyze_bar(item.otherwise)
                elif isinstance(item,SetNode):
                    value=ExpressionTypeChecker(symbols,item.line).check(item.expression)
                    scalar_value=ValueType.SCALAR_BOOL if value in {ValueType.SCALAR_BOOL,ValueType.SERIES_BOOL} else ValueType.SCALAR_NUMBER
                    if item.name in state_names:
                        current=symbols[item.name]
                        if _boolean(current)!=_boolean(scalar_value):raise DSLSemanticError(f"state 형식을 변경할 수 없습니다: {item.name}",item.line,code="STATE_TYPE_CHANGE")
                    symbols[item.name]=scalar_value
                    event_symbols[item.name]=ValueType.SERIES_BOOL if _boolean(scalar_value) else ValueType.SERIES_NUMBER
        analyze_bar(document.on_bar)
        for event in document.events:
            value=ExpressionTypeChecker(event_symbols,event.line).check(event.condition)
            if not _boolean(value):raise DSLSemanticError("on 조건은 boolean이어야 합니다.",event.line,code="BAD_EVENT_TYPE")
        return event_symbols
