#!/usr/bin/env python3
"""
Simple test script
"""

print("Starting test...")

try:
    import sqlite3
    print("sqlite3 import successful")
    
    import os
    print("os import successful")
    
    # Check database file
    db_path = 'instance/sales_system_v4.db'
    if os.path.exists(db_path):
        print(f"Database file exists: {db_path}")
        
        # Try to connect
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables")
        
        conn.close()
    else:
        print(f"Database file does not exist: {db_path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed")
