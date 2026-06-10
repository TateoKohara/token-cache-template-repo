PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS fragments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fragment_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    fragment_type TEXT NOT NULL,
    content TEXT NOT NULL,
    source_path TEXT,
    model_scope TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    checksum_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_key TEXT NOT NULL UNIQUE,
    session_label TEXT NOT NULL,
    model_name TEXT,
    branch_name TEXT,
    summary TEXT NOT NULL,
    open_items_json TEXT NOT NULL DEFAULT '[]',
    file_refs_json TEXT NOT NULL DEFAULT '[]',
    command_refs_json TEXT NOT NULL DEFAULT '[]',
    recommended_static_keys_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    checksum_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS packets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    packet_key TEXT NOT NULL UNIQUE,
    snapshot_key TEXT NOT NULL,
    static_keys_json TEXT NOT NULL DEFAULT '[]',
    packet_text TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_key) REFERENCES snapshots(snapshot_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fragments_updated_at ON fragments(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_updated_at ON snapshots(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_packets_snapshot_key ON packets(snapshot_key);