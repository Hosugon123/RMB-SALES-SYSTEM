#!/usr/bin/env python3
"""
檢查資料庫結構
"""

import sqlite3
import os

def check_database():
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"資料庫檔案不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== 資料庫資料表 ===")
        for table in tables:
            table_name = table[0]
            print(f"\n📊 資料表: {table_name}")
            
            # 獲取資料表結構
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("   欄位:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # 獲取資料筆數
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   資料筆數: {count}")
            
            # 如果有資料，顯示前幾筆範例
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                print("   範例資料:")
                for i, row in enumerate(rows, 1):
                    print(f"   {i}: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"檢查資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    check_database()
