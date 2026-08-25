"""Prompt compiler backed by the single official DSL Playbook."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Optional
from core.capabilities import ARTIFACT_TYPES, DSL_VERSION, capability_markdown

PLAYBOOK_PATH=Path(__file__).resolve().parent.parent/"QUANT_DSL_PLAYBOOK.md"
def playbook_text(): return PLAYBOOK_PATH.read_text(encoding="utf-8")
def playbook_hash(): return hashlib.sha256(playbook_text().encode("utf-8")).hexdigest()

def generate_full_llm_prompt(user_requirement: str, *, artifact_type: str="strategy",
                             current_dsl: str="", source_type: str="NATURAL_LANGUAGE",
                             source_code: str="", validation_error: Optional[str]=None) -> str:
    kind=ARTIFACT_TYPES.get(artifact_type, ARTIFACT_TYPES["strategy"])
    return f"""당신은 Quant DSL 변환기입니다. 공식 Playbook과 Capability Manifest만을 근거로 전체 DSL을 작성하세요.

[작업 계약]
- 결과물 종류: {kind} ({artifact_type})
- 입력 소스 형식: {source_type}
- 사용자 요청: {user_requirement}
- DSL 버전: {DSL_VERSION}
- Playbook SHA-256: {playbook_hash()}

[현재 검증된 DSL]
```dsl
{current_dsl.strip() or '(신규 결과물이므로 없음)'}
```
[변환할 원본 소스]
```text
{source_code.strip() or '(별도 원본 소스 없음)'}
```
[이전 검증 오류]
[검증 피드백]
(실패 시 문법·실행 오류, 성공 시 전략 비종속 성과 증거)
{validation_error.strip() if validation_error else '(첫 요청이므로 없음)'}

[공식 별첨 시작]
{playbook_text()}
{capability_markdown()}
[공식 별첨 끝]

[반환 규칙]
1. 사용자의 의도를 만족하는 전체 DSL을 반환하세요.
2. 부분 패치나 생략 기호를 사용하지 마세요.
3. DSL은 반드시 하나의 ```dsl 코드 블록에 넣으세요.
4. 성과 증거가 첨부되면 전략 유형을 미리 가정하지 말고 사용자 요청과 현재 DSL에서 의도와 신호 단계를 먼저 복원하세요.
5. 증거와 현재 DSL로 설명 가능한 병목 가설을 하나만 선택하고, 그 가설을 검증할 수 있는 최소 변경을 하세요.
6. 특정 지표·시장국면·전략 이름에 특화된 처방을 범용 규칙처럼 적용하지 마세요.
7. 동일 표본의 수익률에 맞춘 기간·임계값 탐색을 피하고, 구조·상태 전이·체결 의미·미래참조 여부를 우선 점검하세요.
8. 신호 수, 거래 수, 총수익률, MDD 중 하나를 개선하기 위해 다른 항목을 무시하지 마세요.
9. 표본이 부족하면 성과를 확정적으로 주장하지 말고, 다음 검증에서 원인 구분이 가능하도록 의미 있는 중간 조건을 보존하거나 추가하세요.
10. signal_counts는 각 조건의 독립적인 true 봉 수입니다. 두 변수의 횟수 차이만으로 순차 전환율이나 체결 누락을 단정하지 마세요.
11. evaluation_context의 종목·주기·봉 수·체결 방식·비용 설정을 변경하지 말고 동일 조건 비교가 가능한 DSL을 반환하세요.
"""
