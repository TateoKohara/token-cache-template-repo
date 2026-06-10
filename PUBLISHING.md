# Token Cache Template Publishing Guide

Use this guide when publishing the standalone token-cache template repository generated from the source repository.

## 1. Regenerate The Standalone Repo

From the source repository root, run:

```sh
uv run python tools/export_token_cache_template.py --output target/token-cache-template-repo --reset
```

## 2. Validate The Exported Repo

Run validation inside the exported repository:

```sh
cd target/token-cache-template-repo
uv run python tools/validate_token_cache_template.py
```

Do not publish if this command fails.

## 3. Sanity-Check The Public Surface

Before publishing, check these files manually:

- `LICENSE`
- `README.md`
- `README_ja.md`
- `PUBLISHING.md`
- `PUBLISHING_ja.md`
- `RELEASE_NOTES.md`
- `RELEASE_NOTES_ja.md`
- `configs/token-cache/default-fragments.json`
- `.github/workflows/token-cache-template.yml`

Confirm that:

- the README files describe the current CLI surface
- the license matches the intended open-use policy
- the release notes match the intended public release
- the default fragments are generic and publish-safe
- no source-repo-only paths or private context remain

## 4. Publish To GitHub

Option A: create the remote in the GitHub web UI, then push from the exported directory.

```sh
cd target/token-cache-template-repo
git init
git checkout -b main
git add .
git commit -m "Initial template release"
git remote add origin <your-new-repo-url>
git push -u origin main
```

Option B: use the GitHub CLI if it is available.

```sh
cd target/token-cache-template-repo
git init
git checkout -b main
git add .
git commit -m "Initial template release"
gh repo create <owner>/<repo> --public --source . --remote origin --push
```

## 5. Create The Initial GitHub Release

After the first push, create a tagged release from the exported repository.

```sh
cd target/token-cache-template-repo
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes-file RELEASE_NOTES.md
```

## 6. Post-Publish Checks

After publishing, verify:

- the repository home page renders `README.md` correctly
- `README_ja.md` is present and readable
- the `v0.1.0` release is visible with the expected notes
- the GitHub Actions workflow starts and passes
- the repository contains no `target/` runtime leftovers beyond `.gitignore`

## 7. Update The Source Repo Only When Needed

The exported template repository is the public artifact.
The source repository remains the place where future edits, exports, and validations are prepared.