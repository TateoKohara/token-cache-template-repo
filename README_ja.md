# Copilot Token Cache Template

session リセットや model 切り替え時の token 消費を抑えるための、GitHub Copilot 用 instructions / skills とローカル SQLite resume cache の公開テンプレートです。

## このテンプレートに含まれるもの

- 簡潔で cache-friendly な作業フローを前提にした Copilot instructions
- token-efficiency と token-cache reuse の reusable skill
- `bootstrap`、`prepare-switch`、`save-snapshot`、`render-packet` を備えた SQLite CLI
- handoff 用 resume packet を作るための tracked summary template
- template surface を壊さないための GitHub Actions validation

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

`target/token-cache/current-session-summary.md` を埋めたら、次を実行します。

```sh
uv run python tools/token_cache_db.py prepare-switch \
  --db target/token-cache/copilot-context.sqlite3 \
  --model "GPT-5.4" \
  --summary-template-file target/token-cache/current-session-summary.md
```

次の session では、`target/token-cache/` に出力された packet をそのまま使うか、必要に応じて次で再生成します。

```sh
uv run python tools/token_cache_db.py render-packet \
  --db target/token-cache/copilot-context.sqlite3 \
  --snapshot-key <snapshot-key> \
  --stdout
```

## Repository ごとに差し替えるファイル

- `.github/copilot-instructions.md`
- `configs/token-cache/default-fragments.json`
- `configs/token-cache/session-summary-example.md`
- `docs/token-efficiency.md`

公開された template repository は generic かつ publish-safe に保ち、consumer repository 側では `configs/token-cache/default-fragments.json` をその repository 固有の static context に差し替えます。実際の working summary は `target/token-cache/` などの untracked path に置きます。

consumer repository の bootstrap は次です。

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

この検証では bootstrap、fragment seed、template 経由の `prepare-switch`、blank template から作った working summary 経路、packet render をまとめて確認します。

## License

このテンプレートは MIT License で公開しています。template 本体またはその重要部分を再配布する場合は、著作権表示と license 文を保持してください。詳細は `LICENSE` を参照してください。

GitHub 公開の具体的な手順は、template repository を export した後の `PUBLISHING.md` と `PUBLISHING_ja.md` を参照してください。

## 公開前の仕上げ

- `project-static-frame` fragment の対象 repository 向け内容を `configs/token-cache/default-fragments.json` に反映する
- example summary を対象 codebase と team 運用に合わせて更新する
- template 変更時は validation workflow を必ず通す