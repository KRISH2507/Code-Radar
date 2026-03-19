"""
Schema migration — adds columns introduced in the extended Scan model.
Safe to re-run: all statements use IF NOT EXISTS / IF EXISTS.
"""
from app.core.database import engine
from sqlalchemy import text

migrations = [
    # ---- scans table new columns ----
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS task_id VARCHAR(255)",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS error_message TEXT",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS health_score FLOAT",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS language_stats JSONB",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS critical_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS high_count     INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS medium_count   INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS low_count      INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS info_count     INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS total_files    INTEGER DEFAULT 0",
    "ALTER TABLE scans ADD COLUMN IF NOT EXISTS total_lines    INTEGER DEFAULT 0",
    # widen the status column so new enum values fit
    "ALTER TABLE scans ALTER COLUMN status TYPE VARCHAR(20)",
    # If old worker wrote 'processing', normalise to 'running'
    "UPDATE scans SET status = 'running'   WHERE status = 'processing'",
    "UPDATE scans SET status = 'completed' WHERE status = 'done'",
    # indexes
    "CREATE INDEX IF NOT EXISTS ix_scans_repository_id_created ON scans (repository_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_scans_status ON scans (status)",
    # ---- repositories table ----
    "ALTER TABLE repositories ADD COLUMN IF NOT EXISTS health_score FLOAT",
]

print("Running schema migrations...")
with engine.begin() as conn:
    for sql in migrations:
        try:
            conn.execute(text(sql))
            print(f"  OK  : {sql[:75]}")
        except Exception as e:
            print(f"  SKIP: {str(e)[:90]}")

print("\nMigration complete.")
