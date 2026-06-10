# Token Efficiency Playbook

## Goal

Reduce Copilot chat and agent token usage by separating static and dynamic context, routing work to the cheapest viable model, and persisting compact resume packets for session or model switches.

## Important Constraint

Local SQLite does not recreate provider-side prompt or KV cache. It stores compact reusable context so a new session or a different model can restart from a short, stable packet instead of a full transcript replay.

## Recommended Operating Rules

1. Keep static project rules in `.github/copilot-instructions.md`.
2. Put static context above dynamic context in any packet or summary.
3. Use terse output for status, reviews, and diagnostics.
4. Use subagents or targeted search for heavy repo exploration.
5. Before any model or session switch, save a snapshot and render a resume packet.

## Four Levers

### 1. Concise output

- default to short answers unless detail is needed
- do not spend tokens on filler, repeated framing, or large narrative summaries
- keep docs and handoffs readable; do not use compressed shorthand where clarity matters

### 2. Static above dynamic

- keep stable policy in `.github/copilot-instructions.md` and skills
- avoid changing ordering or adding session-specific noise to static instruction files
- keep session-specific state in SQLite snapshots, not in always-on instructions

### 3. Model routing

- use Auto or a cheaper default model for light search, summarization, and routine edits when possible
- reserve expensive models for hard design, deep debugging, or complex multi-step reasoning
- avoid switching models mid-task unless necessary because it throws away prompt-cache locality

### 4. Subagent separation

- use subagents or isolated read-only exploration for broad searches and codebase surveys
- bring back only the distilled summary to the main thread
- do not let heavy exploration pollute the main context window when a summary will do

## SQLite Location

- Default path: `target/token-cache/copilot-context.sqlite3`
- Reason: repo-local, reproducible, and ignored by git through the existing `target/` rule

## Quickstart

```sh
uv run python tools/token_cache_db.py bootstrap \
  --db target/token-cache/copilot-context.sqlite3 \
  --reset \
  --seed configs/token-cache/default-fragments.json
```

Use `--reset` when a local schema change or a failed earlier bootstrap left behind an incompatible SQLite file.

For the normal pre-switch flow, prefer the one-step wrapper:

```sh
uv run python tools/token_cache_db.py prepare-switch \
  --db target/token-cache/copilot-context.sqlite3 \
  --model "GPT-5.4" \
  --summary "Short summary of current state" \
  --open-item "Next concrete step" \
  --file-ref docs/token-efficiency.md
```

This saves the snapshot, stores the packet in SQLite, and writes a packet file under `target/token-cache/` in one step. Use the manual commands below when you need explicit snapshot keys or separate save and render timing.

For repeatable handoff summaries, keep the tracked template generic and copy it into an untracked working file before editing:

```sh
cp configs/token-cache/session-summary-template.md target/token-cache/current-session-summary.md
```

Then fill the sections in the working copy and run:

```sh
uv run python tools/token_cache_db.py prepare-switch \
  --db target/token-cache/copilot-context.sqlite3 \
  --model "GPT-5.4" \
  --summary-template-file target/token-cache/current-session-summary.md
```

Reference files:

- Tracked blank scaffold: `configs/token-cache/session-summary-template.md`
- Tracked example: `configs/token-cache/session-summary-example.md`

```sh
uv run python tools/token_cache_db.py save-snapshot \
  --db target/token-cache/copilot-context.sqlite3 \
  --snapshot-key example-restart-point \
  --session-label "Example restart point" \
  --model "GPT-5.4" \
  --summary "Short summary of current state" \
  --static-key token-efficiency-baseline \
  --static-key project-static-frame \
  --open-item "Next concrete step" \
  --file-ref docs/token-efficiency.md \
  --command-ref "uv run python tools/token_cache_db.py list-fragments"
```

```sh
uv run python tools/token_cache_db.py render-packet \
  --db target/token-cache/copilot-context.sqlite3 \
  --snapshot-key example-restart-point \
  --static-key token-efficiency-baseline \
  --static-key project-static-frame \
  --stdout
```

## Snapshot Content Rule

Snapshots should contain only:

- one short summary
- current model and branch
- open items
- file anchors
- command anchors

Avoid storing raw logs, large code dumps, secrets, or full conversation history.

## Template Repository Notes

- Keep tracked templates and examples publication-safe and generic.
- Put project-specific or session-specific working summaries under `target/token-cache/` or another untracked path.
- Reuse the CLI and schema as the stable surface; adapt fragments, instructions, and examples per repository.
- In this repository, `default-fragments.json` may stay project-specific after the standalone template repo is published.