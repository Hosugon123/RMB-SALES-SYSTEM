#!/usr/bin/env python3
"""
簡化版銷售訂單創建診斷腳本
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

def main():
    """主函數"""
    print("銷售訂單創建診斷腳本")
    print("=" * 50)
    
    app = create_app()
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 1. 檢查資料庫連接
            print("1. 檢查資料庫連接...")
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"   [OK] 資料庫連接成功: {result}")
            
            # 2. 檢查銷售記錄
            print("\n2. 檢查銷售記錄...")
            count_query = text("SELECT COUNT(*) FROM sales_records")
            sales_count = db.session.execute(count_query).scalar()
            print(f"   [INFO] 銷售記錄總數: {sales_count}")
            
            if sales_count > 0:
                # 檢查最近的銷售記錄
                recent_query = text("""
                    SELECT id, customer_id, rmb_account_id, twd_amount, rmb_amount, 
                           exchange_rate, is_settled, created_at
                    FROM sales_records 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """)
                
                result = db.session.execute(recent_query).fetchall()
                print(f"   [INFO] 最近3筆銷售記錄:")
                for row in result:
                    print(f"     ID: {row[0]}, 客戶: {row[1]}, RMB帳戶: {row[2]}, "
                          f"TWD: {row[3]}, RMB: {row[4]}, 已結算: {row[6]}")
            else:
                print("   [ERROR] 沒有找到任何銷售記錄")
            
            # 3. 檢查記帳記錄
            print("\n3. 檢查記帳記錄...")
            ledger_count = db.session.execute(text("SELECT COUNT(*) FROM ledger_entries")).scalar()
            print(f"   [INFO] 記帳記錄總數: {ledger_count}")
            
            if ledger_count > 0:
                # 檢查利潤相關記錄
                profit_count = db.session.execute(text("SELECT COUNT(*) FROM ledger_entries WHERE entry_type = 'PROFIT_EARNED'")).scalar()
                print(f"   [INFO] 利潤入庫記錄: {profit_count}")
            
            # 4. 檢查客戶和帳戶
            print("\n4. 檢查客戶和帳戶...")
            customer_count = db.session.execute(text("SELECT COUNT(*) FROM customers")).scalar()
            account_count = db.session.execute(text("SELECT COUNT(*) FROM cash_accounts")).scalar()
            print(f"   [INFO] 客戶總數: {customer_count}")
            print(f"   [INFO] 現金帳戶總數: {account_count}")
            
            # 5. 檢查FIFO分配記錄
            print("\n5. 檢查FIFO分配記錄...")
            fifo_count = db.session.execute(text("SELECT COUNT(*) FROM fifo_sales_allocations")).scalar()
            print(f"   [INFO] FIFO分配記錄總數: {fifo_count}")
            
            # 6. 檢查表格結構
            print("\n6. 檢查表格結構...")
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = db.session.execute(tables_query).fetchall()
            tables = [row[0] for row in result]
            print(f"   [INFO] 現有表格: {tables}")
            
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
            
    except Exception as e:
        print(f"[ERROR] 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
