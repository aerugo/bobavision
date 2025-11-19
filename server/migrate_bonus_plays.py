"""Migration script to add bonus_plays fields to client_settings table.

This script adds:
- bonus_plays_count (INTEGER, default 0)
- bonus_plays_date (DATE, nullable)

Run this script once to upgrade existing databases.
"""
import sqlite3
import sys
from pathlib import Path

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def migrate():
    """Add bonus_plays fields to client_settings table."""
    # Get database path
    db_path = Path(__file__).parent / "bobavision.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("No migration needed - database will be created with new schema.")
        return 0

    print(f"Migrating database at {db_path}")

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check and add bonus_plays_count column
        if not check_column_exists(cursor, "client_settings", "bonus_plays_count"):
            print("Adding bonus_plays_count column...")
            cursor.execute(
                "ALTER TABLE client_settings ADD COLUMN bonus_plays_count INTEGER NOT NULL DEFAULT 0"
            )
            print("✓ Added bonus_plays_count column")
        else:
            print("✓ bonus_plays_count column already exists")

        # Check and add bonus_plays_date column
        if not check_column_exists(cursor, "client_settings", "bonus_plays_date"):
            print("Adding bonus_plays_date column...")
            cursor.execute(
                "ALTER TABLE client_settings ADD COLUMN bonus_plays_date DATE"
            )
            print("✓ Added bonus_plays_date column")
        else:
            print("✓ bonus_plays_date column already exists")

        # Commit changes
        conn.commit()
        print("\n✓ Migration completed successfully!")
        return 0

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        return 1

    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(migrate())
