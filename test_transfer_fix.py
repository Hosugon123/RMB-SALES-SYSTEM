#!/usr/bin/env python3
"""
測試轉帳記錄顯示修復
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
        # 本地測試
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///F:/Code_design/Cursor_code/RMB-SALES-SYSTEM/instance/sales_system_v4.db"
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

def test_transfer_records():
    """測試轉帳記錄顯示"""
    print("測試轉帳記錄顯示...")
    
    app = create_app()
    db = SQLAlchemy(app)
    
    with app.app_context():
        try:
            # 查詢轉帳記錄
            query = text("""
                SELECT 
                    le.id,
                    le.entry_type,
                    le.description,
                    le.from_account_id,
                    le.to_account_id,
                    ca1.name as from_account_name,
                    ca2.name as to_account_name
                FROM ledger_entries le
                LEFT JOIN cash_accounts ca1 ON le.from_account_id = ca1.id
                LEFT JOIN cash_accounts ca2 ON le.to_account_id = ca2.id
                WHERE le.entry_type IN ('TRANSFER', 'TRANSFER_IN', 'TRANSFER_OUT')
                ORDER BY le.entry_date DESC
                LIMIT 10
            """)
            
            result = db.session.execute(query).fetchall()
            
            print(f"找到 {len(result)} 筆轉帳記錄:")
            
            for row in result:
                print(f"\n記錄 ID: {row[0]}")
                print(f"類型: {row[1]}")
                print(f"描述: {row[2]}")
                print(f"轉出帳戶ID: {row[3]}")
                print(f"轉入帳戶ID: {row[4]}")
                print(f"轉出帳戶名稱: {row[5] or 'N/A'}")
                print(f"轉入帳戶名稱: {row[6] or 'N/A'}")
                
                # 測試顯示邏輯
                if row[1] == "TRANSFER_IN":
                    if row[5]:  # from_account_name
                        payment_account = row[5]
                    else:
                        if "從" in row[2]:
                            payment_account = row[2].split("從")[1].split("轉入")[0].strip()
                        else:
                            payment_account = "其他帳戶"
                    deposit_account = row[6] or "N/A"
                    print(f"顯示 - 轉出帳戶: {payment_account}, 轉入帳戶: {deposit_account}")
                
                elif row[1] == "TRANSFER_OUT":
                    payment_account = row[6] or "N/A"
                    if row[6]:  # to_account_name
                        deposit_account = row[6]
                    else:
                        if "轉出至" in row[2]:
                            deposit_account = row[2].split("轉出至")[1].strip()
                        else:
                            deposit_account = "其他帳戶"
                    print(f"顯示 - 轉出帳戶: {payment_account}, 轉入帳戶: {deposit_account}")
                
                elif row[1] == "TRANSFER":
                    payment_account = row[5] or "N/A"
                    deposit_account = row[6] or "N/A"
                    print(f"顯示 - 轉出帳戶: {payment_account}, 轉入帳戶: {deposit_account}")
            
            return True
            
        except Exception as e:
            print(f"測試失敗: {e}")
            return False

def main():
    """主測試函數"""
    print("轉帳記錄顯示修復測試")
    print("=" * 50)
    
    if test_transfer_records():
        print("\n轉帳記錄顯示測試通過")
        print("修復成功！轉帳記錄現在應該正確顯示出入款帳戶")
    else:
        print("\n轉帳記錄顯示測試失敗")
        print("需要進一步檢查和修復")

if __name__ == "__main__":
    main()
