#!/usr/bin/env python3
"""
檢查資料庫結構
"""

import sqlite3
import os

def check_database():
    """檢查資料庫結構"""
    db_path = "./instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"資料庫文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有表格
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"資料庫表格: {tables}")
        
        # 檢查每個表格的結構
        for table in tables:
            print(f"\n表格 {table} 的結構:")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
        # 檢查是否有user表格
        if 'user' in tables:
            print(f"\nuser表格存在，檢查數據:")
            cursor.execute("SELECT COUNT(*) FROM user")
            count = cursor.fetchone()[0]
            print(f"  用戶數量: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, username FROM user LIMIT 5")
                users = cursor.fetchall()
                for user in users:
                    print(f"  - ID: {user[0]}, 用戶名: {user[1]}")
        else:
            print(f"\n❌ user表格不存在！這是銷帳API失敗的原因。")
            print("銷帳API需要user表格來記錄操作員信息。")
        
        conn.close()
        
    except Exception as e:
        print(f"檢查資料庫時出錯: {e}")

if __name__ == "__main__":
    check_database()
