---
name: "Token Efficiency Assets"
description: "Use when editing token-efficiency instructions or skills, SQLite-backed session cache reuse tooling, resume packet docs, or model-switch handoff assets."
applyTo: ".github/copilot-instructions.md, .github/instructions/token-efficiency.instructions.md, .github/skills/token-efficiency/**, .github/skills/token-cache-reuse/**, tools/token_cache_db.py, tools/token_cache_schema.sql, docs/token-efficiency.md, configs/token-cache/**"
---

# Token Efficiency Guidance

- Keep always-on static instructions short, stable, and free of volatile timestamps or per-run data.
- Put static policy in repo instructions or skills, not in ad hoc repeated chat text.
- Separate static fragments from session snapshots; do not mix them into one growing blob.
- Do not claim that local SQLite recreates provider-side KV cache; it only stores compact reusable context and resume packets.
- Keep the default SQLite path under target/ so runtime cache state stays repo-local and untracked.
- Prefer append-only or upsert-safe snapshot workflows so session history remains recoverable after model switches.
- When adding new static fragments, store concise summaries rather than full transcripts, raw logs, or secrets.