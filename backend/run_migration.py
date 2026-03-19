"""
Migration: Add SaaS columns to users table.
Run once: python run_migration.py
"""
from datetime import date
from app.core.database import engine
from sqlalchemy import text, inspect


def run():
    insp = inspect(engine)
    existing_cols = [c["name"] for c in insp.get_columns("users")]
    print("Existing columns:", existing_cols)

    with engine.connect() as conn:
        today = date.today().isoformat()

        migrations = [
            ("plan",           "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro'))"),
            ("role",           "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user'))"),
            ("scan_count",     "ALTER TABLE users ADD COLUMN IF NOT EXISTS scan_count INTEGER NOT NULL DEFAULT 0"),
            ("scan_reset_date",f"ALTER TABLE users ADD COLUMN IF NOT EXISTS scan_reset_date DATE NOT NULL DEFAULT '{today}'"),
        ]

        for col_name, sql in migrations:
            if col_name in existing_cols:
                print(f"  SKIP {col_name} (already exists)")
                continue
            print(f"  ADD  {col_name} ...")
            conn.execute(text(sql))
            conn.commit()
            print(f"       OK")

    # Verify
    insp2 = inspect(engine)
    final_cols = [c["name"] for c in insp2.get_columns("users")]
    print("\nFinal columns:", final_cols)
    print("\nMigration complete!")


if __name__ == "__main__":
    run()
