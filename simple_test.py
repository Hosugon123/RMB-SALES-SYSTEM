print("Hello World")
print("Testing Python")

import sqlite3
print("SQLite imported successfully")

try:
    conn = sqlite3.connect("instance/sales_system_v4.db")
    print("Database connected")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cash_accounts")
    count = cursor.fetchone()[0]
    print(f"Cash accounts: {count}")
    
    conn.close()
    print("Database closed")
    
except Exception as e:
    print(f"Error: {e}")
