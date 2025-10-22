#!/usr/bin/env python3
"""
銷帳錯誤簡化調試工具 (避免Unicode問題)
"""

import sqlite3
import os
import sys
import json
from datetime import datetime
import traceback

def connect_to_database():
    """連接到資料庫"""
    possible_paths = [
        "./instance/sales_system.db",
        "./instance/sales_system_v4.db", 
        "./instance/sales_system_backup.db"
    ]
    
    for db_path in possible_paths:
        if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            print(f"找到資料庫文件: {db_path} (大小: {os.path.getsize(db_path)} bytes)")
            break
    else:
        print("找不到有效的資料庫文件")
        print(f"檢查的路徑: {possible_paths}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print(f"成功連接到資料庫: {db_path}")
        return conn
    except Exception as e:
        print(f"連接資料庫失敗: {e}")
        return None

def check_database_schema(conn):
    """檢查資料庫結構"""
    print("\n檢查資料庫結構...")
    
    tables = ['customers', 'cash_accounts', 'ledger_entries', 'cash_logs', 'users']
    
    for table in tables:
        try:
            cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"表格 {table} 存在")
            else:
                print(f"表格 {table} 不存在")
        except Exception as e:
            print(f"檢查表格 {table} 時出錯: {e}")
    
    # 檢查ledger_entries的欄位
    try:
        cursor = conn.execute("PRAGMA table_info(ledger_entries)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"ledger_entries 欄位: {columns}")
        
        required_columns = ['id', 'entry_type', 'account_id', 'amount', 'description', 'entry_date', 'operator_id']
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"缺少必要欄位: {missing_columns}")
        else:
            print("ledger_entries 結構正常")
    except Exception as e:
        print(f"檢查ledger_entries結構時出錯: {e}")

def get_customers(conn):
    """獲取客戶列表"""
    try:
        cursor = conn.execute("""
            SELECT id, name, total_receivables_twd 
            FROM customers 
            WHERE total_receivables_twd > 0
            ORDER BY total_receivables_twd DESC
        """)
        customers = cursor.fetchall()
        return customers
    except Exception as e:
        print(f"獲取客戶列表失敗: {e}")
        return []

def get_cash_accounts(conn):
    """獲取現金帳戶列表"""
    try:
        cursor = conn.execute("""
            SELECT ca.id, ca.name, ca.balance, ca.currency, ca.is_active, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'TWD' AND ca.is_active = 1
            ORDER BY ca.name
        """)
        accounts = cursor.fetchall()
        return accounts
    except Exception as e:
        print(f"獲取現金帳戶列表失敗: {e}")
        return []

def get_users(conn):
    """獲取用戶列表"""
    try:
        cursor = conn.execute("SELECT id, username FROM user ORDER BY id")
        users = cursor.fetchall()
        return users
    except Exception as e:
        print(f"獲取用戶列表失敗: {e}")
        return []

def simulate_settlement(conn, customer_id, amount, account_id, note, operator_id):
    """模擬銷帳操作"""
    print(f"\n模擬銷帳操作...")
    print(f"   客戶ID: {customer_id}")
    print(f"   銷帳金額: {amount}")
    print(f"   帳戶ID: {account_id}")
    print(f"   備註: {note}")
    print(f"   操作員ID: {operator_id}")
    
    try:
        # 開始事務
        conn.execute("BEGIN TRANSACTION")
        
        # 1. 檢查客戶
        print("\n1. 檢查客戶...")
        cursor = conn.execute("SELECT id, name, total_receivables_twd FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            print("找不到指定的客戶")
            return False, "找不到指定的客戶"
        
        print(f"客戶: {customer['name']}, 應收帳款: {customer['total_receivables_twd']}")
        
        if amount > customer['total_receivables_twd']:
            error_msg = f"銷帳金額超過應收帳款！客戶應收 {customer['total_receivables_twd']:,.2f}，但銷帳 {amount:,.2f}"
            print(f"錯誤: {error_msg}")
            return False, error_msg
        
        # 2. 檢查帳戶
        print("\n2. 檢查帳戶...")
        cursor = conn.execute("""
            SELECT ca.id, ca.name, ca.balance, ca.currency, ca.is_active, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.id = ?
        """, (account_id,))
        account = cursor.fetchone()
        
        if not account:
            error_msg = f"找不到帳戶 ID {account_id}，該帳戶可能已被刪除"
            print(f"錯誤: {error_msg}")
            return False, error_msg
        
        print(f"帳戶: {account['name']} ({account['holder_name']}), 餘額: {account['balance']}, 幣種: {account['currency']}, 狀態: {'啟用' if account['is_active'] else '停用'}")
        
        if not account['is_active']:
            error_msg = f"帳戶「{account['name']}」已停用，無法使用"
            print(f"錯誤: {error_msg}")
            return False, error_msg
        
        if account['currency'] != "TWD":
            error_msg = f"帳戶「{account['name']}」的幣種是 {account['currency']}，不是台幣帳戶"
            print(f"錯誤: {error_msg}")
            return False, error_msg
        
        # 3. 檢查操作員
        print("\n3. 檢查操作員...")
        cursor = conn.execute("SELECT id, username FROM user WHERE id = ?", (operator_id,))
        operator = cursor.fetchone()
        
        if not operator:
            error_msg = f"找不到操作員 ID {operator_id}"
            print(f"錯誤: {error_msg}")
            return False, error_msg
        
        print(f"操作員: {operator['username']}")
        
        # 4. 模擬更新客戶應收帳款
        print("\n4. 更新客戶應收帳款...")
        new_receivables = customer['total_receivables_twd'] - amount
        print(f"   原應收帳款: {customer['total_receivables_twd']:,.2f}")
        print(f"   銷帳金額: {amount:,.2f}")
        print(f"   新應收帳款: {new_receivables:,.2f}")
        
        # 5. 模擬更新帳戶餘額
        print("\n5. 更新帳戶餘額...")
        new_balance = account['balance'] + amount
        print(f"   原帳戶餘額: {account['balance']:,.2f}")
        print(f"   增加金額: {amount:,.2f}")
        print(f"   新帳戶餘額: {new_balance:,.2f}")
        
        # 6. 檢查LedgerEntry創建
        print("\n6. 檢查LedgerEntry創建...")
        try:
            # 檢查欄位是否存在
            cursor = conn.execute("PRAGMA table_info(ledger_entries)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"   ledger_entries 欄位: {columns}")
            
            required_columns = ['id', 'entry_type', 'account_id', 'amount', 'description', 'entry_date', 'operator_id']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"缺少必要欄位: {missing_columns}")
                return False, f"LedgerEntry表格缺少必要欄位: {missing_columns}"
            
            print("LedgerEntry結構檢查通過")
            
        except Exception as e:
            print(f"檢查LedgerEntry結構時出錯: {e}")
            return False, f"檢查LedgerEntry結構時出錯: {e}"
        
        # 7. 檢查CashLog創建
        print("\n7. 檢查CashLog創建...")
        try:
            cursor = conn.execute("PRAGMA table_info(cash_logs)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"   cash_logs 欄位: {columns}")
            
            required_columns = ['id', 'time', 'type', 'description', 'amount', 'operator_id']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"缺少必要欄位: {missing_columns}")
                return False, f"CashLog表格缺少必要欄位: {missing_columns}"
            
            print("CashLog結構檢查通過")
            
        except Exception as e:
            print(f"檢查CashLog結構時出錯: {e}")
            return False, f"檢查CashLog結構時出錯: {e}"
        
        # 8. 模擬實際創建記錄
        print("\n8. 模擬創建記錄...")
        
        # 創建LedgerEntry
        try:
            description = f"客戶「{customer['name']}」銷帳收款 - {note}" if note else f"客戶「{customer['name']}」銷帳收款"
            cursor = conn.execute("""
                INSERT INTO ledger_entries (entry_type, account_id, amount, description, entry_date, operator_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("SETTLEMENT", account_id, amount, description, datetime.utcnow().isoformat(), operator_id))
            
            ledger_id = cursor.lastrowid
            print(f"LedgerEntry創建成功，ID: {ledger_id}")
            
        except Exception as e:
            print(f"創建LedgerEntry失敗: {e}")
            print(f"   錯誤詳情: {traceback.format_exc()}")
            return False, f"創建LedgerEntry失敗: {e}"
        
        # 創建CashLog
        try:
            description = f"客戶「{customer['name']}」銷帳收款 - {note}" if note else f"客戶「{customer['name']}」銷帳收款"
            cursor = conn.execute("""
                INSERT INTO cash_logs (type, amount, time, description, operator_id)
                VALUES (?, ?, ?, ?, ?)
            """, ("SETTLEMENT", amount, datetime.utcnow().isoformat(), description, operator_id))
            
            cash_log_id = cursor.lastrowid
            print(f"CashLog創建成功，ID: {cash_log_id}")
            
        except Exception as e:
            print(f"創建CashLog失敗: {e}")
            print(f"   錯誤詳情: {traceback.format_exc()}")
            return False, f"創建CashLog失敗: {e}"
        
        # 9. 模擬更新客戶和帳戶
        print("\n9. 模擬更新客戶和帳戶...")
        
        try:
            # 更新客戶應收帳款
            conn.execute("UPDATE customers SET total_receivables_twd = ? WHERE id = ?", (new_receivables, customer_id))
            print("客戶應收帳款更新成功")
            
            # 更新帳戶餘額
            conn.execute("UPDATE cash_accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
            print("帳戶餘額更新成功")
            
        except Exception as e:
            print(f"更新客戶或帳戶失敗: {e}")
            print(f"   錯誤詳情: {traceback.format_exc()}")
            return False, f"更新客戶或帳戶失敗: {e}"
        
        # 10. 提交事務
        print("\n10. 提交事務...")
        try:
            conn.commit()
            print("事務提交成功")
            return True, "銷帳操作模擬成功"
            
        except Exception as e:
            print(f"提交事務失敗: {e}")
            print(f"   錯誤詳情: {traceback.format_exc()}")
            conn.rollback()
            return False, f"提交事務失敗: {e}"
        
    except Exception as e:
        print(f"模擬銷帳操作時發生未預期錯誤: {e}")
        print(f"   錯誤詳情: {traceback.format_exc()}")
        conn.rollback()
        return False, f"模擬銷帳操作時發生未預期錯誤: {e}"

def main():
    """主函數"""
    print("銷帳錯誤本地調試工具")
    print("=" * 50)
    
    # 連接資料庫
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # 檢查資料庫結構
        check_database_schema(conn)
        
        # 獲取客戶列表
        print("\n可用的客戶（有應收帳款的）:")
        customers = get_customers(conn)
        if not customers:
            print("沒有找到有應收帳款的客戶")
            return
        
        for i, customer in enumerate(customers, 1):
            print(f"   {i}. ID: {customer['id']}, 名稱: {customer['name']}, 應收帳款: NT$ {customer['total_receivables_twd']:,.2f}")
        
        # 獲取帳戶列表
        print("\n可用的台幣帳戶:")
        accounts = get_cash_accounts(conn)
        if not accounts:
            print("沒有找到可用的台幣帳戶")
            return
        
        for i, account in enumerate(accounts, 1):
            print(f"   {i}. ID: {account['id']}, 名稱: {account['name']} ({account['holder_name']}), 餘額: NT$ {account['balance']:,.2f}")
        
        # 獲取用戶列表
        print("\n可用的操作員:")
        users = get_users(conn)
        if not users:
            print("沒有找到可用的操作員")
            return
        
        for i, user in enumerate(users, 1):
            print(f"   {i}. ID: {user['id']}, 用戶名: {user['username']}")
        
        # 獲取用戶輸入
        print("\n" + "=" * 50)
        print("請輸入銷帳參數:")
        
        try:
            customer_id = int(input("客戶ID: "))
            amount = float(input("銷帳金額: "))
            account_id = int(input("帳戶ID: "))
            note = input("備註 (可選): ").strip()
            operator_id = int(input("操作員ID: "))
        except ValueError as e:
            print(f"輸入格式錯誤: {e}")
            return
        
        # 執行模擬
        success, message = simulate_settlement(conn, customer_id, amount, account_id, note, operator_id)
        
        print("\n" + "=" * 50)
        if success:
            print("模擬結果: 成功")
            print(f"   消息: {message}")
        else:
            print("模擬結果: 失敗")
            print(f"   錯誤: {message}")
        
        print("\n調試建議:")
        if not success:
            if "找不到指定的客戶" in message:
                print("   - 檢查客戶ID是否正確")
                print("   - 確認客戶存在且有應收帳款")
            elif "找不到帳戶" in message:
                print("   - 檢查帳戶ID是否正確")
                print("   - 確認帳戶存在且為台幣帳戶")
            elif "銷帳金額超過應收帳款" in message:
                print("   - 檢查銷帳金額是否超過客戶應收帳款")
            elif "缺少必要欄位" in message:
                print("   - 檢查資料庫結構是否完整")
                print("   - 可能需要執行資料庫遷移")
            elif "創建" in message and "失敗" in message:
                print("   - 檢查資料庫權限")
                print("   - 檢查表格結構是否正確")
            else:
                print("   - 查看詳細錯誤信息")
                print("   - 檢查資料庫連接和權限")
        else:
            print("   - 銷帳邏輯正常，問題可能在於:")
            print("   - 線上環境的資料庫結構不同")
            print("   - 線上環境的權限問題")
            print("   - 線上環境的依賴項問題")
    
    finally:
        conn.close()
        print("\n調試完成")

if __name__ == "__main__":
    main()
