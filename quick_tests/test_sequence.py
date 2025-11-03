#!/usr/bin/env python3
"""
Test script to reproduce the delete/create ID issue.
"""
import asyncio
import sys
import os

# Add to path and change directory
sys.path.insert(0, '/home/alfonso/repos/archaeologist/api')
os.chdir('/home/alfonso/repos/archaeologist/api')

try:
    import sqlite3
    from pathlib import Path
    
    db_path = Path("archaeologist.db")
    if db_path.exists():
        print("Testing source ID sequence...")
        
        # Connect to database directly
        conn = sqlite3.connect("archaeologist.db")
        conn.row_factory = sqlite3.Row
        
        # Check current sources
        cursor = conn.execute("SELECT id, original_filename FROM sources ORDER BY id DESC LIMIT 5")
        sources = cursor.fetchall()
        
        print(f"Current sources (last 5):")
        for source in sources:
            print(f"  ID: {source['id']}, File: {source['original_filename']}")
        
        # Test deletion
        if sources:
            test_id = sources[0]['id']  # Delete the most recent one
            print(f"\n--- Testing deletion of source ID {test_id} ---")
            
            cursor = conn.execute("DELETE FROM sources WHERE id = ?", (test_id,))
            conn.commit()
            print(f"Deleted {cursor.rowcount} rows")
            
            # Check what the next ID will be
            cursor = conn.execute("SELECT seq FROM sqlite_sequence WHERE name = 'sources'")
            seq_info = cursor.fetchone()
            if seq_info:
                print(f"SQLite sequence for 'sources': {seq_info['seq']}")
            else:
                print("No sequence info found for 'sources' table")
            
            # Test insertion
            print(f"\n--- Testing insertion of new source ---")
            cursor.execute("""
                INSERT INTO sources (
                    project_id, filename, original_filename, file_size,
                    file_type, content_type, data_lake_entry_id, metadata, uploaded_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, "test.txt", "test.txt", 100,
                "text/plain", "text", "test-entry", 
                '{"comment": "test comment"}',
                1
            ))
            conn.commit()
            
            new_id = cursor.lastrowid
            print(f"New source ID: {new_id}")
            
            # Check if it's using deleted ID
            if new_id == test_id:
                print("❌ PROBLEM: New source got deleted ID!")
            else:
                print("✅ OK: New source got different ID")
            
            # Clean up test insertion
            cursor.execute("DELETE FROM sources WHERE id = ?", (new_id,))
            conn.commit()
            
            # Try VACUUM to reset sequence
            print(f"\n--- Testing VACUUM ---")
            conn.execute("VACUUM")
            
            # Check sequence again
            cursor = conn.execute("SELECT seq FROM sqlite_sequence WHERE name = 'sources'")
            seq_info = cursor.fetchone()
            if seq_info:
                print(f"SQLite sequence after VACUUM: {seq_info['seq']}")
        
        conn.close()
    else:
        print("❌ Database file not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()