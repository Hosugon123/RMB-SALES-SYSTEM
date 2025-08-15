#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試現金管理頁面問題的腳本
"""

import sqlite3
import os

def debug_cash_management():
    """調試現金管理頁面的問題"""
    
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件 {db_path} 不存在")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查數據庫結構...")
        
        # 檢查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 數據庫中的表: {[table[0] for table in tables]}")
        
        # 檢查 cash_logs 表結構
        if ('cash_logs',) in tables:
            print("\n🔍 檢查 cash_logs 表結構...")
            cursor.execute("PRAGMA table_info(cash_logs)")
            columns = cursor.fetchall()
            print("cash_logs 表欄位:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 檢查 cash_logs 表數據
            cursor.execute("SELECT COUNT(*) FROM cash_logs")
            count = cursor.fetchone()[0]
            print(f"cash_logs 表記錄數: {count}")
            
            if count > 0:
                cursor.execute("SELECT * FROM cash_logs LIMIT 3")
                rows = cursor.fetchall()
                print("前3條記錄:")
                for row in rows:
                    print(f"  {row}")
        else:
            print("❌ cash_logs 表不存在")
        
        # 檢查 user 表結構
        if ('user',) in tables:
            print("\n🔍 檢查 user 表結構...")
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()
            print("user 表欄位:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 檢查 user 表數據
            cursor.execute("SELECT COUNT(*) FROM user")
            count = cursor.fetchone()[0]
            print(f"user 表記錄數: {count}")
        else:
            print("❌ user 表不存在")
        
        # 檢查 cash_accounts 表結構
        if ('cash_accounts',) in tables:
            print("\n🔍 檢查 cash_accounts 表結構...")
            cursor.execute("PRAGMA table_info(cash_accounts)")
            columns = cursor.fetchall()
            print("cash_accounts 表欄位:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 檢查 cash_accounts 表數據
            cursor.execute("SELECT COUNT(*) FROM cash_accounts")
            count = cursor.fetchone()[0]
            print(f"cash_accounts 表記錄數: {count}")
        else:
            print("❌ cash_accounts 表不存在")
        
        # 檢查 holders 表結構
        if ('holders',) in tables:
            print("\n🔍 檢查 holders 表結構...")
            cursor.execute("PRAGMA table_info(holders)")
            columns = cursor.fetchall()
            print("holders 表欄位:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 檢查 holders 表數據
            cursor.execute("SELECT COUNT(*) FROM holders")
            count = cursor.fetchone()[0]
            print(f"holders 表記錄數: {count}")
        else:
            print("❌ holders 表不存在")
        
        # 檢查 customers 表結構
        if ('customers',) in tables:
            print("\n🔍 檢查 customers 表結構...")
            cursor.execute("PRAGMA table_info(customers)")
            columns = cursor.fetchall()
            print("customers 表欄位:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 檢查 customers 表數據
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            print(f"customers 表記錄數: {count}")
        else:
            print("❌ customers 表不存在")
        
        conn.close()
        print("\n✅ 數據庫檢查完成")
        return True
        
    except Exception as e:
        print(f"❌ 檢查數據庫時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始調試現金管理頁面問題...")
    debug_cash_management()
