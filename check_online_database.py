#!/usr/bin/env python3
"""
檢查線上資料庫的轉帳記錄狀態
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def create_app():
    """創建Flask應用程式實例"""
    app = Flask(__name__)
    
    # 使用線上資料庫
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
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

def check_online_database():
    """檢查線上資料庫狀態"""
    print("檢查線上資料庫的轉帳記錄狀態...")
    
    app = create_app()
    if not app:
        return False
    
    db = SQLAlchemy(app)
    
    with app.app_context():
        try:
            # 檢查最近的轉帳記錄
            query = text("""
                SELECT 
                    le.id,
                    le.entry_type,
                    le.description,
                    le.from_account_id,
                    le.to_account_id,
                    ca1.name as from_account_name,
                    ca2.name as to_account_name,
                    le.entry_date
                FROM ledger_entries le
                LEFT JOIN cash_accounts ca1 ON le.from_account_id = ca1.id
                LEFT JOIN cash_accounts ca2 ON le.to_account_id = ca2.id
                WHERE le.entry_type IN ('TRANSFER_IN', 'TRANSFER_OUT')
                ORDER BY le.entry_date DESC
                LIMIT 10
            """)
            
            result = db.session.execute(query).fetchall()
            
            print(f"找到 {len(result)} 筆轉帳記錄:")
            
            for row in result:
                record_id, entry_type, description, from_account_id, to_account_id, from_account_name, to_account_name, entry_date = row
                print(f"\n記錄 ID: {record_id}")
                print(f"類型: {entry_type}")
                print(f"描述: {description}")
                print(f"轉出帳戶ID: {from_account_id}")
                print(f"轉入帳戶ID: {to_account_id}")
                print(f"轉出帳戶名稱: {from_account_name or 'N/A'}")
                print(f"轉入帳戶名稱: {to_account_name or 'N/A'}")
                print(f"日期: {entry_date}")
                
                # 檢查是否為NULL
                if from_account_id is None or to_account_id is None:
                    print("⚠️ 警告：此記錄的帳戶ID為NULL，需要修復")
                else:
                    print("✅ 此記錄的帳戶ID已正確設置")
            
            # 檢查資料庫表結構
            print(f"\n檢查資料庫表結構...")
            columns_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'ledger_entries' 
                AND table_schema = 'public'
                AND column_name IN ('from_account_id', 'to_account_id')
                ORDER BY column_name
            """)
            
            columns_result = db.session.execute(columns_query).fetchall()
            print("ledger_entries 表的相關欄位:")
            for col in columns_result:
                print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
            
            return True
            
        except Exception as e:
            print(f"檢查失敗: {e}")
            return False

def main():
    """主函數"""
    print("檢查線上資料庫狀態")
    print("=" * 50)
    
    if check_online_database():
        print("\n檢查完成")
    else:
        print("\n檢查失敗")

if __name__ == "__main__":
    main()
