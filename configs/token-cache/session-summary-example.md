# Example Session Summary

## Summary
Prepare the token-efficiency workflow for publication as a reusable template repository.
The next session should keep the generic SQLite workflow intact and only swap in project-specific static fragments.

## Open Items
- Check that default static fragment names stay generic enough for template users.
- Keep repo-specific instructions and artifacts out of reusable cache fragments.

## File Anchors
- docs/token-efficiency.md
- tools/token_cache_db.py

## Command Anchors
- uv run python tools/token_cache_db.py list-fragments --db target/token-cache/copilot-context.sqlite3

## Tags
- template-repo
- session-switch