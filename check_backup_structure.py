#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查備份數據庫結構
"""

import sqlite3
import os

def check_backup_structure():
    """檢查備份數據庫結構"""
    backup_path = 'recovery_backups/sales_system_v4_backup_20250823_001011.db'
    
    if not os.path.exists(backup_path):
        print(f"❌ 備份文件不存在: {backup_path}")
        return
    
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # 獲取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 備份數據庫中的表:")
        for table in tables:
            table_name = table[0]
            print(f"   - {table_name}")
            
            # 獲取表結構
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print(f"     列:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"       {col_name} ({col_type})")
            
            # 獲取記錄數
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"     記錄數: {count}")
            except:
                print(f"     記錄數: 無法獲取")
            print()
        
        # 特別檢查 sales_records 表
        print("🔍 特別檢查 sales_records 表:")
        try:
            cursor.execute("SELECT * FROM sales_records LIMIT 1;")
            sample_record = cursor.fetchone()
            if sample_record:
                print(f"   樣本記錄: {sample_record}")
            else:
                print("   沒有銷售記錄")
        except Exception as e:
            print(f"   無法讀取銷售記錄: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查備份數據庫結構失敗: {e}")

if __name__ == "__main__":
    check_backup_structure()
