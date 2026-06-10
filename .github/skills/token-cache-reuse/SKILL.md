---
name: token-cache-reuse
description: "Use when saving or restoring work across session changes or model switches, creating compact resume packets, or managing the local SQLite token cache. Triggers: 'resume packet', 'session switch', 'model switch', 'SQLite cache', 'token cache reuse', 'save snapshot'."
---

# Token Cache Reuse

Use this skill for the repo-local SQLite workflow that preserves reusable context when Copilot session state or model-side cache is lost.

This skill is for:

- bootstrapping the local SQLite cache
- storing concise static fragments for reuse
- saving per-task snapshots before session or model switches
- rendering compact resume packets for a new session
- searching prior snapshots instead of replaying long transcript history

This skill is not for:

- recreating provider-side KV cache
- storing secrets, credentials, or full raw logs
- replacing canonical handoffs or tracked artifacts
- keeping binary SQLite files under version control

## Read First

- `.github/copilot-instructions.md`
- `docs/token-efficiency.md`
- `tools/token_cache_schema.sql`

## Workflow

1. Bootstrap the cache once with the default static fragments.
2. Before a model or session switch, prefer `prepare-switch` to save a snapshot and render the packet in one step.
3. For structured handoffs, copy `configs/token-cache/session-summary-template.md` into an untracked working file and pass it with `--summary-template-file`.
4. Use the separate `save-snapshot` and `render-packet` commands only when you need explicit control over timing or keys.
5. Start the next session from that packet instead of replaying the full transcript.
6. Keep snapshots concise; the cache is for high-value context, not chat exhaust.

## Command Pattern

1. Bootstrap: `uv run python tools/token_cache_db.py bootstrap --db target/token-cache/copilot-context.sqlite3 --reset --seed configs/token-cache/default-fragments.json`
2. Normal pre-switch path: `uv run python tools/token_cache_db.py prepare-switch --db target/token-cache/copilot-context.sqlite3 --model <model> --summary "<short summary>" --open-item "<next step>"`
3. Template-backed pre-switch path: `uv run python tools/token_cache_db.py prepare-switch --db target/token-cache/copilot-context.sqlite3 --model <model> --summary-template-file target/token-cache/current-session-summary.md`
4. Manual save: `uv run python tools/token_cache_db.py save-snapshot --db target/token-cache/copilot-context.sqlite3 --snapshot-key <key> --session-label <label> --model <model> --summary-file <file> --static-key token-efficiency-baseline --static-key project-static-frame`
5. Manual render: `uv run python tools/token_cache_db.py render-packet --db target/token-cache/copilot-context.sqlite3 --snapshot-key <key> --output target/token-cache/<key>-packet.md`
6. Search old state: `uv run python tools/token_cache_db.py search --db target/token-cache/copilot-context.sqlite3 --query <term>`

## Template Repo Rule

- Keep tracked templates generic and publishable.
- Keep real session summaries in untracked paths such as `target/token-cache/`.

## Minimum Snapshot Shape

- one summary paragraph or a few tight bullets
- open items
- touched file refs
- validation commands already run
- exact next step