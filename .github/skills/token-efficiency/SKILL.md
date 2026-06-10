---
name: token-efficiency
description: "Use when reducing Copilot token usage, planning long agent work, deciding whether to switch models, splitting heavy exploration into subagents, or resuming after a session reset. Triggers: 'token reduction', 'prompt caching', 'model routing', 'subagent separation', 'context pollution', 'verbose output', 'session switch', 'cache reuse'."
---

# Token Efficiency

Use this skill for repo-local workflow decisions that reduce Copilot token usage without lowering engineering quality.

This skill is for:

- keeping stable context in always-on files instead of restating it each session
- deciding when broad exploration should move to a subagent or targeted search
- choosing terse versus detailed output mode
- routing tasks to cheaper or default models before escalating
- preparing compact handoff or resume packets before a session or model switch

This skill is not for:

- restoring provider-side KV cache
- replacing issue-specific implementation skills
- storing secrets or raw transcripts in repo files
- replacing tracked measurement artifacts or handoffs
- turning user-facing docs into compressed shorthand

## Read First

- `.github/copilot-instructions.md`
- `docs/token-efficiency.md`

## Workflow

1. Keep reusable static rules in `.github/copilot-instructions.md` or a skill, not in repeated user-turn prose.
2. For broad repo exploration, prefer a subagent or targeted search and bring back only findings and anchors.
3. Use terse output for status, summaries, diagnostics, and review findings unless detail is necessary to unblock action.
4. Stay on Auto or a mid-cost model for routine work. Escalate only after the cheap pass is insufficient.
5. Before a session or model switch, save a compact snapshot into the local SQLite cache and render a resume packet.

## Fast Heuristics

- large logs, JSON, or tables: summarize or search them; do not paste them raw into the main context
- design doc to code: keep the design summary in static context, pass only the delta dynamically
- code to design doc: use a subagent to extract only the required symbols and decisions first
- repeated repo rules in chat: move them into static instructions or reusable fragments
- handoffs and design docs: keep them readable; do not force caveman-style compression

## Core Commands

- `uv run python tools/token_cache_db.py bootstrap --db target/token-cache/copilot-context.sqlite3 --seed configs/token-cache/default-fragments.json`
- `uv run python tools/token_cache_db.py save-snapshot --db target/token-cache/copilot-context.sqlite3 ...`
- `uv run python tools/token_cache_db.py render-packet --db target/token-cache/copilot-context.sqlite3 ...`