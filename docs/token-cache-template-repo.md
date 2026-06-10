# Token Cache Template Repo Guide

This document describes how to use this repository after it has been published as a standalone token-cache template.

## Read First

- [README.md](../README.md)
- [README_ja.md](../README_ja.md)
- [PUBLISHING.md](../PUBLISHING.md)
- [PUBLISHING_ja.md](../PUBLISHING_ja.md)
- [docs/token-efficiency.md](token-efficiency.md)

## What To Customize First

Replace these files before regular use in a consumer repository.

- `.github/copilot-instructions.md`
- `configs/token-cache/default-fragments.json`
- `configs/token-cache/session-summary-example.md`
- `docs/token-efficiency.md`

Keep these files generic and reusable.

- `.github/instructions/token-efficiency.instructions.md`
- `.github/skills/token-efficiency/SKILL.md`
- `.github/skills/token-cache-reuse/SKILL.md`
- `configs/token-cache/session-summary-template.md`
- `tools/token_cache_db.py`
- `tools/token_cache_schema.sql`
- `tools/validate_token_cache_template.py`
- `.github/workflows/token-cache-template.yml`

## Validation

Run this after any template change.

```sh
uv run python tools/validate_token_cache_template.py
```

This validates:

- clean bootstrap into SQLite
- fragment seeding from `configs/token-cache/default-fragments.json`
- `prepare-switch` with the tracked example summary
- `prepare-switch` with a generated working summary
- `render-packet` output regeneration

## Publishing Checklist

1. Update `configs/token-cache/default-fragments.json` with publish-safe generic defaults.
2. Check that `README.md` and `README_ja.md` match the current CLI surface.
3. Run `uv run python tools/validate_token_cache_template.py`.
4. Confirm `.github/workflows/token-cache-template.yml` still covers every public template asset.

## Consumer Checklist

1. Replace `project-static-frame` in `configs/token-cache/default-fragments.json` with repository-specific static context.
2. Update `configs/token-cache/session-summary-example.md` to match the target codebase.
3. Keep real working summaries under `target/token-cache/` or another untracked path.
4. Use `prepare-switch` before a session reset or model switch.