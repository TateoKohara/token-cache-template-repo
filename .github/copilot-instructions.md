# Copilot Token Efficiency Baseline

## Token Efficiency

- Keep stable project rules in this file or repo skills; do not restate them ad hoc in each session.
- Prefer terse answers for status, summaries, and diagnostics unless the user asks for depth or the risk demands detail.
- Put static context first and dynamic context last when building prompts, summaries, or resume packets.
- Do not paste large logs, JSON, or code into chat when targeted search, file anchors, or a compact summary will do.
- Use subagents or targeted search for broad exploration and return only findings, anchors, and the next decision.

## Model Routing

- Default to Auto or a mid-cost model for routine edits, narrow debugging, and mechanical refactors.
- Escalate to a higher-cost model only for architecture changes, hard diagnosis, or after a cheaper pass failed.
- Avoid switching models mid-task. If a switch is necessary, save a SQLite snapshot first.

## Session Cache Reuse

- Provider-side prompt or KV cache cannot be restored locally after a model switch or a new session.
- Use uv run python tools/token_cache_db.py with the default DB at target/token-cache/copilot-context.sqlite3.
- Store compact reusable fragments and session snapshots, not full transcripts or giant logs.
- Before ending or switching sessions, persist summary, open items, touched files, validation commands, and the next step.
- Resume new sessions from render-packet output plus the static baseline instead of replaying full transcript history.

## Output Rules

- Lead with the conclusion, then give only the evidence needed to act.
- For implementation tasks, read narrowly, edit quickly, and validate immediately.
- Keep static docs deterministic. Put timestamps, run-specific logs, and volatile state outside the static baseline.