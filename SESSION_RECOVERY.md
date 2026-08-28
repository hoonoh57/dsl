# DSL Session Recovery Protocol

Status: **AUTHORITATIVE CRASH-SAFE RECOVERY ENTRYPOINT / ACTIVE / 2026-08-28 KST**

## Trigger

When the user sends exactly `세션복구` (or starts a message with `세션복구`) in any new chat inside the `dsl` project, treat it as a recovery command, not as a request for clarification.

The assistant must recover the project immediately without asking the user to restate history.

The protocol is specifically designed for the common failure mode where the previous conversation is terminated by context limits **before the assistant had a chance to update any checkpoint document**.

Therefore recovery must never assume that `CURRENT_STATE.md`, this file, or another checkpoint was updated immediately before the prior session ended.

## Core rule — reconstruct, do not merely read a checkpoint

`세션복구` means:

```text
previous project conversation evidence
 + latest GitHub repository reality
 + last local evidence reported in conversation
 + checkpoint/authority documents
 -> reconstruct the most likely current project position
```

A checkpoint document may be stale by one or more commits/tranches. That is expected and must not cause recovery to fall back to the stale state.

## Recovery evidence sources

Use all available sources, not only the documents.

### 1. Previous ChatGPT Project conversations — first source for continuity

Use the most recent available conversations inside the same `dsl` project to recover:

- the product/development intent being discussed;
- design decisions made after the last written checkpoint;
- code changes the assistant said it made;
- the most recent user-provided local terminal evidence;
- failures and their classification (`test defect`, `product defect`, `authority drift`, `environment issue`, `unknown`);
- the exact task that was about to start when the session stopped.

Pay special attention to the tail of the last conversation rather than summarizing the whole history equally.

### 2. Last user-reported local evidence — strongest proof of what actually passed locally

Recover terminal evidence from prior project conversations, especially:

```text
git rev-parse HEAD
focused unittest result
Tactical P1 Full result
failure logs
working-tree / branch information if the user supplied it
```

An exact SHA plus focused PASS plus Full PASS reported by the user is stronger validation evidence than a document that still says `AWAITING_LOCAL_VALIDATION`.

Conversely, a GitHub commit after the last locally tested SHA must not be called trusted merely because it exists remotely.

### 3. Current GitHub repository — source of remote code reality

Always inspect repository `hoonoh57/dsl`, branch `main`, at recovery time.

At minimum recover:

- current `main` HEAD;
- current `CURRENT_STATE.md` and this protocol;
- the changed files / commits between the last locally validated SHA found in project conversation and current `main`, when they differ;
- the relevant newest implementation/checkpoint files for those changed files.

If repository `main` is ahead of the last documented checkpoint, infer what was implemented from the actual changed files and commit history rather than pretending the checkpoint is current.

### 4. Checkpoint and authority documents — source of constraints, not guaranteed recency

`CURRENT_STATE.md` remains the main compact repository state index, but during crash recovery it is **not assumed to be the newest evidence**.

Use it and its authority order to recover architectural constraints and known trusted checkpoints. Then reconcile it against project-conversation evidence and actual GitHub commits.

Architecture authority still outranks an old conversational idea when deciding what code may be changed.

## Required reconciliation algorithm

On every `세션복구`, perform this reasoning before replying or resuming development:

1. Find the last meaningful development exchange in previous `dsl` project conversations.
2. Extract the latest user-reported local SHA and test outcome, if any.
3. Fetch current GitHub `main` HEAD.
4. Read `SESSION_RECOVERY.md` and `CURRENT_STATE.md`, but mark their state text as potentially stale until reconciled.
5. If `main` differs from the last local SHA, inspect the commits/changed files between them.
6. Reconstruct a chronological tail:

```text
last locally trusted executable point
 -> remote changes after that point
 -> any local validation reported after those changes
 -> unfinished decision/work at conversation end
```

7. Classify recovered state internally into:

```text
TRUSTED_LOCAL
  exact SHA backed by prior user local test evidence

REMOTE_UNVALIDATED
  present on GitHub after the latest proven local checkpoint, but no recovered local PASS evidence

CONVERSATION_DECISION
  design/product decision made in prior conversation but not necessarily written to repo yet

UNKNOWN_LOCAL_ONLY
  possible local-PC state that was never shared and never pushed; cannot be reconstructed remotely
```

8. Prefer the newest evidence that is actually supported. Do not downgrade a recovered trusted local PASS because a stale document says awaiting validation, and do not upgrade a remote commit to trusted without evidence.
9. Re-read the relevant authority files before making new executable changes.
10. Resume from the reconstructed immediate next boundary unless the user gives a different instruction.

## Conflict rules

Use these rules when sources disagree:

- **Implementation content:** current GitHub code wins over descriptions in older conversations/documents.
- **Local validation status:** the latest exact user-reported local SHA + test output wins over stale checkpoint text.
- **Unpushed local code:** only facts actually present in prior conversation can be recovered. Never invent unshared local edits.
- **Architecture/permission:** current authority documents win over informal older plans.
- **Product intent/rationale:** recent project conversation is valuable and should be preserved unless it conflicts with authority or newer explicit user direction.

## Local-machine limitation and last-resort rule

The assistant cannot directly inspect the user's current `E:\2026\gemini\dsl` filesystem from a new chat.

This does **not** prevent normal crash recovery because the previous project's conversation usually contains the last local SHA/test output and GitHub contains pushed changes.

Only when the reconstructed state materially depends on information that could exist solely on the user's PC and was neither pushed nor mentioned in prior project conversation may the assistant ask for a minimal local check, for example:

```powershell
git status --short
git rev-parse HEAD
git log -1 --oneline
```

Do not ask for these commands routinely. Ask only when unresolved local-only divergence actually blocks a correct next action.

## First recovery reply — fixed human format

The first reply to `세션복구` must be concise Korean and contain these three sections at normal human abstraction level:

### 1. 개발철학

Explain the philosophy in **five items or fewer**. Default compression:

- **작고 검증된 전술부터 키운다.** 한 번에 거대한 자동매매 시스템을 만들지 않고 작은 전술을 반복 검증·진화시킨다.
- **DSL 핵심은 범용적이고 믿을 수 있게 유지한다.** 계산·신호·주문 같은 공통 기능만 DSL에 두고 시장/섹터/대장주·추종주 판단은 외부 분석 계층에 둔다.
- **미래정보와 숨은 종합점수를 금지한다.** 당시 알 수 있었던 정보만 사용하고 중요한 판단축은 따로 보존한다.
- **상위 정보는 약한 전술을 억지로 살리지 않는다.** 시장·섹터·그룹 정보는 기존 전술의 기회를 검증·제한하는 방향으로 사용한다.
- **최소 기능으로 먼저 실제 가동하고 성공 후 확장한다.** 첫 vertical slice를 작게 완성한 뒤 정교한 패턴·예약주문·다중종목 운영을 단계적으로 넓힌다.

### 2. 최근 한 일

List at most five recent milestones reconstructed from **conversation + GitHub + recovered local evidence**, not merely copied from `CURRENT_STATE.md`.

If a remote tranche exists after the last proven local checkpoint, say naturally that it is implemented but awaiting local validation rather than calling it complete.

### 3. 앞으로 할 일

List at most five immediate steps from the reconstructed tail. The first item should be the actual next executable/product boundary, not a generic roadmap item.

If there is one unresolved local-only ambiguity that truly blocks development, mention the single minimal confirmation needed here. Otherwise do not ask the user to recap or run commands.

## Response style

- Speak to a human product owner, not to a compiler engineer.
- Omit class names, schemas, hashes, filenames and machine detail unless necessary to distinguish trusted vs unvalidated state.
- Do not dump old logs.
- Do not ask `무엇을 하던 중이었나요?`.
- Keep the first answer scannable in under a minute.
- After the summary, autonomous plan -> modify -> verify may resume from the reconstructed boundary.

## Current recovery anchor

The following anchor is only a fallback if conversation/repository reconciliation yields nothing newer. It is **not** assumed to be the latest state at future recovery time.

As of 2026-08-28:

- `CTXINT3` is trusted: next-open entry uses only prior-completed-bar information.
- `LF1` is trusted at `5ec230c8bbada60f0e4b9fe945a5380d7c405fe2`: 7 focused tests and Tactical P1 Full passed.
- LF1 provides minimal leader/follower relationship evidence while retaining no direct order authority.
- The next known executable boundary is generic pending-order cancellation by explicit stable identity.

## Before resuming implementation

After reconstructing the state and before making code changes, re-read the authority order from current `CURRENT_STATE.md` and the authority/checkpoint files directly relevant to the reconstructed next tranche.

Do not use crash recovery as permission to bypass Core DSL freeze, causality, validation, Broker authority or fail-closed behavior.

## Maintenance rule

Normal milestone updates should still update `CURRENT_STATE.md` and this file's fallback anchor when convenient, but **correct recovery must not depend on that update having happened**.

The protocol is considered successful only if an abrupt context-limit termination before any final checkpoint write can still be recovered from previous project conversation evidence plus current repository history.
