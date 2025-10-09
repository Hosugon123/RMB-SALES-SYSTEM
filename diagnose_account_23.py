#!/usr/bin/env python3
"""診斷帳戶 ID 23 的問題"""

import sqlite3
import os

def diagnose_account():
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查帳戶 ID 23
        print("=== 檢查帳戶 ID 23 ===")
        cursor.execute("SELECT * FROM cash_accounts WHERE id = 23;")
        account_23 = cursor.fetchone()
        
        if account_23:
            print(f"✅ 帳戶 ID 23 存在")
            cursor.execute("PRAGMA table_info(cash_accounts);")
            columns = [col[1] for col in cursor.fetchall()]
            
            print("\n帳戶詳細資訊:")
            for i, col in enumerate(columns):
                print(f"  {col}: {account_23[i]}")
        else:
            print("❌ 帳戶 ID 23 不存在")
        
        # 列出所有 TWD 帳戶
        print("\n=== 所有 TWD 帳戶 ===")
        cursor.execute("SELECT id, name, currency, balance, is_active, holder_id FROM cash_accounts WHERE currency = 'TWD';")
        twd_accounts = cursor.fetchall()
        
        if twd_accounts:
            print(f"找到 {len(twd_accounts)} 個 TWD 帳戶:")
            for acc in twd_accounts:
                status = "✅ 啟用" if acc[4] else "❌ 停用"
                print(f"  ID {acc[0]}: {acc[1]} - 餘額: {acc[3]:,.2f} - {status} - 持有人ID: {acc[5]}")
        else:
            print("❌ 沒有找到任何 TWD 帳戶")
        
        # 列出所有帳戶
        print("\n=== 所有帳戶 ===")
        cursor.execute("SELECT id, name, currency, balance, is_active FROM cash_accounts ORDER BY id;")
        all_accounts = cursor.fetchall()
        
        print(f"總共 {len(all_accounts)} 個帳戶:")
        for acc in all_accounts:
            status = "✅" if acc[4] else "❌"
            print(f"  {status} ID {acc[0]}: {acc[1]} ({acc[2]}) - 餘額: {acc[3]:,.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_account()

