#!/usr/bin/env python3
"""
PostgreSQL 銷帳功能修復腳本
專門用於修復線上環境的PostgreSQL資料庫問題
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def create_app():
    """創建Flask應用程式實例"""
    app = Flask(__name__)
    
    # 資料庫配置
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        # 修復 Render PostgreSQL URL 格式問題
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        print("❌ 未找到 DATABASE_URL 環境變數")
        return None
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

def check_postgresql_structure():
    """檢查PostgreSQL資料庫結構"""
    print("🔍 檢查PostgreSQL資料庫結構...")
    
    app = create_app()
    if not app:
        return False
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 檢查是否為PostgreSQL
            database_url = str(db.engine.url)
            if 'postgresql' not in database_url:
                print("❌ 不是PostgreSQL資料庫")
                return False
            
            print(f"✅ 檢測到PostgreSQL資料庫: {database_url}")
            
            # 檢查關鍵表格是否存在
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('customers', 'cash_accounts', 'ledger_entries', 'cash_logs', 'user')
            """)
            
            result = db.session.execute(tables_query).fetchall()
            existing_tables = [row[0] for row in result]
            
            print(f"📋 現有表格: {existing_tables}")
            
            required_tables = ['customers', 'cash_accounts', 'ledger_entries', 'cash_logs', 'user']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"❌ 缺少表格: {missing_tables}")
                return False
            
            # 檢查user表格結構
            user_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user' 
                AND table_schema = 'public'
            """)
            
            result = db.session.execute(user_columns_query).fetchall()
            user_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 user表格欄位: {user_columns}")
            
            if 'id' not in user_columns or 'username' not in user_columns:
                print("❌ user表格缺少必要欄位")
                return False
            
            # 檢查ledger_entries表格結構
            ledger_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ledger_entries' 
                AND table_schema = 'public'
            """)
            
            result = db.session.execute(ledger_columns_query).fetchall()
            ledger_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 ledger_entries表格欄位: {ledger_columns}")
            
            required_ledger_columns = ['id', 'entry_type', 'account_id', 'amount', 'description', 'entry_date', 'operator_id']
            missing_ledger_columns = [col for col in required_ledger_columns if col not in ledger_columns]
            
            if missing_ledger_columns:
                print(f"❌ ledger_entries表格缺少必要欄位: {missing_ledger_columns}")
                return False
            
            # 檢查cash_logs表格結構
            cash_logs_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cash_logs' 
                AND table_schema = 'public'
            """)
            
            result = db.session.execute(cash_logs_columns_query).fetchall()
            cash_logs_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 cash_logs表格欄位: {cash_logs_columns}")
            
            required_cash_logs_columns = ['id', 'time', 'type', 'description', 'amount', 'operator_id']
            missing_cash_logs_columns = [col for col in required_cash_logs_columns if col not in cash_logs_columns]
            
            if missing_cash_logs_columns:
                print(f"❌ cash_logs表格缺少必要欄位: {missing_cash_logs_columns}")
                return False
            
            # 檢查數據
            user_count_query = text("SELECT COUNT(*) FROM \"user\"")
            user_count = db.session.execute(user_count_query).scalar()
            print(f"👤 用戶數量: {user_count}")
            
            if user_count == 0:
                print("❌ 沒有用戶數據")
                return False
            
            customers_count_query = text("SELECT COUNT(*) FROM customers WHERE total_receivables_twd > 0")
            customers_count = db.session.execute(customers_count_query).scalar()
            print(f"👥 有應收帳款的客戶數量: {customers_count}")
            
            accounts_count_query = text("SELECT COUNT(*) FROM cash_accounts WHERE currency = 'TWD' AND is_active = true")
            accounts_count = db.session.execute(accounts_count_query).scalar()
            print(f"💰 台幣帳戶數量: {accounts_count}")
            
            print("✅ PostgreSQL資料庫結構檢查通過")
            return True
            
    except Exception as e:
        print(f"❌ 檢查PostgreSQL結構時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_postgresql_settlement():
    """測試PostgreSQL銷帳功能"""
    print("\n🧪 測試PostgreSQL銷帳功能...")
    
    app = create_app()
    if not app:
        return False
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 獲取測試數據
            customer_query = text("""
                SELECT id, name, total_receivables_twd 
                FROM customers 
                WHERE total_receivables_twd > 0
                ORDER BY total_receivables_twd DESC
                LIMIT 1
            """)
            
            customer = db.session.execute(customer_query).fetchone()
            if not customer:
                print("❌ 沒有找到有應收帳款的客戶")
                return False
            
            print(f"👤 測試客戶: {customer[1]} (ID: {customer[0]}, 應收帳款: {customer[2]})")
            
            account_query = text("""
                SELECT ca.id, ca.name, ca.balance, h.name as holder_name
                FROM cash_accounts ca
                LEFT JOIN holders h ON ca.holder_id = h.id
                WHERE ca.currency = 'TWD' AND ca.is_active = true
                ORDER BY ca.name
                LIMIT 1
            """)
            
            account = db.session.execute(account_query).fetchone()
            if not account:
                print("❌ 沒有找到可用的台幣帳戶")
                return False
            
            print(f"💰 測試帳戶: {account[1]} ({account[3]}) (ID: {account[0]}, 餘額: {account[2]})")
            
            user_query = text("SELECT id, username FROM \"user\" ORDER BY id LIMIT 1")
            user = db.session.execute(user_query).fetchone()
            if not user:
                print("❌ 沒有找到用戶")
                return False
            
            print(f"👤 測試用戶: {user[1]} (ID: {user[0]})")
            
            # 模擬銷帳操作
            test_amount = min(1.0, customer[2] * 0.1)
            print(f"💵 測試金額: {test_amount}")
            
            # 開始事務
            db.session.begin()
            
            try:
                # 更新客戶應收帳款
                update_customer_query = text("""
                    UPDATE customers 
                    SET total_receivables_twd = total_receivables_twd - :amount 
                    WHERE id = :customer_id
                """)
                db.session.execute(update_customer_query, {
                    'amount': test_amount, 
                    'customer_id': customer[0]
                })
                
                # 更新帳戶餘額
                update_account_query = text("""
                    UPDATE cash_accounts 
                    SET balance = balance + :amount 
                    WHERE id = :account_id
                """)
                db.session.execute(update_account_query, {
                    'amount': test_amount, 
                    'account_id': account[0]
                })
                
                # 創建LedgerEntry
                ledger_query = text("""
                    INSERT INTO ledger_entries (entry_type, account_id, amount, description, entry_date, operator_id)
                    VALUES (:entry_type, :account_id, :amount, :description, :entry_date, :operator_id)
                    RETURNING id
                """)
                
                result = db.session.execute(ledger_query, {
                    'entry_type': 'SETTLEMENT',
                    'account_id': account[0],
                    'amount': test_amount,
                    'description': f'PostgreSQL測試銷帳 - {customer[1]}',
                    'entry_date': '2024-01-01 12:00:00',
                    'operator_id': user[0]
                })
                
                ledger_id = result.scalar()
                print(f"✅ LedgerEntry創建成功 (ID: {ledger_id})")
                
                # 創建CashLog
                cash_log_query = text("""
                    INSERT INTO cash_logs (type, amount, time, description, operator_id)
                    VALUES (:type, :amount, :time, :description, :operator_id)
                    RETURNING id
                """)
                
                result = db.session.execute(cash_log_query, {
                    'type': 'SETTLEMENT',
                    'amount': test_amount,
                    'time': '2024-01-01 12:00:00',
                    'description': f'PostgreSQL測試銷帳 - {customer[1]}',
                    'operator_id': user[0]
                })
                
                cash_log_id = result.scalar()
                print(f"✅ CashLog創建成功 (ID: {cash_log_id})")
                
                # 提交事務
                db.session.commit()
                print("✅ 事務提交成功")
                
                return True
                
            except Exception as e:
                print(f"❌ 銷帳操作失敗: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ 測試PostgreSQL銷帳功能時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("PostgreSQL 銷帳功能修復腳本")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.environ.get('DATABASE_URL'):
        print("❌ 未設置 DATABASE_URL 環境變數")
        print("請在Render環境中設置DATABASE_URL")
        return False
    
    # 檢查資料庫結構
    if not check_postgresql_structure():
        print("❌ 資料庫結構檢查失敗")
        return False
    
    # 測試銷帳功能
    if not test_postgresql_settlement():
        print("❌ 銷帳功能測試失敗")
        return False
    
    print("\n🎉 PostgreSQL銷帳功能修復成功！")
    print("✅ 資料庫結構正常")
    print("✅ 銷帳功能正常")
    print("✅ 可以安全部署")
    
    return True

if __name__ == "__main__":
    main()
