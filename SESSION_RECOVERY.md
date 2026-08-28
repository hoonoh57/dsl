# DSL Session Recovery Protocol

Status: **AUTHORITATIVE CRASH-SAFE RECOVERY ENTRYPOINT / HANDOFF-FIRST / ACTIVE / 2026-08-28 KST**

## Trigger

When the user sends exactly `세션복구` (or starts a message with `세션복구`) in any new chat inside the `dsl` project, treat it as a recovery command, not as a request for clarification.

The assistant must recover the project immediately without asking the user to restate history.

This protocol is specifically designed for abrupt context-limit termination before the previous session had time to write a final checkpoint.

## Primary handoff rule

`SESSION_HANDOFF.md` is the first human-readable handoff document.

Read it first to recover the project story, recent work and immediate next boundary quickly. Then verify and repair that picture using previous ChatGPT Project conversations and actual GitHub history.

The handoff document is the preferred continuously updated summary, but it is **not assumed to be perfectly current after a crash**.

## Core rule — reconstruct, do not merely trust a document

`세션복구` means:

```text
SESSION_HANDOFF human summary
 + previous project conversation tail
 + latest GitHub repository reality
 + last local evidence reported in conversation
 + CURRENT_STATE / authority documents
 -> reconstruct the most strongly supported current project position
```

A handoff/checkpoint may be stale by one or more commits or validation steps. That is expected.

## Recovery evidence sources

### 1. SESSION_HANDOFF.md — fastest human baseline

Use it to recover:

- development philosophy in five items or fewer;
- recent completed milestones;
- current product position;
- immediate next executable boundary;
- the intended human-level first recovery reply.

### 2. Previous ChatGPT Project conversations — continuity after the last handoff write

Use the newest available conversations inside the same `dsl` project, especially the tail of the last session, to recover:

- design/product decisions made after the handoff was last updated;
- code changes the assistant said it made;
- the most recent user-provided local terminal evidence;
- failure classification (`test defect`, `product defect`, `authority drift`, `environment issue`, `unknown`);
- the exact work that was underway when the session stopped.

### 3. Last user-reported local evidence — strongest proof of local validation

Recover prior terminal evidence, especially:

```text
git rev-parse HEAD
focused unittest result
Tactical P1 Full result
failure logs
working-tree / branch information when supplied
```

An exact SHA plus focused PASS plus Full PASS reported by the user outranks stale text that still says `AWAITING_LOCAL_VALIDATION`.

A newer GitHub commit without recovered local PASS must remain untrusted executable state.

### 4. Current GitHub repository — remote code reality

Always inspect repository `hoonoh57/dsl`, branch `main`.

At minimum recover:

- current `main` HEAD;
- `SESSION_HANDOFF.md`;
- `CURRENT_STATE.md` and this protocol;
- commits/changed files between the last locally validated SHA and current `main` when they differ;
- relevant newest implementation/checkpoint files.

If GitHub is ahead of the handoff, infer what changed from actual commits/files rather than pretending the handoff is current.

### 5. CURRENT_STATE / authority documents — structural authority

`CURRENT_STATE.md` remains the compact machine/project index. Use its authority order before new executable modifications.

Architecture authority outranks informal old conversation ideas when deciding what code may change.

## Required reconciliation algorithm

On every `세션복구`:

1. Read `SESSION_HANDOFF.md` for the fast human baseline.
2. Find the last meaningful development exchange in previous `dsl` project conversations.
3. Extract the latest user-reported local SHA and focused/Full test outcome, if any.
4. Fetch current GitHub `main` HEAD.
5. Read `CURRENT_STATE.md` and this file; treat status text as potentially stale until reconciled.
6. If `main` differs from the last locally validated SHA, inspect commits/changed files between them.
7. Reconstruct the chronological tail:

```text
last locally trusted executable point
 -> remote changes after that point
 -> any local validation reported after those changes
 -> unfinished conversation decision/work
```

8. Internally classify evidence:

```text
TRUSTED_LOCAL
REMOTE_UNVALIDATED
CONVERSATION_DECISION
UNKNOWN_LOCAL_ONLY
```

9. Prefer the newest evidence that is actually supported. Never downgrade a recovered exact PASS because a stale document says waiting, and never upgrade a remote commit to trusted without evidence.
10. Re-read relevant authority files before executable changes.
11. Resume from the reconstructed immediate next boundary unless the user gives a different instruction.

## Conflict rules

- **Implementation content:** current GitHub code wins over older descriptions.
- **Local validation status:** latest exact user-reported local SHA + test output wins over stale checkpoint text.
- **Unpushed local code:** recover only what was actually mentioned in project conversation; never invent unshared local edits.
- **Architecture/permission:** current authority documents win over informal older plans.
- **Product intent/rationale:** newest explicit user direction and recent project conversation should be preserved unless they conflict with authority.

## Local-machine limitation

The assistant cannot directly inspect the user's live `E:\2026\gemini\dsl` filesystem from a new chat.

Normal crash recovery should still work from project conversation + GitHub. Only if a materially important state may exist solely on the user's PC and was never pushed or mentioned may the assistant request a minimal check such as:

```powershell
git status --short
git rev-parse HEAD
git log -1 --oneline
```

Do not ask routinely.

## First recovery reply

The first reply to `세션복구` must be concise Korean and contain only:

### 1. 개발철학
Five items or fewer.

### 2. 최근 한 일
At most five milestones reconstructed from handoff + conversation + GitHub + local evidence.

### 3. 앞으로 할 일
At most five immediate steps from the reconstructed tail.

Speak to a human product owner. Do not dump class names, schemas, hashes or long logs unless needed to distinguish trusted from unvalidated state. Do not ask the user what they were doing.

## Current fallback anchor

This is only a fallback if no newer evidence exists.

- `CTXINT3` trusted: next-open entry uses only prior-completed-bar information.
- `LF1` trusted at `5ec230c8bbada60f0e4b9fe945a5380d7c405fe2` with 7 focused tests and Tactical P1 Full PASS.
- LF1 measures qualified leader/follower relationship evidence but has no direct order authority.
- Next known executable boundary: generic pending-order cancellation by explicit stable identity.

## Maintenance rule

At every meaningful milestone, **update `SESSION_HANDOFF.md` first or together with `CURRENT_STATE.md`** when practical.

Especially update the handoff after:

- a new exact local focused + Full PASS;
- implementation of a new unvalidated tranche;
- a change to the immediate next boundary;
- a material development-philosophy/product-direction decision.

But crash recovery correctness must never depend on the update having happened before a sudden context-limit termination.
