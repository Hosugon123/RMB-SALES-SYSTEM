#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修復銷帳功能 500 錯誤
解決線上部署的銷帳 API 內部伺服器錯誤問題
"""

import os
import sys
import sqlite3
from datetime import datetime

def connect_database():
    """連接資料庫"""
    # 嘗試多個可能的資料庫路徑
    possible_paths = [
        'instance/sales_system.db',
        'instance/sales_system_v4.db',
        'sales_system.db',
        'instance/database.db'
    ]
    
    for db_path in possible_paths:
        if os.path.exists(db_path):
            print(f"✅ 找到資料庫: {db_path}")
            return sqlite3.connect(db_path)
    
    print("❌ 找不到資料庫檔案")
    return None

def check_database_tables(conn):
    """檢查資料庫表格結構"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查資料庫表格...")
    
    # 檢查必要的表格
    required_tables = [
        'customers',
        'cash_accounts', 
        'ledger_entries',
        'cash_logs',
        'users'
    ]
    
    missing_tables = []
    
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        if not cursor.fetchone():
            missing_tables.append(table)
            print(f"❌ 缺少表格: {table}")
        else:
            print(f"✅ 表格存在: {table}")
    
    return missing_tables

def check_ledger_entries_structure(conn):
    """檢查 ledger_entries 表格結構"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查 ledger_entries 表格結構...")
    
    try:
        cursor.execute("PRAGMA table_info(ledger_entries);")
        columns = cursor.fetchall()
        
        required_columns = [
            'id', 'entry_type', 'account_id', 'amount', 
            'description', 'entry_date', 'operator_id'
        ]
        
        existing_columns = [col[1] for col in columns]
        
        print("現有欄位:", existing_columns)
        
        missing_columns = []
        for col in required_columns:
            if col not in existing_columns:
                missing_columns.append(col)
                print(f"❌ 缺少欄位: {col}")
            else:
                print(f"✅ 欄位存在: {col}")
        
        return missing_columns
        
    except Exception as e:
        print(f"❌ 檢查表格結構失敗: {e}")
        return ['table_not_found']

def fix_ledger_entries_table(conn, missing_columns):
    """修復 ledger_entries 表格"""
    cursor = conn.cursor()
    
    print("\n🔧 修復 ledger_entries 表格...")
    
    try:
        # 如果表格不存在，創建表格
        if 'table_not_found' in missing_columns:
            print("創建 ledger_entries 表格...")
            cursor.execute("""
                CREATE TABLE ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type VARCHAR(50) NOT NULL,
                    account_id INTEGER,
                    amount FLOAT NOT NULL DEFAULT 0,
                    description VARCHAR(200),
                    entry_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operator_id INTEGER NOT NULL,
                    profit_before FLOAT,
                    profit_after FLOAT,
                    profit_change FLOAT,
                    from_account_id INTEGER,
                    to_account_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES cash_accounts(id),
                    FOREIGN KEY (operator_id) REFERENCES user(id),
                    FOREIGN KEY (from_account_id) REFERENCES cash_accounts(id),
                    FOREIGN KEY (to_account_id) REFERENCES cash_accounts(id)
                );
            """)
            print("✅ ledger_entries 表格創建成功")
        
        # 添加缺失的欄位
        for column in missing_columns:
            if column == 'table_not_found':
                continue
                
            print(f"添加欄位: {column}")
            
            if column == 'profit_before':
                cursor.execute("ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT;")
            elif column == 'profit_after':
                cursor.execute("ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT;")
            elif column == 'profit_change':
                cursor.execute("ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT;")
            elif column == 'from_account_id':
                cursor.execute("ALTER TABLE ledger_entries ADD COLUMN from_account_id INTEGER;")
            elif column == 'to_account_id':
                cursor.execute("ALTER TABLE ledger_entries ADD COLUMN to_account_id INTEGER;")
        
        conn.commit()
        print("✅ ledger_entries 表格修復完成")
        return True
        
    except Exception as e:
        print(f"❌ 修復表格失敗: {e}")
        conn.rollback()
        return False

def check_cash_logs_table(conn):
    """檢查 cash_logs 表格"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查 cash_logs 表格...")
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cash_logs';")
        if not cursor.fetchone():
            print("❌ cash_logs 表格不存在，創建表格...")
            cursor.execute("""
                CREATE TABLE cash_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(50),
                    description VARCHAR(200),
                    amount FLOAT,
                    operator_id INTEGER NOT NULL,
                    FOREIGN KEY (operator_id) REFERENCES user(id)
                );
            """)
            conn.commit()
            print("✅ cash_logs 表格創建成功")
        else:
            print("✅ cash_logs 表格存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查 cash_logs 表格失敗: {e}")
        return False

def check_sample_data(conn):
    """檢查範例資料"""
    cursor = conn.cursor()
    
    print("\n📊 檢查範例資料...")
    
    try:
        # 檢查客戶資料
        cursor.execute("SELECT COUNT(*) FROM customers;")
        customer_count = cursor.fetchone()[0]
        print(f"客戶數量: {customer_count}")
        
        # 檢查現金帳戶
        cursor.execute("SELECT COUNT(*) FROM cash_accounts;")
        account_count = cursor.fetchone()[0]
        print(f"現金帳戶數量: {account_count}")
        
        # 檢查用戶
        cursor.execute("SELECT COUNT(*) FROM user;")
        user_count = cursor.fetchone()[0]
        print(f"用戶數量: {user_count}")
        
        if customer_count == 0 or account_count == 0 or user_count == 0:
            print("⚠️ 資料庫可能已被清空，需要重新初始化資料")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查範例資料失敗: {e}")
        return False

def create_sample_data(conn):
    """創建範例資料"""
    cursor = conn.cursor()
    
    print("\n🔧 創建範例資料...")
    
    try:
        # 創建管理員用戶
        cursor.execute("""
            INSERT OR IGNORE INTO user (id, username, password_hash, is_admin) 
            VALUES (1, 'admin', 'pbkdf2:sha256:600000$admin$hash', 1);
        """)
        
        # 創建範例客戶
        cursor.execute("""
            INSERT OR IGNORE INTO customers (id, name, total_receivables_twd) 
            VALUES (1, '測試客戶', 1000.00);
        """)
        
        # 創建範例現金帳戶
        cursor.execute("""
            INSERT OR IGNORE INTO cash_accounts (id, name, balance, currency, is_active, holder_id) 
            VALUES (1, '台幣帳戶', 5000.00, 'TWD', 1, 1);
        """)
        
        conn.commit()
        print("✅ 範例資料創建成功")
        return True
        
    except Exception as e:
        print(f"❌ 創建範例資料失敗: {e}")
        conn.rollback()
        return False

def main():
    """主函數"""
    print("🚀 開始修復銷帳功能錯誤...")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 連接資料庫
    conn = connect_database()
    if not conn:
        print("❌ 無法連接資料庫，修復失敗")
        return False
    
    try:
        # 檢查資料庫表格
        missing_tables = check_database_tables(conn)
        if missing_tables:
            print(f"❌ 缺少必要表格: {missing_tables}")
            print("請先運行資料庫遷移或初始化腳本")
            return False
        
        # 檢查 ledger_entries 表格結構
        missing_columns = check_ledger_entries_structure(conn)
        
        # 修復 ledger_entries 表格
        if missing_columns:
            if not fix_ledger_entries_table(conn, missing_columns):
                print("❌ 修復 ledger_entries 表格失敗")
                return False
        
        # 檢查 cash_logs 表格
        if not check_cash_logs_table(conn):
            print("❌ 修復 cash_logs 表格失敗")
            return False
        
        # 檢查範例資料
        if not check_sample_data(conn):
            print("⚠️ 資料庫可能已被清空，創建範例資料...")
            if not create_sample_data(conn):
                print("❌ 創建範例資料失敗")
                return False
        
        print("\n✅ 銷帳功能修復完成！")
        print("現在可以重新測試銷帳功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 修復成功！")
        print("建議重新部署應用程式以確保修復生效")
    else:
        print("\n💥 修復失敗，請檢查錯誤信息")
    
    sys.exit(0 if success else 1)
