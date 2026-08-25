"""Canonical, machine-readable capabilities exposed to prompt generation."""
from core.function_registry import FUNCTION_SPECS, manifest_lines

DSL_VERSION = "1.4.0"
TA_FUNCTIONS = {spec.name: spec.signature for spec in FUNCTION_SPECS.values() if spec.category == "ta"}
MATH_FUNCTIONS = [spec.name for spec in FUNCTION_SPECS.values() if spec.category in {"math", "logic"}]
STATE_FUNCTIONS = {spec.name: spec.signature for spec in FUNCTION_SPECS.values() if spec.category == "state"}
MTF_FUNCTIONS = {spec.name: spec.signature for spec in FUNCTION_SPECS.values() if spec.category == "mtf"}
SESSION_FUNCTIONS = {spec.name: spec.signature for spec in FUNCTION_SPECS.values() if spec.category == "session"}
ARTIFACT_TYPES = {"indicator":"지표","signal":"신호","strength":"강세·약세","strategy":"전략","drawing":"사용자형식"}


def capability_markdown():
    functions = "\n".join(f"- `{value}`" for value in manifest_lines("ta"))
    math = "\n".join(f"- `{value}`" for category in ("math", "logic") for value in manifest_lines(category))
    states = "\n".join(f"- `{value}`" for value in manifest_lines("state"))
    mtf = "\n".join(f"- `{value}`" for value in manifest_lines("mtf"))
    session = "\n".join(f"- `{value}`" for value in manifest_lines("session"))
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
### 세션 함수
{session}
### 멀티 타임프레임 (lookahead 금지, 완료된 상위 봉만 반환)
{mtf}
"""
