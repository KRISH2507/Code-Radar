"""
Database migration script to add scan metrics to repositories table.

This adds the following columns to the repositories table:
- completed_at: Timestamp when scan was completed
- file_count: Total number of files in repository
- line_count: Total number of lines of code

Run this after updating the Repository model.
"""

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    """Add scan metrics columns to repositories table."""
    
    migrations = [
        # Add completed_at column
        """
        ALTER TABLE repositories 
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;
        """,
        
        # Add file_count column
        """
        ALTER TABLE repositories 
        ADD COLUMN IF NOT EXISTS file_count INTEGER DEFAULT 0;
        """,
        
        # Add line_count column
        """
        ALTER TABLE repositories 
        ADD COLUMN IF NOT EXISTS line_count INTEGER DEFAULT 0;
        """,
    ]
    
    with engine.connect() as conn:
        for migration_sql in migrations:
            try:
                conn.execute(text(migration_sql))
                conn.commit()
                print(f"✅ Executed: {migration_sql.strip()[:60]}...")
            except Exception as e:
                print(f"⚠️  Migration warning: {str(e)}")
                # Continue with other migrations
    
    print("\n✅ Database migration completed!")
    print("   Added columns: completed_at, file_count, line_count")

def downgrade():
    """Remove scan metrics columns from repositories table."""
    
    rollbacks = [
        "ALTER TABLE repositories DROP COLUMN IF EXISTS completed_at;",
        "ALTER TABLE repositories DROP COLUMN IF EXISTS file_count;",
        "ALTER TABLE repositories DROP COLUMN IF EXISTS line_count;",
    ]
    
    with engine.connect() as conn:
        for rollback_sql in rollbacks:
            try:
                conn.execute(text(rollback_sql))
                conn.commit()
                print(f"✅ Rolled back: {rollback_sql}")
            except Exception as e:
                print(f"⚠️  Rollback warning: {str(e)}")
    
    print("\n✅ Database rollback completed!")

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🗄️  Repository Scan Metrics Migration")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("\n⬇️  Running downgrade (removing columns)...\n")
        downgrade()
    else:
        print("\n⬆️  Running upgrade (adding columns)...\n")
        upgrade()
    
    print("\n" + "=" * 60)
