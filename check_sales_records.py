#!/usr/bin/env python3
"""
檢查銷售記錄的簡單腳本
"""

import sqlite3
import os

def check_database():
    """檢查資料庫中的銷售記錄"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"錯誤: 資料庫文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("銷售記錄檢查報告")
        print("=" * 50)
        
        # 1. 檢查銷售記錄總數
        cursor.execute("SELECT COUNT(*) FROM sales_records")
        sales_count = cursor.fetchone()[0]
        print(f"1. 銷售記錄總數: {sales_count}")
        
        if sales_count > 0:
            # 2. 檢查最近的銷售記錄
            print("\n2. 最近5筆銷售記錄:")
            cursor.execute("""
                SELECT id, customer_id, rmb_account_id, twd_amount, rmb_amount, 
                       exchange_rate, is_settled, created_at
                FROM sales_records 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            for record in records:
                print(f"   ID: {record[0]}, 客戶: {record[1]}, RMB帳戶: {record[2]}, "
                      f"TWD: {record[3]}, RMB: {record[4]}, 已結算: {record[6]}")
            
            # 3. 檢查未結算的銷售記錄
            cursor.execute("SELECT COUNT(*) FROM sales_records WHERE is_settled = 0")
            unsettled_count = cursor.fetchone()[0]
            print(f"\n3. 未結算銷售記錄: {unsettled_count}")
            
        else:
            print("   [警告] 沒有找到任何銷售記錄")
        
        # 4. 檢查記帳記錄
        print("\n4. 記帳記錄檢查:")
        cursor.execute("SELECT COUNT(*) FROM ledger_entries")
        ledger_count = cursor.fetchone()[0]
        print(f"   記帳記錄總數: {ledger_count}")
        
        if ledger_count > 0:
            cursor.execute("SELECT COUNT(*) FROM ledger_entries WHERE entry_type = 'PROFIT_EARNED'")
            profit_count = cursor.fetchone()[0]
            print(f"   利潤入庫記錄: {profit_count}")
        
        # 5. 檢查客戶和帳戶
        print("\n5. 客戶和帳戶檢查:")
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        print(f"   客戶總數: {customer_count}")
        
        cursor.execute("SELECT COUNT(*) FROM cash_accounts")
        account_count = cursor.fetchone()[0]
        print(f"   現金帳戶總數: {account_count}")
        
        # 6. 檢查FIFO分配記錄
        print("\n6. FIFO分配記錄檢查:")
        cursor.execute("SELECT COUNT(*) FROM fifo_sales_allocations")
        fifo_count = cursor.fetchone()[0]
        print(f"   FIFO分配記錄總數: {fifo_count}")
        
        # 7. 檢查表格結構
        print("\n7. 表格結構檢查:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"   現有表格: {[table[0] for table in tables]}")
        
        # 總結
        print("\n" + "=" * 50)
        print("診斷總結")
        print("=" * 50)
        
        if sales_count > 0:
            print("[OK] 銷售記錄存在 - 問題可能在於前端顯示")
            print("建議檢查:")
            print("1. 現金管理頁面的API調用")
            print("2. 前端JavaScript的數據處理")
            print("3. 瀏覽器控制台的錯誤信息")
        else:
            print("[ERROR] 銷售記錄不存在 - 問題在於後端創建")
            print("建議檢查:")
            print("1. api_sales_entry 函數的執行")
            print("2. 資料庫事務是否正確提交")
            print("3. 錯誤處理和日誌記錄")
        
        if ledger_count > 0:
            print("[OK] 記帳記錄存在")
        else:
            print("[ERROR] 記帳記錄不存在")
        
        print("\n下一步建議:")
        print("1. 檢查瀏覽器開發者工具的Network標籤")
        print("2. 查看後端日誌中的錯誤信息")
        print("3. 測試手動創建銷售記錄")
        
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    check_database()
