#!/usr/bin/env python3
"""
PostgreSQL 欄位檢查腳本 - Render 部署優化版
專門用於檢查線上環境欄位是否存在，避免與 Alembic migration 衝突
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

def fix_ledger_entries_columns():
    """檢查ledger_entries表格欄位是否存在"""
    print("🔍 檢查ledger_entries表格欄位...")
    
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
            
            print(f"✅ 檢測到PostgreSQL資料庫")
            
            # 檢查現有欄位
            columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ledger_entries' 
                AND table_schema = 'public'
                ORDER BY column_name
            """)
            
            result = db.session.execute(columns_query).fetchall()
            existing_columns = {row[0]: row[1] for row in result}
            
            print(f"📋 現有欄位: {list(existing_columns.keys())}")
            
            # 需要檢查的欄位
            required_columns = [
                'from_account_id',
                'to_account_id', 
                'profit_before',
                'profit_after',
                'profit_change'
            ]
            
            # 檢查缺少的欄位
            missing_columns = []
            for column_name in required_columns:
                if column_name not in existing_columns:
                    missing_columns.append(column_name)
                    print(f"❌ 缺少欄位: {column_name}")
                else:
                    print(f"✅ 欄位存在: {column_name}")
            
            if missing_columns:
                print(f"⚠️ 發現 {len(missing_columns)} 個缺少的欄位: {missing_columns}")
                print("請確保 Alembic migration 已正確執行")
                return False
            else:
                print("✅ 所有必要欄位都存在")
                return True
                
    except Exception as e:
        print(f"❌ 檢查欄位時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ledger_entry_creation():
    """測試LedgerEntry創建"""
    print("\n🧪 測試LedgerEntry創建...")
    
    app = create_app()
    if not app:
        return False
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 動態查詢現有的 cash_accounts.id
            account_query = text("SELECT id FROM cash_accounts LIMIT 1")
            account_result = db.session.execute(account_query).fetchone()
            
            if not account_result:
                print("⚠️ 沒有找到現有的 cash_accounts 記錄，跳過測試")
                return True
            
            account_id = account_result[0]
            print(f"✅ 找到現有帳戶 ID: {account_id}")
            
            # 動態查詢現有的 user.id (operator_id)
            user_query = text("SELECT id FROM \"user\" LIMIT 1")
            user_result = db.session.execute(user_query).fetchone()
            
            if not user_result:
                print("⚠️ 沒有找到現有的 user 記錄，跳過測試")
                return True
            
            operator_id = user_result[0]
            print(f"✅ 找到現有用戶 ID: {operator_id}")
            
            # 測試插入LedgerEntry
            test_query = text("""
                INSERT INTO ledger_entries (
                    entry_type, account_id, amount, description, entry_date, operator_id,
                    from_account_id, to_account_id, profit_before, profit_after, profit_change
                ) VALUES (
                    :entry_type, :account_id, :amount, :description, :entry_date, :operator_id,
                    :from_account_id, :to_account_id, :profit_before, :profit_after, :profit_change
                ) RETURNING id
            """)
            
            result = db.session.execute(test_query, {
                'entry_type': 'TEST',
                'account_id': account_id,
                'amount': 0.01,
                'description': '欄位修復測試',
                'entry_date': '2024-01-01 12:00:00',
                'operator_id': operator_id,
                'from_account_id': None,
                'to_account_id': None,
                'profit_before': None,
                'profit_after': None,
                'profit_change': None
            })
            
            test_id = result.scalar()
            print(f"✅ 測試記錄創建成功 (ID: {test_id})")
            
            # 清理測試記錄
            cleanup_query = text("DELETE FROM ledger_entries WHERE id = :id")
            db.session.execute(cleanup_query, {'id': test_id})
            db.session.commit()
            print("✅ 測試記錄已清理")
            
            return True
            
    except Exception as e:
        print(f"❌ 測試LedgerEntry創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("PostgreSQL 欄位檢查腳本")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.environ.get('DATABASE_URL'):
        print("❌ 未設置 DATABASE_URL 環境變數")
        print("請在Render環境中設置DATABASE_URL")
        return False
    
    # 檢查欄位
    if not fix_ledger_entries_columns():
        print("❌ 欄位檢查失敗")
        return False
    
    # 測試功能
    if not test_ledger_entry_creation():
        print("❌ 測試失敗")
        return False
    
    print("\n🎉 PostgreSQL欄位檢查完成！")
    print("✅ ledger_entries表格欄位檢查通過")
    print("✅ 銷帳功能應該可以正常工作")
    print("✅ 可以繼續部署應用程式")
    
    return True

if __name__ == "__main__":
    main()
