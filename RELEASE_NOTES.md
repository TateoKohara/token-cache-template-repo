# Release Notes v0.1.0

Initial public release of the Copilot Token Cache Template.

## Included

- stable Copilot instructions for token-efficient workflows
- reusable skills for token-efficiency and token-cache reuse
- SQLite CLI for `bootstrap`, `prepare-switch`, `save-snapshot`, and `render-packet`
- tracked summary templates for session handoff packets
- GitHub Actions validation for the public template surface
- English and Japanese README plus publishing guides

## Validation

- `uv run python tools/validate_token_cache_template.py`
- GitHub Actions workflow: `Token Cache Template Validation`

## Notes

- `configs/token-cache/default-fragments.json` is intentionally generic and should be replaced per consumer repository.
- real working summaries belong under `target/token-cache/` or another untracked path.