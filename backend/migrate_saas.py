"""
migrate_saas.py — add SaaS columns to existing tables

Run from the backend/ directory:
    python migrate_saas.py

Safe to run multiple times (uses IF NOT EXISTS / DO NOTHING patterns).
"""

import os
import sys

# ── Load .env ────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

# psycopg2 expects the plain postgres:// URI (not the +psycopg2 variant)
DB_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

print(f"Connecting to database...")
conn = psycopg2.connect(DB_URL)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# ── 1. Create ENUM types (if they don't exist yet) ───────────────────────────
print("Creating ENUM types...")

cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plan') THEN
        CREATE TYPE plan AS ENUM ('free', 'pro');
    END IF;
END
$$;
""")

cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role') THEN
        CREATE TYPE role AS ENUM ('admin', 'user');
    END IF;
END
$$;
""")

cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentstatus') THEN
        CREATE TYPE paymentstatus AS ENUM ('pending', 'captured', 'failed');
    END IF;
END
$$;
""")

print("  ✓ ENUM types ready")

# ── 2. Add columns to users table ─────────────────────────────────────────────
print("Adding columns to users table...")

alterations = [
    ("plan",            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan plan NOT NULL DEFAULT 'free';"),
    ("role",            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role role NOT NULL DEFAULT 'user';"),
    ("scan_count",      "ALTER TABLE users ADD COLUMN IF NOT EXISTS scan_count INTEGER NOT NULL DEFAULT 0;"),
    ("scan_reset_date", "ALTER TABLE users ADD COLUMN IF NOT EXISTS scan_reset_date DATE NOT NULL DEFAULT CURRENT_DATE;"),
]

for col_name, sql in alterations:
    cur.execute(sql)
    print(f"  ✓ {col_name}")

# ── 3. Create payments table ──────────────────────────────────────────────────
print("Creating payments table...")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    razorpay_order_id    VARCHAR(255) NOT NULL UNIQUE,
    razorpay_payment_id  VARCHAR(255),
    razorpay_signature   VARCHAR(512),
    amount               INTEGER NOT NULL,
    currency             VARCHAR(10) NOT NULL DEFAULT 'INR',
    status               paymentstatus NOT NULL DEFAULT 'pending',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""")

cur.execute("CREATE INDEX IF NOT EXISTS ix_payments_user_id ON payments (user_id);")
cur.execute("CREATE INDEX IF NOT EXISTS ix_payments_razorpay_order_id ON payments (razorpay_order_id);")

print("  ✓ payments table ready")

cur.close()
conn.close()

print("")
print("=" * 50)
print("✅  SaaS migration complete!")
print("=" * 50)
print("")
print("Next steps:")
print("  1. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend/.env")
print("  2. Restart the FastAPI server")
print("  3. To make a user admin: UPDATE users SET role='admin' WHERE email='your@email.com';")
