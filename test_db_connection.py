#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據庫連接
"""

import sqlite3
import os

def test_connection():
    """測試數據庫連接"""
    print("🔍 開始測試數據庫連接...")
    
    # 檢查數據庫文件是否存在
    db_path = "instance/sales_system_v4.db"
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ 數據庫連接成功！")
        
        # 測試簡單查詢
        cursor.execute("SELECT COUNT(*) FROM cash_accounts")
        count = cursor.fetchone()[0]
        print(f"📊 cash_accounts表記錄數: {count}")
        
        cursor.execute("SELECT COUNT(*) FROM fifo_inventory")
        count = cursor.fetchone()[0]
        print(f"📦 fifo_inventory表記錄數: {count}")
        
        # 檢查RMB帳戶
        cursor.execute("SELECT COUNT(*) FROM cash_accounts WHERE currency = 'RMB'")
        rmb_count = cursor.fetchone()[0]
        print(f"💰 RMB帳戶數量: {rmb_count}")
        
        if rmb_count > 0:
            cursor.execute("SELECT SUM(balance) FROM cash_accounts WHERE currency = 'RMB'")
            total_rmb = cursor.fetchone()[0] or 0
            print(f"📊 總RMB餘額: {total_rmb:,.2f}")
        
        # 檢查庫存
        cursor.execute("SELECT SUM(remaining_rmb) FROM fifo_inventory")
        total_inventory = cursor.fetchone()[0] or 0
        print(f"📦 總庫存RMB: {total_inventory:,.2f}")
        
        return True
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 數據庫連接測試工具")
    print("=" * 60)
    
    test_connection()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")
    print("=" * 60)
