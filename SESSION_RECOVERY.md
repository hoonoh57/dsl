# DSL Session Recovery Protocol

Status: **AUTHORITATIVE RECOVERY ENTRYPOINT / ACTIVE / 2026-08-28 KST**

## Trigger

When the user sends exactly `세션복구` (or starts a message with `세션복구`) in any new chat inside the `dsl` project, treat it as a command, not as a request for clarification.

The assistant must recover the project immediately without asking the user to restate history.

## Recovery sources and precedence

Use the strongest available sources in this order:

1. Current ChatGPT Project context and previous project conversations, when available, to recover intent, design decisions, user preferences and unfinished reasoning.
2. This file, `SESSION_RECOVERY.md`, as the permanent recovery protocol.
3. `CURRENT_STATE.md` from repository `hoonoh57/dsl` branch `main` for the current executable position, trusted checkpoints and immediate next boundary.
4. The authority documents listed by `CURRENT_STATE.md` when implementation is about to resume.
5. Recent checkpoint documents for details that are not needed in the first recovery reply.

If an old conversation conflicts with current repository state, the current repository wins for implementation status and exact tested checkpoints. Previous conversations remain useful for product intent and rationale.

If previous-project-conversation access is unavailable for any reason, do not fail recovery. Recover from this file plus `CURRENT_STATE.md` and say nothing about missing history unless the missing information materially blocks development.

## First recovery reply — fixed human format

The first reply to `세션복구` must be concise Korean and contain only these three sections at normal human abstraction level:

### 1. 개발철학

Explain the project philosophy in **five items or fewer**. Default compression:

- **작고 검증된 전술부터 키운다.** 한 번에 거대한 자동매매 시스템을 만들지 않고, 작은 전술을 반복 검증·진화시킨다.
- **DSL 핵심은 단순하고 믿을 수 있게 유지한다.** 계산·신호·주문 같은 범용 기능만 DSL에 두고, 시장/섹터/대장주·추종주 판단은 외부 분석 계층에 둔다.
- **미래정보와 숨은 점수를 금지한다.** 당시 알 수 있었던 정보만 사용하고, 여러 판단 기준을 불투명한 하나의 점수로 감추지 않는다.
- **상위 정보는 기회를 만들기보다 검증·제한한다.** 시장·섹터·그룹 정보는 약한 전술을 억지로 살리지 않고, 이미 존재하는 전술의 진입을 더 안전하게 고르는 데 사용한다.
- **최소 기능으로 먼저 실제 가동하고 성공 후 확장한다.** 1차 vertical slice를 작게 완성한 뒤 대장/추종 패턴, 예약주문, 취소, 다중종목 운영을 단계적으로 넓힌다.

### 2. 최근 한 일

List at most five recent milestones in plain language. Use `CURRENT_STATE.md` to refresh this list. Mention exact SHA only when it is needed to distinguish a trusted executable checkpoint.

Current anchor as of 2026-08-28:

- `CTXINT3` completed: next-bar-open entry uses only information confirmed on the prior completed bar.
- `LF1` completed at exact trusted checkpoint `5ec230c8bbada60f0e4b9fe945a5380d7c405fe2`: 7 focused tests passed and Tactical P1 Full passed.
- `LF1` provides first minimal leader/follower relationship evidence: qualified leader, follow rate, lag and response strength remain separate observations.
- Leader/follower judgement remains outside Instrument DSL and has no direct order authority.

### 3. 앞으로 할 일

List at most five immediate steps in plain language. Refresh from `CURRENT_STATE.md` before answering.

Current next boundary as of 2026-08-28:

- Add a **generic pending-order cancellation capability** to the DSL using explicit order/client identity.
- Verify deterministic Backtest/Broker cancellation behavior independently from leader/follower logic.
- Only after cancellation is trusted, compose a story such as: leader rebound -> follower setup -> pending order -> leader/sector reversal -> cancel.
- Keep the first operating slice minimal; expand follower-pattern sophistication, adaptive lag and multi-follower competition only after the minimal flow succeeds.

## Response style for recovery

- Speak to a human product owner, not to a compiler engineer.
- Do not dump class names, schemas, hashes, test filenames or machine-level implementation details unless they are necessary to explain current status.
- Do not repeat long logs.
- Do not ask `무엇을 하던 중이었나요?` or request a manual recap.
- Keep the first recovery answer short enough to scan in under a minute.
- After the recovery summary, resume autonomous plan -> modify -> test workflow from the immediate next boundary unless the user gives a different instruction.

## Before resuming implementation

After the first recovery reply and before making code changes, re-read the current `CURRENT_STATE.md` authority order and the specific authority/checkpoint files relevant to the next tranche. Do not infer permission to bypass Core DSL freeze, causality, validation or execution boundaries from old conversation context.

## Maintenance rule

Whenever a trusted milestone changes the immediate project position, update both:

- `CURRENT_STATE.md`
- this file's `Current anchor` / `Current next boundary`

This keeps `세션복구` useful even if project-conversation retrieval is partial or unavailable.
