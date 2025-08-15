#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
為 cash_logs 表添加 account_id 欄位的腳本
"""

import sqlite3
import os

def add_account_id_to_cash_logs():
    """為 cash_logs 表添加 account_id 欄位"""
    
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件 {db_path} 不存在")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查 cash_logs 表結構...")
        
        # 檢查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cash_logs'")
        if not cursor.fetchone():
            print("❌ cash_logs 表不存在")
            return False
        
        # 檢查 account_id 欄位是否已存在
        cursor.execute("PRAGMA table_info(cash_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'account_id' in columns:
            print("✅ account_id 欄位已存在")
            return True
        
        print("🔧 添加 account_id 欄位...")
        
        # 添加 account_id 欄位
        cursor.execute("ALTER TABLE cash_logs ADD COLUMN account_id INTEGER")
        
        # 創建外鍵約束（如果支持）
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cash_logs_account_id 
                ON cash_logs(account_id)
            """)
            print("✅ 創建了 account_id 索引")
        except Exception as e:
            print(f"⚠️ 創建索引時出現警告: {e}")
        
        # 提交更改
        conn.commit()
        
        print("✅ 成功添加 account_id 欄位到 cash_logs 表")
        
        # 驗證更改
        cursor.execute("PRAGMA table_info(cash_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 當前欄位: {columns}")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加欄位時發生錯誤: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 開始為 cash_logs 表添加 account_id 欄位...")
    success = add_account_id_to_cash_logs()
    
    if success:
        print("🎉 操作完成！")
    else:
        print("💥 操作失敗！")
