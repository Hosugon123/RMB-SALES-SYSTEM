#!/usr/bin/env python3
import sqlite3
import os

db_path = 'instance/sales_system.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 檢查表結構
    cursor.execute("PRAGMA table_info(ledger_entries)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print("現有欄位:")
    for col in columns:
        print(f"  - {col}")
    
    print(f"\n是否包含 profit_before: {'profit_before' in columns}")
    print(f"是否包含 profit_after: {'profit_after' in columns}")
    print(f"是否包含 profit_change: {'profit_change' in columns}")
    
    conn.close()
else:
    print(f"數據庫文件不存在: {db_path}")
