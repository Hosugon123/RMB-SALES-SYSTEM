#!/usr/bin/env python3
"""
銷售訂單創建診斷腳本
檢查銷售記錄是否正確創建和顯示
"""

import os
import sys
from datetime import datetime, date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def create_app():
    """創建Flask應用程式實例"""
    app = Flask(__name__)
    
    # 資料庫配置
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # 本地測試使用 SQLite
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/sales_system_v4.db"
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

def check_database_connection():
    """檢查資料庫連接"""
    print("=" * 60)
    print("1. 檢查資料庫連接")
    print("=" * 60)
    
    app = create_app()
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 檢查資料庫連接
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"[OK] 資料庫連接成功: {result}")
            
            # 檢查資料庫類型
            database_url = str(db.engine.url)
            print(f"[INFO] 資料庫類型: {database_url.split('://')[0]}")
            
            return True, db, app
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return False, None, None

def check_tables_exist(db):
    """檢查必要表格是否存在"""
    print("\n" + "=" * 60)
    print("2. 檢查必要表格")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查所有表格
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = db.session.execute(tables_query).fetchall()
            tables = [row[0] for row in result]
            
            print(f"📋 現有表格: {tables}")
            
            # 檢查關鍵表格
            required_tables = [
                'sales_records', 'customers', 'cash_accounts', 
                'ledger_entries', 'fifo_sales_allocations'
            ]
            
            missing_tables = []
            for table in required_tables:
                if table in tables:
                    print(f"✅ 表格存在: {table}")
                else:
                    print(f"❌ 表格缺失: {table}")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n⚠️ 缺少關鍵表格: {missing_tables}")
                return False
            else:
                print("\n✅ 所有關鍵表格都存在")
                return True
                
    except Exception as e:
        print(f"❌ 檢查表格時發生錯誤: {e}")
        return False

def check_sales_records(db):
    """檢查銷售記錄"""
    print("\n" + "=" * 60)
    print("3. 檢查銷售記錄")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查銷售記錄總數
            count_query = text("SELECT COUNT(*) FROM sales_records")
            total_count = db.session.execute(count_query).scalar()
            print(f"📊 銷售記錄總數: {total_count}")
            
            if total_count > 0:
                # 檢查最近的銷售記錄
                recent_query = text("""
                    SELECT id, customer_id, rmb_account_id, twd_amount, rmb_amount, 
                           exchange_rate, is_settled, created_at
                    FROM sales_records 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                
                result = db.session.execute(recent_query).fetchall()
                print(f"\n📋 最近5筆銷售記錄:")
                for row in result:
                    print(f"  ID: {row[0]}, 客戶: {row[1]}, RMB帳戶: {row[2]}, "
                          f"TWD: {row[3]}, RMB: {row[4]}, 匯率: {row[5]}, "
                          f"已結算: {row[6]}, 創建時間: {row[7]}")
                
                # 檢查未結算的銷售記錄
                unsettled_query = text("SELECT COUNT(*) FROM sales_records WHERE is_settled = false")
                unsettled_count = db.session.execute(unsettled_query).scalar()
                print(f"\n📊 未結算銷售記錄: {unsettled_count}")
                
                return True
            else:
                print("❌ 沒有找到任何銷售記錄")
                return False
                
    except Exception as e:
        print(f"❌ 檢查銷售記錄時發生錯誤: {e}")
        return False

def check_ledger_entries(db):
    """檢查記帳記錄"""
    print("\n" + "=" * 60)
    print("4. 檢查記帳記錄")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查記帳記錄總數
            count_query = text("SELECT COUNT(*) FROM ledger_entries")
            total_count = db.session.execute(count_query).scalar()
            print(f"📊 記帳記錄總數: {total_count}")
            
            if total_count > 0:
                # 檢查最近的記帳記錄
                recent_query = text("""
                    SELECT id, entry_type, account_id, amount, description, 
                           entry_date, operator_id
                    FROM ledger_entries 
                    ORDER BY entry_date DESC 
                    LIMIT 5
                """)
                
                result = db.session.execute(recent_query).fetchall()
                print(f"\n📋 最近5筆記帳記錄:")
                for row in result:
                    print(f"  ID: {row[0]}, 類型: {row[1]}, 帳戶: {row[2]}, "
                          f"金額: {row[3]}, 描述: {row[4]}, 日期: {row[5]}, "
                          f"操作員: {row[6]}")
                
                # 檢查利潤相關記錄
                profit_query = text("SELECT COUNT(*) FROM ledger_entries WHERE entry_type = 'PROFIT_EARNED'")
                profit_count = db.session.execute(profit_query).scalar()
                print(f"\n📊 利潤入庫記錄: {profit_count}")
                
                return True
            else:
                print("❌ 沒有找到任何記帳記錄")
                return False
                
    except Exception as e:
        print(f"❌ 檢查記帳記錄時發生錯誤: {e}")
        return False

def check_customers_and_accounts(db):
    """檢查客戶和帳戶"""
    print("\n" + "=" * 60)
    print("5. 檢查客戶和帳戶")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查客戶
            customer_query = text("SELECT COUNT(*) FROM customers")
            customer_count = db.session.execute(customer_query).scalar()
            print(f"📊 客戶總數: {customer_count}")
            
            if customer_count > 0:
                recent_customers = db.session.execute(text("""
                    SELECT id, name, total_receivables_twd 
                    FROM customers 
                    ORDER BY id DESC 
                    LIMIT 3
                """)).fetchall()
                
                print(f"📋 最近3個客戶:")
                for row in recent_customers:
                    print(f"  ID: {row[0]}, 姓名: {row[1]}, 應收帳款: {row[2]}")
            
            # 檢查現金帳戶
            account_query = text("SELECT COUNT(*) FROM cash_accounts")
            account_count = db.session.execute(account_query).scalar()
            print(f"\n📊 現金帳戶總數: {account_count}")
            
            if account_count > 0:
                recent_accounts = db.session.execute(text("""
                    SELECT id, account_name, account_type, balance_twd, balance_rmb
                    FROM cash_accounts 
                    ORDER BY id DESC 
                    LIMIT 3
                """)).fetchall()
                
                print(f"📋 最近3個帳戶:")
                for row in recent_accounts:
                    print(f"  ID: {row[0]}, 名稱: {row[1]}, 類型: {row[2]}, "
                          f"TWD餘額: {row[3]}, RMB餘額: {row[4]}")
            
            return True
            
    except Exception as e:
        print(f"❌ 檢查客戶和帳戶時發生錯誤: {e}")
        return False

def check_fifo_allocations(db):
    """檢查FIFO分配記錄"""
    print("\n" + "=" * 60)
    print("6. 檢查FIFO分配記錄")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查FIFO分配記錄總數
            count_query = text("SELECT COUNT(*) FROM fifo_sales_allocations")
            total_count = db.session.execute(count_query).scalar()
            print(f"📊 FIFO分配記錄總數: {total_count}")
            
            if total_count > 0:
                # 檢查最近的FIFO分配記錄
                recent_query = text("""
                    SELECT id, sales_record_id, fifo_inventory_id, allocated_quantity, 
                           allocated_cost_twd, allocated_profit_twd
                    FROM fifo_sales_allocations 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                
                result = db.session.execute(recent_query).fetchall()
                print(f"\n📋 最近5筆FIFO分配記錄:")
                for row in result:
                    print(f"  ID: {row[0]}, 銷售記錄: {row[1]}, 庫存: {row[2]}, "
                          f"分配數量: {row[3]}, 分配成本: {row[4]}, 分配利潤: {row[5]}")
                
                return True
            else:
                print("❌ 沒有找到任何FIFO分配記錄")
                return False
                
    except Exception as e:
        print(f"❌ 檢查FIFO分配記錄時發生錯誤: {e}")
        return False

def test_sales_creation_api(db):
    """測試銷售創建API"""
    print("\n" + "=" * 60)
    print("7. 測試銷售創建API")
    print("=" * 60)
    
    try:
        with db.app.app_context():
            # 檢查是否有可用的客戶和帳戶
            customer_query = text("SELECT id, name FROM customers LIMIT 1")
            customer_result = db.session.execute(customer_query).fetchone()
            
            account_query = text("SELECT id, account_name FROM cash_accounts WHERE account_type = 'RMB' LIMIT 1")
            account_result = db.session.execute(account_query).fetchone()
            
            if not customer_result:
                print("❌ 沒有可用的客戶")
                return False
            
            if not account_result:
                print("❌ 沒有可用的RMB帳戶")
                return False
            
            print(f"✅ 找到測試客戶: ID={customer_result[0]}, 姓名={customer_result[1]}")
            print(f"✅ 找到測試帳戶: ID={account_result[0]}, 名稱={account_result[1]}")
            
            # 記錄創建前的狀態
            before_count = db.session.execute(text("SELECT COUNT(*) FROM sales_records")).scalar()
            print(f"📊 創建前銷售記錄數: {before_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ 測試銷售創建API時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("銷售訂單創建診斷腳本")
    print("=" * 60)
    
    # 1. 檢查資料庫連接
    success, db, app = check_database_connection()
    if not success:
        print("\n❌ 診斷失敗：無法連接到資料庫")
        return False
    
    # 2. 檢查必要表格
    if not check_tables_exist(db):
        print("\n❌ 診斷失敗：缺少必要表格")
        return False
    
    # 3. 檢查銷售記錄
    sales_exist = check_sales_records(db)
    
    # 4. 檢查記帳記錄
    ledger_exist = check_ledger_entries(db)
    
    # 5. 檢查客戶和帳戶
    check_customers_and_accounts(db)
    
    # 6. 檢查FIFO分配記錄
    check_fifo_allocations(db)
    
    # 7. 測試銷售創建API
    test_sales_creation_api(db)
    
    # 總結
    print("\n" + "=" * 60)
    print("診斷總結")
    print("=" * 60)
    
    if sales_exist:
        print("✅ 銷售記錄存在 - 問題可能在於前端顯示")
        print("   建議檢查:")
        print("   1. 現金管理頁面的API調用")
        print("   2. 前端JavaScript的數據處理")
        print("   3. 瀏覽器控制台的錯誤信息")
    else:
        print("❌ 銷售記錄不存在 - 問題在於後端創建")
        print("   建議檢查:")
        print("   1. api_sales_entry 函數的執行")
        print("   2. 資料庫事務是否正確提交")
        print("   3. 錯誤處理和日誌記錄")
    
    if ledger_exist:
        print("✅ 記帳記錄存在")
    else:
        print("❌ 記帳記錄不存在")
    
    print("\n🔧 下一步建議:")
    print("1. 檢查瀏覽器開發者工具的Network標籤")
    print("2. 查看後端日誌中的錯誤信息")
    print("3. 測試手動創建銷售記錄")
    print("4. 檢查資料庫事務隔離級別")
    
    return True

if __name__ == "__main__":
    main()