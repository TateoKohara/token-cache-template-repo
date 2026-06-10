# Release Notes v0.1.0

Copilot Token Cache Template の初回公開版です。

## 内容

- token 効率を意識した Copilot instructions
- token-efficiency と token-cache reuse の reusable skill
- `bootstrap`、`prepare-switch`、`save-snapshot`、`render-packet` を備えた SQLite CLI
- session handoff packet 用の tracked summary template
- public template surface を検証する GitHub Actions workflow
- 英語版 / 日本語版 README と公開手順書

## Validation

- `uv run python tools/validate_token_cache_template.py`
- GitHub Actions workflow: `Token Cache Template Validation`

## Notes

- `configs/token-cache/default-fragments.json` は意図的に generic にしてあり、consumer repository ごとに差し替える前提です。
- 実際の working summary は `target/token-cache/` などの untracked path に置いてください。