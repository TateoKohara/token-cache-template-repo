# Token Cache Template 公開手順

この手順は、source repository から生成した standalone token-cache template repository を GitHub に公開する時に使います。

## 1. Standalone Repo を再生成する

source repository の root で次を実行します。

```sh
uv run python tools/export_token_cache_template.py --output target/token-cache-template-repo --reset
```

## 2. Exported Repo を検証する

export 後の repository で validation を実行します。

```sh
cd target/token-cache-template-repo
uv run python tools/validate_token_cache_template.py
```

このコマンドが失敗した状態では公開しません。

## 3. 公開 surface を目視確認する

公開前に次を確認します。

- `LICENSE`
- `README.md`
- `README_ja.md`
- `PUBLISHING.md`
- `PUBLISHING_ja.md`
- `RELEASE_NOTES.md`
- `RELEASE_NOTES_ja.md`
- `configs/token-cache/default-fragments.json`
- `.github/workflows/token-cache-template.yml`

確認ポイント:

- README が現在の CLI surface と一致している
- license が想定した open-use policy と一致している
- release notes が今回公開する内容と一致している
- default fragments が generic かつ publish-safe である
- source repository 専用 path や private context が残っていない

## 4. GitHub に公開する

方法 A: GitHub の Web UI で remote repository を先に作成し、exported directory から push します。

```sh
cd target/token-cache-template-repo
git init
git checkout -b main
git add .
git commit -m "Initial template release"
git remote add origin <your-new-repo-url>
git push -u origin main
```

方法 B: GitHub CLI が使えるなら次でも構いません。

```sh
cd target/token-cache-template-repo
git init
git checkout -b main
git add .
git commit -m "Initial template release"
gh repo create <owner>/<repo> --public --source . --remote origin --push
```

## 5. 初回 GitHub Release を作成する

最初の push の後で、exported repository から tag と release を作成します。

```sh
cd target/token-cache-template-repo
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes-file RELEASE_NOTES.md
```

## 6. 公開後の確認

公開後は次を確認します。

- repository のトップで `README.md` が正しく表示される
- `README_ja.md` が存在し、読める
- `v0.1.0` release が作成され、想定した notes が表示される
- GitHub Actions workflow が起動し、成功する
- `.gitignore` 以外に `target/` の runtime 生成物が混ざっていない

## 7. source repository の役割

公開される成果物は exported template repository です。
source repository 側は今後も編集、再 export、validation の準備場所として使います。