#!/usr/bin/env python3
"""
PostgreSQL 欄位修復腳本 - Render 部署優化版
專門用於修復線上環境缺少的欄位
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
    """修復ledger_entries表格缺少的欄位"""
    print("🔧 修復ledger_entries表格欄位...")
    
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
            
            # 需要添加的欄位
            columns_to_add = [
                ('from_account_id', 'INTEGER'),
                ('to_account_id', 'INTEGER'),
                ('profit_before', 'REAL'),
                ('profit_after', 'REAL'),
                ('profit_change', 'REAL')
            ]
            
            added_columns = []
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        # 添加欄位
                        alter_query = text(f"""
                            ALTER TABLE ledger_entries 
                            ADD COLUMN {column_name} {column_type}
                        """)
                        db.session.execute(alter_query)
                        db.session.commit()
                        added_columns.append(column_name)
                        print(f"✅ 添加欄位: {column_name} ({column_type})")
                    except Exception as e:
                        print(f"❌ 添加欄位 {column_name} 失敗: {e}")
                        db.session.rollback()
                else:
                    print(f"ℹ️ 欄位已存在: {column_name}")
            
            # 驗證修復結果
            result = db.session.execute(columns_query).fetchall()
            updated_columns = {row[0]: row[1] for row in result}
            
            print(f"\n📋 修復後欄位: {list(updated_columns.keys())}")
            
            # 檢查是否所有必要欄位都存在
            required_columns = ['id', 'entry_type', 'account_id', 'amount', 'description', 
                              'entry_date', 'operator_id', 'from_account_id', 'to_account_id',
                              'profit_before', 'profit_after', 'profit_change']
            
            missing_columns = [col for col in required_columns if col not in updated_columns]
            
            if missing_columns:
                print(f"❌ 仍有缺少的欄位: {missing_columns}")
                return False
            else:
                print("✅ 所有必要欄位都存在")
                return True
                
    except Exception as e:
        print(f"❌ 修復欄位時發生錯誤: {e}")
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
                'account_id': 1,
                'amount': 0.01,
                'description': '欄位修復測試',
                'entry_date': '2024-01-01 12:00:00',
                'operator_id': 1,
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
    print("PostgreSQL 欄位修復腳本")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.environ.get('DATABASE_URL'):
        print("❌ 未設置 DATABASE_URL 環境變數")
        print("請在Render環境中設置DATABASE_URL")
        return False
    
    # 修復欄位
    if not fix_ledger_entries_columns():
        print("❌ 欄位修復失敗")
        return False
    
    # 測試修復結果
    if not test_ledger_entry_creation():
        print("❌ 測試失敗")
        return False
    
    print("\n🎉 PostgreSQL欄位修復成功！")
    print("✅ ledger_entries表格欄位已修復")
    print("✅ 銷帳功能現在應該可以正常工作")
    print("✅ 可以重新部署應用程式")
    
    return True

if __name__ == "__main__":
    main()
