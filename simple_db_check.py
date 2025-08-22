#!/usr/bin/env python3
"""
簡單的資料庫檢查腳本
"""

import sqlite3
import os

def simple_db_check():
    """簡單的資料庫狀態檢查"""
    
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return
    
    try:
        print("🔍 檢查資料庫狀態...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查RMB帳戶餘額
        cursor.execute("SELECT SUM(balance) FROM cash_accounts WHERE currency = 'RMB' AND is_active = 1")
        total_rmb = cursor.fetchone()[0] or 0
        
        # 檢查FIFO庫存
        cursor.execute("SELECT SUM(remaining_rmb) FROM fifo_inventory")
        total_inventory = cursor.fetchone()[0] or 0
        
        print(f"💰 RMB帳戶總餘額: {total_rmb}")
        print(f"📦 FIFO庫存總RMB: {total_inventory}")
        print(f"🔍 差異: {total_inventory - total_rmb}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    simple_db_check()
