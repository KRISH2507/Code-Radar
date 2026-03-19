#!/usr/bin/env python3
"""
Database Initialization Script

This script handles database operations:
- Create all tables
- Drop all tables (with confirmation)
- Reset database (drop + create)

Usage:
    python init_db.py                    # Create tables
    python init_db.py --drop             # Drop all tables (requires confirmation)
    python init_db.py --reset            # Drop and recreate (requires confirmation)
    python init_db.py --create           # Create tables (same as no args)
"""

import sys
from app.core.database import create_tables, drop_tables, reset_database, engine
from app.models import ALL_MODELS


def confirm_action(message: str) -> bool:
    """Ask user for confirmation."""
    response = input(f"{message} (yes/no): ").strip().lower()
    return response in ('yes', 'y')


def show_tables():
    """Show all registered models/tables."""
    print("\n📋 Registered Models:")
    print("=" * 50)
    for model in ALL_MODELS:
        table_name = model.__tablename__
        print(f"   ✓ {model.__name__:20s} → {table_name}")
    print("=" * 50)
    print(f"Total models: {len(ALL_MODELS)}\n")


def main():
    """Main function to handle database operations."""
    
    # Determine action from command line arguments
    action = sys.argv[1] if len(sys.argv) > 1 else '--create'
    
    print("\n" + "=" * 70)
    print("🗄️  Code Radar - Database Initialization")
    print("=" * 70)
    
    # Show database URL (hide password)
    db_url = str(engine.url)
    if '@' in db_url and ':' in db_url:
        # Hide password in URL
        parts = db_url.split('@')
        user_pass = parts[0].split('://')[-1]
        if ':' in user_pass:
            user = user_pass.split(':')[0]
            db_url = db_url.replace(user_pass, f"{user}:****")
    
    print(f"📍 Database: {db_url}")
    
    # Show all models
    show_tables()
    
    # Execute action
    if action == '--create':
        print("🔧 Action: Create Tables")
        print("-" * 70)
        create_tables()
        print("\n✅ Done! All tables are ready.\n")
        
    elif action == '--drop':
        print("⚠️  Action: Drop All Tables")
        print("-" * 70)
        print("⚠️  WARNING: This will DELETE all tables and data!")
        if confirm_action("Are you sure you want to drop all tables?"):
            drop_tables()
            print("\n✅ All tables dropped.\n")
        else:
            print("\n❌ Operation cancelled.\n")
            
    elif action == '--reset':
        print("🔄 Action: Reset Database (Drop + Create)")
        print("-" * 70)
        print("⚠️  WARNING: This will DELETE all data and recreate tables!")
        if confirm_action("Are you sure you want to reset the database?"):
            reset_database()
            print("\n✅ Database reset complete!\n")
        else:
            print("\n❌ Operation cancelled.\n")
            
    else:
        print(f"❌ Unknown action: {action}")
        print("\nUsage:")
        print("  python init_db.py           # Create tables")
        print("  python init_db.py --create  # Create tables")
        print("  python init_db.py --drop    # Drop all tables")
        print("  python init_db.py --reset   # Drop and recreate\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
