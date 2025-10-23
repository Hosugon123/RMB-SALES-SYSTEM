#!/usr/bin/env python3
"""
部署驗證腳本 - 檢查線上環境的資料庫結構
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

def check_database_structure():
    """檢查資料庫結構"""
    print("🔍 檢查資料庫結構...")
    
    app = create_app()
    if not app:
        return False
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
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
            
            # 檢查關鍵表格是否存在
            required_tables = [
                'sales_records', 'fifo_sales_allocations', 'fifo_inventory',
                'ledger_entries', 'profit_transactions', 'cash_accounts',
                'customers', 'purchase_records'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ 缺少表格: {missing_tables}")
                return False
            else:
                print("✅ 所有必要表格都存在")
            
            # 檢查 sales_records 表格結構
            sales_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sales_records' 
                AND table_schema = 'public'
                ORDER BY column_name
            """)
            
            result = db.session.execute(sales_columns_query).fetchall()
            sales_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 sales_records 欄位: {list(sales_columns.keys())}")
            
            # 檢查 ledger_entries 表格結構
            ledger_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ledger_entries' 
                AND table_schema = 'public'
                ORDER BY column_name
            """)
            
            result = db.session.execute(ledger_columns_query).fetchall()
            ledger_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 ledger_entries 欄位: {list(ledger_columns.keys())}")
            
            # 檢查是否有售出記錄
            sales_count_query = text("SELECT COUNT(*) FROM sales_records")
            sales_count = db.session.execute(sales_count_query).scalar()
            print(f"📊 售出記錄數量: {sales_count}")
            
            # 檢查是否有 FIFO 分配記錄
            fifo_count_query = text("SELECT COUNT(*) FROM fifo_sales_allocations")
            fifo_count = db.session.execute(fifo_count_query).scalar()
            print(f"📊 FIFO 分配記錄數量: {fifo_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ 檢查資料庫結構時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("部署驗證腳本")
    print("=" * 50)
    
    if check_database_structure():
        print("\n🎉 資料庫結構檢查通過！")
        return True
    else:
        print("\n❌ 資料庫結構檢查失敗！")
        return False

if __name__ == "__main__":
    main()
