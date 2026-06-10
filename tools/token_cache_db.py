#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("target/token-cache/copilot-context.sqlite3")
SCHEMA_PATH = Path(__file__).with_name("token_cache_schema.sql")
DEFAULT_STATIC_KEYS = ["token-efficiency-baseline", "project-static-frame"]
DEFAULT_SUMMARY_TEMPLATE = Path("configs/token-cache/session-summary-template.md")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(read_text(SCHEMA_PATH))
    connection.commit()


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def normalize_items(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [value.strip() for value in values if value and value.strip()]


def choose_static_keys(values: list[str] | None) -> list[str]:
    keys = normalize_items(values)
    return keys or list(DEFAULT_STATIC_KEYS)


def template_heading_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    heading = stripped.lstrip("#").strip().lower()
    return heading or None


def template_summary_lines(lines: list[str]) -> list[str]:
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        collected.append(line.rstrip())
    return collected


def template_list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return items


def load_summary_template(path: Path) -> dict[str, Any]:
    section_map = {
        "summary": "summary",
        "open items": "open_items",
        "file anchors": "file_refs",
        "command anchors": "command_refs",
        "tags": "tags",
    }
    sections = {value: [] for value in section_map.values()}
    current_section: str | None = None

    for line in read_text(path).splitlines():
        heading = template_heading_key(line)
        if heading is not None:
            current_section = section_map.get(heading)
            continue
        if current_section is None:
            continue
        sections[current_section].append(line)

    return {
        "summary": "\n".join(template_summary_lines(sections["summary"])).strip(),
        "open_items": template_list_items(sections["open_items"]),
        "file_refs": template_list_items(sections["file_refs"]),
        "command_refs": template_list_items(sections["command_refs"]),
        "tags": template_list_items(sections["tags"]),
    }


def resolve_snapshot_payload(args: argparse.Namespace) -> dict[str, Any]:
    template_path_value = getattr(args, "summary_template_file", None)
    if template_path_value and (getattr(args, "summary", None) or getattr(args, "summary_file", None)):
        raise ValueError("Use either --summary/--summary-file or --summary-template-file")

    template_payload = {
        "summary": "",
        "open_items": [],
        "file_refs": [],
        "command_refs": [],
        "tags": [],
    }
    if template_path_value:
        template_payload = load_summary_template(Path(template_path_value).resolve())

    if getattr(args, "summary_file", None):
        summary = read_text(Path(args.summary_file).resolve())
    elif getattr(args, "summary", None):
        summary = args.summary or ""
    else:
        summary = template_payload["summary"]

    summary = summary.strip()
    if not summary:
        raise ValueError("A non-empty summary is required")

    return {
        "summary": summary,
        "open_items": template_payload["open_items"] + normalize_items(getattr(args, "open_item", None)),
        "file_refs": template_payload["file_refs"] + normalize_items(getattr(args, "file_ref", None)),
        "command_refs": template_payload["command_refs"] + normalize_items(getattr(args, "command_ref", None)),
        "tags": template_payload["tags"] + normalize_items(getattr(args, "tag", None)),
    }


def normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        lines = [str(item).strip() for item in content if str(item).strip()]
        return "\n".join(f"- {line}" for line in lines)
    raise TypeError(f"Unsupported content type: {type(content)!r}")


def git_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-") or "switch"


def default_snapshot_key(session_label: str, branch_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = slugify(branch_name or session_label or "switch")
    return f"{base}-{stamp}"


def default_packet_output(repo_root: Path, snapshot_key: str) -> Path:
    return (repo_root / "target" / "token-cache" / f"{snapshot_key}-packet.md").resolve()


def default_render_command(snapshot_key: str) -> str:
    return (
        "uv run python tools/token_cache_db.py render-packet "
        f"--db {DEFAULT_DB} --snapshot-key {snapshot_key} --stdout"
    )


def upsert_fragment(
    connection: sqlite3.Connection,
    *,
    fragment_key: str,
    title: str,
    fragment_type: str,
    content: str,
    source_path: str | None,
    model_scope: str | None,
    tags: list[str],
) -> None:
    checksum = sha256_text(content)
    connection.execute(
        """
        INSERT INTO fragments (
            fragment_key,
            title,
            fragment_type,
            content,
            source_path,
            model_scope,
            tags_json,
            checksum_sha256
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(fragment_key) DO UPDATE SET
            title = excluded.title,
            fragment_type = excluded.fragment_type,
            content = excluded.content,
            source_path = excluded.source_path,
            model_scope = excluded.model_scope,
            tags_json = excluded.tags_json,
            checksum_sha256 = excluded.checksum_sha256,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            fragment_key,
            title,
            fragment_type,
            content,
            source_path,
            model_scope,
            dump_json(tags),
            checksum,
        ),
    )


def upsert_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_key: str,
    session_label: str,
    model_name: str,
    branch_name: str,
    summary: str,
    open_items: list[str],
    file_refs: list[str],
    command_refs: list[str],
    static_keys: list[str],
    tags: list[str],
) -> None:
    checksum_payload = {
        "session_label": session_label,
        "model_name": model_name,
        "branch_name": branch_name,
        "summary": summary,
        "open_items": open_items,
        "file_refs": file_refs,
        "command_refs": command_refs,
        "static_keys": static_keys,
        "tags": tags,
    }
    checksum = sha256_text(dump_json(checksum_payload))
    connection.execute(
        """
        INSERT INTO snapshots (
            snapshot_key,
            session_label,
            model_name,
            branch_name,
            summary,
            open_items_json,
            file_refs_json,
            command_refs_json,
            recommended_static_keys_json,
            tags_json,
            checksum_sha256
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(snapshot_key) DO UPDATE SET
            session_label = excluded.session_label,
            model_name = excluded.model_name,
            branch_name = excluded.branch_name,
            summary = excluded.summary,
            open_items_json = excluded.open_items_json,
            file_refs_json = excluded.file_refs_json,
            command_refs_json = excluded.command_refs_json,
            recommended_static_keys_json = excluded.recommended_static_keys_json,
            tags_json = excluded.tags_json,
            checksum_sha256 = excluded.checksum_sha256,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            snapshot_key,
            session_label,
            model_name,
            branch_name,
            summary,
            dump_json(open_items),
            dump_json(file_refs),
            dump_json(command_refs),
            dump_json(static_keys),
            dump_json(tags),
            checksum,
        ),
    )


def upsert_packet(
    connection: sqlite3.Connection,
    *,
    packet_key: str,
    snapshot_key: str,
    static_keys: list[str],
    packet_text: str,
) -> None:
    checksum = sha256_text(packet_text)
    connection.execute(
        """
        INSERT INTO packets (
            packet_key,
            snapshot_key,
            static_keys_json,
            packet_text,
            checksum_sha256
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(packet_key) DO UPDATE SET
            snapshot_key = excluded.snapshot_key,
            static_keys_json = excluded.static_keys_json,
            packet_text = excluded.packet_text,
            checksum_sha256 = excluded.checksum_sha256
        """,
        (packet_key, snapshot_key, dump_json(static_keys), packet_text, checksum),
    )


def load_seed(seed_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    payload = json.loads(read_text(seed_path))
    fragments = payload.get("fragments")
    if not isinstance(fragments, list):
        raise ValueError("Seed file must contain a 'fragments' array")
    normalized: list[dict[str, Any]] = []
    for fragment in fragments:
        source_file = fragment.get("content_file")
        if source_file:
            content = read_text((repo_root / source_file).resolve())
        else:
            content = normalize_content(fragment.get("content", fragment.get("lines", "")))
        normalized.append(
            {
                "fragment_key": fragment["key"],
                "title": fragment["title"],
                "fragment_type": fragment.get("fragment_type", fragment.get("type", "static")),
                "content": content,
                "source_path": fragment.get("source_path") or source_file,
                "model_scope": fragment.get("model_scope"),
                "tags": normalize_items(fragment.get("tags")),
            }
        )
    return normalized


def fetch_snapshot(connection: sqlite3.Connection, snapshot_key: str | None) -> sqlite3.Row:
    if snapshot_key:
        row = connection.execute(
            "SELECT * FROM snapshots WHERE snapshot_key = ?",
            (snapshot_key,),
        ).fetchone()
    else:
        row = connection.execute(
            "SELECT * FROM snapshots ORDER BY updated_at DESC, id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        raise ValueError("No matching snapshot found")
    return row


def fetch_fragments(connection: sqlite3.Connection, fragment_keys: list[str]) -> list[sqlite3.Row]:
    if not fragment_keys:
        return []
    placeholders = ",".join("?" for _ in fragment_keys)
    rows = connection.execute(
        f"SELECT * FROM fragments WHERE fragment_key IN ({placeholders})",
        tuple(fragment_keys),
    ).fetchall()
    keyed_rows = {row["fragment_key"]: row for row in rows}
    missing = [key for key in fragment_keys if key not in keyed_rows]
    if missing:
        raise ValueError(f"Missing fragments: {', '.join(missing)}")
    return [keyed_rows[key] for key in fragment_keys]


def build_packet(snapshot: sqlite3.Row, fragments: list[sqlite3.Row]) -> str:
    open_items = json.loads(snapshot["open_items_json"])
    file_refs = json.loads(snapshot["file_refs_json"])
    command_refs = json.loads(snapshot["command_refs_json"])

    parts: list[str] = [f"# Resume Packet: {snapshot['snapshot_key']}", ""]

    if fragments:
        parts.extend(["## Static Context", ""])
        for fragment in fragments:
            parts.extend([f"### {fragment['title']}", fragment["content"], ""])

    parts.extend(
        [
            "## Session Snapshot",
            f"- session: {snapshot['session_label']}",
            f"- model: {snapshot['model_name'] or 'unspecified'}",
            f"- branch: {snapshot['branch_name'] or 'unknown'}",
            f"- saved_at: {snapshot['updated_at']}",
            "",
            "### Summary",
            snapshot["summary"],
            "",
        ]
    )

    if open_items:
        parts.extend(["### Open Items", *[f"- {item}" for item in open_items], ""])

    if file_refs:
        parts.extend(["### File Anchors", *[f"- {item}" for item in file_refs], ""])

    if command_refs:
        parts.extend(["### Command Anchors", *[f"- {item}" for item in command_refs], ""])

    parts.extend(
        [
            "### Resume Rule",
            "- Use the static section above as the stable prefix.",
            "- Treat the snapshot section as the dynamic suffix.",
            "- Avoid replaying full transcript history unless it contains irreplaceable evidence.",
            "",
        ]
    )
    return "\n".join(parts).rstrip() + "\n"


def cmd_init(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    if args.reset and db_path.exists():
        db_path.unlink()
    connection = connect(db_path)
    init_db(connection)
    print(f"db={db_path}")
    print(f"reset={'true' if args.reset else 'false'}")
    print("result=initialized")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    repo_root = Path(args.repo_root).resolve()
    seed_path = Path(args.seed).resolve()
    if args.reset and db_path.exists():
        db_path.unlink()
    connection = connect(db_path)
    init_db(connection)
    fragments = load_seed(seed_path, repo_root)
    for fragment in fragments:
        upsert_fragment(connection, **fragment)
    connection.commit()
    print(f"db={db_path}")
    print(f"seed={seed_path}")
    print(f"reset={'true' if args.reset else 'false'}")
    print(f"fragments={len(fragments)}")
    print("result=bootstrapped")
    return 0


def cmd_save_snapshot(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    repo_root = Path(args.repo_root).resolve()
    payload = resolve_snapshot_payload(args)
    branch_name = args.branch or git_branch(repo_root)
    connection = connect(db_path)
    init_db(connection)
    upsert_snapshot(
        connection,
        snapshot_key=args.snapshot_key,
        session_label=args.session_label,
        model_name=(args.model or "").strip(),
        branch_name=branch_name,
        summary=payload["summary"],
        open_items=payload["open_items"],
        file_refs=payload["file_refs"],
        command_refs=payload["command_refs"],
        static_keys=normalize_items(args.static_key),
        tags=payload["tags"],
    )
    connection.commit()
    print(f"db={db_path}")
    print(f"snapshot_key={args.snapshot_key}")
    print(f"branch={branch_name or 'unknown'}")
    print("result=snapshot_saved")
    return 0


def cmd_render_packet(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    connection = connect(db_path)
    init_db(connection)
    snapshot = fetch_snapshot(connection, args.snapshot_key)
    requested_keys = normalize_items(args.static_key)
    if not requested_keys:
        requested_keys = json.loads(snapshot["recommended_static_keys_json"])
    fragments = fetch_fragments(connection, requested_keys)
    packet_text = build_packet(snapshot, fragments)

    if args.packet_key:
        upsert_packet(
            connection,
            packet_key=args.packet_key,
            snapshot_key=snapshot["snapshot_key"],
            static_keys=requested_keys,
            packet_text=packet_text,
        )
        connection.commit()

    if args.output:
        output_path = Path(args.output).resolve()
        write_text(output_path, packet_text)
        print(f"output={output_path}")
    if args.stdout or not args.output:
        sys.stdout.write(packet_text)

    if args.packet_key:
        print(f"packet_key={args.packet_key}")
    return 0


def cmd_prepare_switch(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    repo_root = Path(args.repo_root).resolve()
    payload = resolve_snapshot_payload(args)

    branch_name = args.branch or git_branch(repo_root)
    snapshot_key = args.snapshot_key or default_snapshot_key(args.session_label, branch_name)
    static_keys = choose_static_keys(args.static_key)
    command_refs = list(payload["command_refs"])
    if not command_refs:
        command_refs = [default_render_command(snapshot_key)]

    packet_key = (args.packet_key or f"{snapshot_key}-packet").strip()
    if not packet_key:
        raise ValueError("Packet key must be non-empty")

    connection = connect(db_path)
    init_db(connection)
    upsert_snapshot(
        connection,
        snapshot_key=snapshot_key,
        session_label=args.session_label,
        model_name=(args.model or "").strip(),
        branch_name=branch_name,
        summary=payload["summary"],
        open_items=payload["open_items"],
        file_refs=payload["file_refs"],
        command_refs=command_refs,
        static_keys=static_keys,
        tags=payload["tags"],
    )
    snapshot = fetch_snapshot(connection, snapshot_key)
    fragments = fetch_fragments(connection, static_keys)
    packet_text = build_packet(snapshot, fragments)
    upsert_packet(
        connection,
        packet_key=packet_key,
        snapshot_key=snapshot_key,
        static_keys=static_keys,
        packet_text=packet_text,
    )
    connection.commit()

    output_path = Path(args.output).resolve() if args.output else default_packet_output(repo_root, snapshot_key)
    write_text(output_path, packet_text)

    print(f"db={db_path}")
    print(f"snapshot_key={snapshot_key}")
    print(f"packet_key={packet_key}")
    print(f"output={output_path}")
    print(f"branch={branch_name or 'unknown'}")
    print(f"static_keys={','.join(static_keys)}")
    print("result=switch_prepared")
    if args.stdout:
        sys.stdout.write(packet_text)
    return 0


def cmd_list_fragments(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    connection = connect(db_path)
    init_db(connection)
    rows = connection.execute(
        "SELECT fragment_key, title, fragment_type, updated_at FROM fragments ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    for row in rows:
        print(
            f"{row['fragment_key']}\t{row['fragment_type']}\t{row['updated_at']}\t{row['title']}"
        )
    return 0


def cmd_list_snapshots(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    connection = connect(db_path)
    init_db(connection)
    rows = connection.execute(
        "SELECT snapshot_key, session_label, model_name, branch_name, updated_at FROM snapshots ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    for row in rows:
        model_name = row["model_name"] or "unspecified"
        branch_name = row["branch_name"] or "unknown"
        print(
            f"{row['snapshot_key']}\t{model_name}\t{branch_name}\t{row['updated_at']}\t{row['session_label']}"
        )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    db_path = Path(args.db).resolve()
    query = f"%{args.query.strip()}%"
    if query == "%%":
        raise ValueError("Search query must be non-empty")
    connection = connect(db_path)
    init_db(connection)
    rows = connection.execute(
        """
        SELECT 'fragment' AS kind, fragment_key AS item_key, title, content AS body, updated_at
        FROM fragments
        WHERE fragment_key LIKE ? OR title LIKE ? OR content LIKE ?
        UNION ALL
        SELECT 'snapshot' AS kind, snapshot_key AS item_key, session_label AS title, summary AS body, updated_at
        FROM snapshots
        WHERE snapshot_key LIKE ? OR session_label LIKE ? OR summary LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (query, query, query, query, query, query, args.limit),
    ).fetchall()
    for row in rows:
        body = row["body"].replace("\n", " ")
        snippet = body[:160] + ("..." if len(body) > 160 else "")
        print(
            f"{row['kind']}\t{row['item_key']}\t{row['updated_at']}\t{row['title']}\t{snippet}"
        )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Store compact static fragments and session snapshots for Copilot token-efficient resume flows"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize the SQLite cache database.")
    init_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    init_parser.add_argument("--reset", action="store_true", help="Delete an existing database file before initialization.")

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Initialize the database and seed default static fragments.",
    )
    bootstrap_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    bootstrap_parser.add_argument("--reset", action="store_true", help="Delete an existing database file before bootstrapping.")
    bootstrap_parser.add_argument(
        "--seed",
        default="configs/token-cache/default-fragments.json",
        help="JSON seed file containing default fragments.",
    )
    bootstrap_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve any seed content_file paths.",
    )

    save_snapshot_parser = subparsers.add_parser(
        "save-snapshot",
        help="Save or update a compact session snapshot before a model or session switch.",
    )
    save_snapshot_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    save_snapshot_parser.add_argument("--repo-root", default=".", help="Repository root used for branch detection.")
    save_snapshot_parser.add_argument("--snapshot-key", required=True, help="Stable key for this snapshot.")
    save_snapshot_parser.add_argument("--session-label", required=True, help="Human-readable session label.")
    save_snapshot_parser.add_argument("--model", help="Model name used for the current session.")
    save_snapshot_parser.add_argument("--branch", help="Git branch name. Defaults to the current branch.")
    save_snapshot_parser.add_argument("--summary", help="Inline summary text.")
    save_snapshot_parser.add_argument("--summary-file", help="Path to a summary file.")
    save_snapshot_parser.add_argument(
        "--summary-template-file",
        default=None,
        help=(
            "Structured markdown file with Summary/Open Items/File Anchors/Command Anchors/Tags sections. "
            f"Tracked template: {DEFAULT_SUMMARY_TEMPLATE}"
        ),
    )
    save_snapshot_parser.add_argument("--open-item", action="append", help="Open item to resume later.")
    save_snapshot_parser.add_argument("--file-ref", action="append", help="Relevant file anchor.")
    save_snapshot_parser.add_argument("--command-ref", action="append", help="Relevant command anchor.")
    save_snapshot_parser.add_argument("--static-key", action="append", help="Recommended static fragment key.")
    save_snapshot_parser.add_argument("--tag", action="append", help="Snapshot tag.")

    render_packet_parser = subparsers.add_parser(
        "render-packet",
        help="Render a resume packet from static fragments plus a saved snapshot.",
    )
    render_packet_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    render_packet_parser.add_argument("--snapshot-key", help="Snapshot key. Defaults to the latest snapshot.")
    render_packet_parser.add_argument("--static-key", action="append", help="Static fragment key. Defaults to the snapshot's recommended keys.")
    render_packet_parser.add_argument("--packet-key", help="Optional packet key to persist in the packets table.")
    render_packet_parser.add_argument("--output", help="Optional output path for the rendered packet.")
    render_packet_parser.add_argument("--stdout", action="store_true", help="Also print the rendered packet to stdout.")

    prepare_switch_parser = subparsers.add_parser(
        "prepare-switch",
        help="Save a switch snapshot and render a resume packet in one step.",
    )
    prepare_switch_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    prepare_switch_parser.add_argument("--repo-root", default=".", help="Repository root used for branch detection and default packet output.")
    prepare_switch_parser.add_argument("--snapshot-key", help="Stable key for this snapshot. Defaults to a branch-based timestamp key.")
    prepare_switch_parser.add_argument("--session-label", default="Model or session switch", help="Human-readable session label.")
    prepare_switch_parser.add_argument("--model", help="Model name used for the current session.")
    prepare_switch_parser.add_argument("--branch", help="Git branch name. Defaults to the current branch.")
    prepare_switch_parser.add_argument("--summary", help="Inline summary text.")
    prepare_switch_parser.add_argument("--summary-file", help="Path to a summary file.")
    prepare_switch_parser.add_argument(
        "--summary-template-file",
        default=None,
        help=(
            "Structured markdown file with Summary/Open Items/File Anchors/Command Anchors/Tags sections. "
            f"Tracked template: {DEFAULT_SUMMARY_TEMPLATE}"
        ),
    )
    prepare_switch_parser.add_argument("--open-item", action="append", help="Open item to resume later.")
    prepare_switch_parser.add_argument("--file-ref", action="append", help="Relevant file anchor.")
    prepare_switch_parser.add_argument("--command-ref", action="append", help="Relevant command anchor.")
    prepare_switch_parser.add_argument("--static-key", action="append", help="Static fragment key. Defaults to the standard token-efficiency keys.")
    prepare_switch_parser.add_argument("--tag", action="append", help="Snapshot tag.")
    prepare_switch_parser.add_argument("--packet-key", help="Packet key to persist. Defaults to <snapshot-key>-packet.")
    prepare_switch_parser.add_argument("--output", help="Output path for the rendered packet. Defaults to target/token-cache/<snapshot-key>-packet.md.")
    prepare_switch_parser.add_argument("--stdout", action="store_true", help="Also print the rendered packet to stdout.")

    list_fragments_parser = subparsers.add_parser(
        "list-fragments",
        help="List stored static fragments.",
    )
    list_fragments_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")

    list_snapshots_parser = subparsers.add_parser(
        "list-snapshots",
        help="List stored session snapshots.",
    )
    list_snapshots_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")

    search_parser = subparsers.add_parser(
        "search",
        help="Search stored fragments and snapshots.",
    )
    search_parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    search_parser.add_argument("--query", required=True, help="Search term.")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of matches to show.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command_map = {
        "init": cmd_init,
        "bootstrap": cmd_bootstrap,
        "save-snapshot": cmd_save_snapshot,
        "render-packet": cmd_render_packet,
        "prepare-switch": cmd_prepare_switch,
        "list-fragments": cmd_list_fragments,
        "list-snapshots": cmd_list_snapshots,
        "search": cmd_search,
    }
    handler = command_map[args.command]
    try:
        return handler(args)
    except Exception as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())