#!/usr/bin/env python3
"""
修復舊的轉帳記錄，為TRANSFER_IN和TRANSFER_OUT記錄設置正確的from_account_id和to_account_id
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

def fix_old_transfer_records():
    """修復舊的轉帳記錄"""
    print("修復舊的轉帳記錄...")
    
    app = create_app()
    db = SQLAlchemy(app)
    
    with app.app_context():
        try:
            # 查詢需要修復的記錄
            query = text("""
                SELECT 
                    le.id,
                    le.entry_type,
                    le.description,
                    le.account_id,
                    ca.name as account_name
                FROM ledger_entries le
                LEFT JOIN cash_accounts ca ON le.account_id = ca.id
                WHERE le.entry_type IN ('TRANSFER_IN', 'TRANSFER_OUT')
                AND (le.from_account_id IS NULL OR le.to_account_id IS NULL)
                ORDER BY le.entry_date DESC
            """)
            
            result = db.session.execute(query).fetchall()
            
            print(f"找到 {len(result)} 筆需要修復的記錄:")
            
            for row in result:
                record_id, entry_type, description, account_id, account_name = row
                print(f"\n記錄 ID: {record_id}")
                print(f"類型: {entry_type}")
                print(f"描述: {description}")
                print(f"帳戶ID: {account_id}")
                print(f"帳戶名稱: {account_name}")
                
                # 根據描述和類型推斷轉出/轉入帳戶
                from_account_id = None
                to_account_id = None
                
                if entry_type == "TRANSFER_IN":
                    # 轉入記錄：從描述中提取轉出帳戶
                    if "從" in description and "轉入" in description:
                        from_account_name = description.split("從")[1].split("轉入")[0].strip()
                        # 查詢轉出帳戶ID
                        from_query = text("SELECT id FROM cash_accounts WHERE name = :name")
                        from_result = db.session.execute(from_query, {"name": from_account_name}).fetchone()
                        if from_result:
                            from_account_id = from_result[0]
                            print(f"找到轉出帳戶: {from_account_name} (ID: {from_account_id})")
                        else:
                            print(f"未找到轉出帳戶: {from_account_name}")
                    
                    to_account_id = account_id
                    
                elif entry_type == "TRANSFER_OUT":
                    # 轉出記錄：從描述中提取轉入帳戶
                    if "轉出至" in description:
                        to_account_name = description.split("轉出至")[1].strip()
                        # 查詢轉入帳戶ID
                        to_query = text("SELECT id FROM cash_accounts WHERE name = :name")
                        to_result = db.session.execute(to_query, {"name": to_account_name}).fetchone()
                        if to_result:
                            to_account_id = to_result[0]
                            print(f"找到轉入帳戶: {to_account_name} (ID: {to_account_id})")
                        else:
                            print(f"未找到轉入帳戶: {to_account_name}")
                    
                    from_account_id = account_id
                
                # 更新記錄
                if from_account_id is not None or to_account_id is not None:
                    update_query = text("""
                        UPDATE ledger_entries 
                        SET from_account_id = :from_account_id, to_account_id = :to_account_id
                        WHERE id = :record_id
                    """)
                    
                    db.session.execute(update_query, {
                        "from_account_id": from_account_id,
                        "to_account_id": to_account_id,
                        "record_id": record_id
                    })
                    
                    print(f"更新記錄 {record_id}: from_account_id={from_account_id}, to_account_id={to_account_id}")
                else:
                    print(f"無法修復記錄 {record_id}: 無法從描述中提取帳戶信息")
            
            # 提交更改
            db.session.commit()
            print(f"\n修復完成！共處理 {len(result)} 筆記錄")
            
            return True
            
        except Exception as e:
            print(f"修復失敗: {e}")
            db.session.rollback()
            return False

def main():
    """主函數"""
    print("修復舊的轉帳記錄")
    print("=" * 50)
    
    if fix_old_transfer_records():
        print("\n修復成功！")
        print("現在轉帳記錄應該正確顯示出入款帳戶")
    else:
        print("\n修復失敗")
        print("需要手動檢查和修復")

if __name__ == "__main__":
    main()
