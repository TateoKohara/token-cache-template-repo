# Copilot Token Cache Template

Reusable GitHub Copilot instructions, skills, and a local SQLite resume cache for token-efficient work across session resets and model switches.

## What This Template Provides

- stable Copilot instructions for concise, cache-friendly workflows
- reusable skills for token-efficiency and token-cache reuse
- a local SQLite CLI for `bootstrap`, `prepare-switch`, `save-snapshot`, and `render-packet`
- tracked summary templates for handoff-ready resume packets
- GitHub Actions validation for the template surface

## Quickstart

```sh
uv run python tools/token_cache_db.py bootstrap \
  --db target/token-cache/copilot-context.sqlite3 \
  --reset \
  --seed configs/token-cache/default-fragments.json
```

```sh
cp configs/token-cache/session-summary-template.md target/token-cache/current-session-summary.md
```

Fill `target/token-cache/current-session-summary.md`, then run:

```sh
uv run python tools/token_cache_db.py prepare-switch \
  --db target/token-cache/copilot-context.sqlite3 \
  --model "GPT-5.4" \
  --summary-template-file target/token-cache/current-session-summary.md
```

In the next session, reuse the packet written under `target/token-cache/` or re-render it with:

```sh
uv run python tools/token_cache_db.py render-packet \
  --db target/token-cache/copilot-context.sqlite3 \
  --snapshot-key <snapshot-key> \
  --stdout
```

## Files to Customize Per Repository

- `.github/copilot-instructions.md`
- `configs/token-cache/default-fragments.json`
- `configs/token-cache/session-summary-example.md`
- `docs/token-efficiency.md`

Keep the published template repository generic and publish-safe. After copying it into a consumer repository, replace `configs/token-cache/default-fragments.json` with that repository's stable static context, and keep real working summaries under `target/token-cache/` or another untracked path.

Bootstrap a consumer repository like this:

```sh
uv run python tools/token_cache_db.py bootstrap \
  --db target/token-cache/copilot-context.sqlite3 \
  --reset \
  --seed configs/token-cache/default-fragments.json
```

## Validation

```sh
uv run python tools/validate_token_cache_template.py
```

This checks bootstrap, fragment seeding, template-backed `prepare-switch`, generated working-summary flow, and packet rendering.

For the actual GitHub publishing steps, see `PUBLISHING.md` after exporting this template repository.

## Next Steps

- replace the `project-static-frame` fragment content in `configs/token-cache/default-fragments.json` with your repository summary
- adapt the example summary to your codebase and team workflow
- keep the validation workflow enabled before publishing template changes