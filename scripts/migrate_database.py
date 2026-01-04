#!/usr/bin/env python3
"""
Database schema migratie voor Obsidian integration.

Voegt structured fields toe aan ai_summaries tabel.
Draai dit script op de server na git pull.
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'newsbot.db'

def check_column_exists(cursor, table_name, column_name):
    """Check of een kolom al bestaat in een tabel."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Voeg ontbrekende kolommen toe aan ai_summaries."""

    if not DB_PATH.exists():
        print(f"✗ Database niet gevonden: {DB_PATH}")
        sys.exit(1)

    print(f"Migreren van database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Nieuwe kolommen voor structured content
    new_columns = {
        'title': 'TEXT',
        'why_matters': 'TEXT',
        'big_picture': 'TEXT',
        'key_details': 'TEXT',
        'next_step': 'TEXT',
        'source_name': 'TEXT',
        'source_url': 'TEXT'
    }

    added_columns = []

    for column_name, column_type in new_columns.items():
        if not check_column_exists(cursor, 'ai_summaries', column_name):
            print(f"  Adding column: {column_name} ({column_type})")
            cursor.execute(f"ALTER TABLE ai_summaries ADD COLUMN {column_name} {column_type}")
            added_columns.append(column_name)
        else:
            print(f"  Column exists: {column_name}")

    if added_columns:
        conn.commit()
        print(f"\n✓ Migration complete - added {len(added_columns)} columns")
        print(f"  New columns: {', '.join(added_columns)}")
    else:
        print("\n✓ Schema already up to date - no changes needed")

    conn.close()

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
