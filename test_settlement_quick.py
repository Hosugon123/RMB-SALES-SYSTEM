#!/usr/bin/env python3
"""
銷帳功能快速測試腳本

這個腳本可以快速測試銷帳功能是否正常工作，無需啟動完整的Flask應用。
"""

import sqlite3
import os
import sys
import json
from datetime import datetime

def test_settlement_locally():
    """本地測試銷帳功能"""
    print("🧪 銷帳功能快速測試")
    print("=" * 50)
    
    # 連接資料庫
    db_path = "./instance/sales_system.db"
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print(f"✅ 成功連接到資料庫: {db_path}")
    except Exception as e:
        print(f"❌ 連接資料庫失敗: {e}")
        return False
    
    try:
        # 1. 檢查資料庫結構
        print("\n🔍 檢查資料庫結構...")
        
        # 檢查關鍵表格
        tables = ['customers', 'cash_accounts', 'ledger_entries', 'cash_logs', 'users']
        for table in tables:
            cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✅ 表格 {table} 存在")
            else:
                print(f"❌ 表格 {table} 不存在")
                return False
        
        # 2. 檢查客戶數據
        print("\n👥 檢查客戶數據...")
        cursor = conn.execute("SELECT COUNT(*) as count FROM customers WHERE total_receivables_twd > 0")
        customer_count = cursor.fetchone()['count']
        print(f"✅ 有應收帳款的客戶數量: {customer_count}")
        
        if customer_count == 0:
            print("⚠️ 沒有客戶有應收帳款，無法測試銷帳功能")
            return False
        
        # 3. 檢查帳戶數據
        print("\n💰 檢查帳戶數據...")
        cursor = conn.execute("SELECT COUNT(*) as count FROM cash_accounts WHERE currency = 'TWD' AND is_active = 1")
        account_count = cursor.fetchone()['count']
        print(f"✅ 可用的台幣帳戶數量: {account_count}")
        
        if account_count == 0:
            print("⚠️ 沒有可用的台幣帳戶，無法測試銷帳功能")
            return False
        
        # 4. 檢查用戶數據
        print("\n👤 檢查用戶數據...")
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        print(f"✅ 用戶數量: {user_count}")
        
        if user_count == 0:
            print("⚠️ 沒有用戶，無法測試銷帳功能")
            return False
        
        # 5. 獲取測試數據
        print("\n📋 獲取測試數據...")
        
        # 獲取第一個有應收帳款的客戶
        cursor = conn.execute("""
            SELECT id, name, total_receivables_twd 
            FROM customers 
            WHERE total_receivables_twd > 0
            ORDER BY total_receivables_twd DESC
            LIMIT 1
        """)
        customer = cursor.fetchone()
        print(f"✅ 測試客戶: {customer['name']} (ID: {customer['id']}, 應收帳款: {customer['total_receivables_twd']})")
        
        # 獲取第一個台幣帳戶
        cursor = conn.execute("""
            SELECT ca.id, ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'TWD' AND ca.is_active = 1
            ORDER BY ca.name
            LIMIT 1
        """)
        account = cursor.fetchone()
        print(f"✅ 測試帳戶: {account['name']} ({account['holder_name']}) (ID: {account['id']}, 餘額: {account['balance']})")
        
        # 獲取第一個用戶
        cursor = conn.execute("SELECT id, username FROM users ORDER BY id LIMIT 1")
        user = cursor.fetchone()
        print(f"✅ 測試用戶: {user['username']} (ID: {user['id']})")
        
        # 6. 模擬銷帳操作
        print("\n🔄 模擬銷帳操作...")
        
        # 使用較小的金額進行測試
        test_amount = min(1.0, customer['total_receivables_twd'] * 0.1)
        print(f"   測試金額: {test_amount}")
        
        # 開始事務
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # 更新客戶應收帳款
            new_receivables = customer['total_receivables_twd'] - test_amount
            conn.execute("UPDATE customers SET total_receivables_twd = ? WHERE id = ?", 
                        (new_receivables, customer['id']))
            print("✅ 客戶應收帳款更新成功")
            
            # 更新帳戶餘額
            new_balance = account['balance'] + test_amount
            conn.execute("UPDATE cash_accounts SET balance = ? WHERE id = ?", 
                        (new_balance, account['id']))
            print("✅ 帳戶餘額更新成功")
            
            # 創建LedgerEntry
            description = f"測試銷帳 - {customer['name']}"
            cursor = conn.execute("""
                INSERT INTO ledger_entries (entry_type, account_id, amount, description, entry_date, operator_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("SETTLEMENT", account['id'], test_amount, description, datetime.utcnow().isoformat(), user['id']))
            
            ledger_id = cursor.lastrowid
            print(f"✅ LedgerEntry創建成功 (ID: {ledger_id})")
            
            # 創建CashLog
            cursor = conn.execute("""
                INSERT INTO cash_logs (type, amount, time, description, operator_id)
                VALUES (?, ?, ?, ?, ?)
            """, ("SETTLEMENT", test_amount, datetime.utcnow().isoformat(), description, user['id']))
            
            cash_log_id = cursor.lastrowid
            print(f"✅ CashLog創建成功 (ID: {cash_log_id})")
            
            # 提交事務
            conn.commit()
            print("✅ 事務提交成功")
            
            # 7. 驗證結果
            print("\n🔍 驗證結果...")
            
            # 檢查客戶應收帳款
            cursor = conn.execute("SELECT total_receivables_twd FROM customers WHERE id = ?", (customer['id'],))
            actual_receivables = cursor.fetchone()['total_receivables_twd']
            expected_receivables = customer['total_receivables_twd'] - test_amount
            
            if abs(actual_receivables - expected_receivables) < 0.01:
                print(f"✅ 客戶應收帳款正確: {actual_receivables}")
            else:
                print(f"❌ 客戶應收帳款錯誤: 期望 {expected_receivables}, 實際 {actual_receivables}")
                return False
            
            # 檢查帳戶餘額
            cursor = conn.execute("SELECT balance FROM cash_accounts WHERE id = ?", (account['id'],))
            actual_balance = cursor.fetchone()['balance']
            expected_balance = account['balance'] + test_amount
            
            if abs(actual_balance - expected_balance) < 0.01:
                print(f"✅ 帳戶餘額正確: {actual_balance}")
            else:
                print(f"❌ 帳戶餘額錯誤: 期望 {expected_balance}, 實際 {actual_balance}")
                return False
            
            # 檢查LedgerEntry
            cursor = conn.execute("SELECT * FROM ledger_entries WHERE id = ?", (ledger_id,))
            ledger_entry = cursor.fetchone()
            if ledger_entry:
                print(f"✅ LedgerEntry記錄正確: {dict(ledger_entry)}")
            else:
                print("❌ LedgerEntry記錄未找到")
                return False
            
            # 檢查CashLog
            cursor = conn.execute("SELECT * FROM cash_logs WHERE id = ?", (cash_log_id,))
            cash_log = cursor.fetchone()
            if cash_log:
                print(f"✅ CashLog記錄正確: {dict(cash_log)}")
            else:
                print("❌ CashLog記錄未找到")
                return False
            
            print("\n🎉 銷帳功能測試成功！")
            return True
            
        except Exception as e:
            print(f"❌ 模擬銷帳操作失敗: {e}")
            conn.rollback()
            return False
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """主函數"""
    success = test_settlement_locally()
    
    if success:
        print("\n✅ 銷帳功能測試通過，可以部署到線上環境")
        print("💡 如果線上環境仍有問題，請使用 debug_settlement_error.py 進行詳細診斷")
    else:
        print("\n❌ 銷帳功能測試失敗，請檢查資料庫結構和數據")
        print("💡 建議使用 debug_settlement_error.py 進行詳細診斷")

if __name__ == "__main__":
    main()
