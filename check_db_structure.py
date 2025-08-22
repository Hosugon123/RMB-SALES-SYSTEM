#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查數據庫表結構
"""

import sqlite3
import os

def check_db_structure():
    """檢查數據庫表結構"""
    print("🔍 開始檢查數據庫表結構...")
    
    # 檢查數據庫文件是否存在
    db_path = "instance/sales_system_v4.db"
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 數據庫中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 檢查關鍵表是否存在
        key_tables = ['cash_account', 'holder', 'fifo_inventory', 'purchase_record', 'fifo_sales_allocation']
        missing_tables = []
        
        for table in key_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n❌ 缺少關鍵表: {missing_tables}")
        else:
            print(f"\n✅ 所有關鍵表都存在")
        
        # 檢查cash_account表結構
        try:
            cursor.execute("PRAGMA table_info(cash_account)")
            columns = cursor.fetchall()
            print(f"\n📋 cash_account表結構:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        except Exception as e:
            print(f"❌ 無法獲取cash_account表結構: {e}")
        
        # 檢查fifo_inventory表結構
        try:
            cursor.execute("PRAGMA table_info(fifo_inventory)")
            columns = cursor.fetchall()
            print(f"\n📦 fifo_inventory表結構:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        except Exception as e:
            print(f"❌ 無法獲取fifo_inventory表結構: {e}")
        
        return True
            
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 數據庫表結構檢查工具")
    print("=" * 60)
    
    check_db_structure()
    
    print("\n" + "=" * 60)
    print("✅ 檢查完成")
    print("=" * 60)
