#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
雲端資料庫結構修復腳本
用於 Render 雲端環境
"""

import os
import sys

# 設置環境變數
os.environ['FLASK_APP'] = 'app.py'

def fix_cloud_database():
    """修復雲端資料庫結構"""
    
    try:
        from app import app, db
        from sqlalchemy import text
        
        with app.app_context():
            print("開始修復雲端資料庫結構...")
            
            # 檢查是否為 PostgreSQL
            if 'postgresql' not in str(db.engine.url):
                print("非 PostgreSQL 資料庫，跳過修復")
                return True
            
            print("檢測到 PostgreSQL 資料庫")
            
            try:
                # 檢查欄位是否存在
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'ledger_entries' 
                    AND column_name IN ('profit_before', 'profit_after', 'profit_change')
                """)).fetchall()
                
                existing_columns = [row[0] for row in result]
                print(f"現有欄位: {existing_columns}")
                
                # 添加缺少的欄位
                columns_to_add = [
                    ('profit_before', 'REAL'),
                    ('profit_after', 'REAL'),
                    ('profit_change', 'REAL')
                ]
                
                for column_name, column_type in columns_to_add:
                    if column_name not in existing_columns:
                        try:
                            db.session.execute(text(f"""
                                ALTER TABLE ledger_entries 
                                ADD COLUMN {column_name} {column_type}
                            """))
                            print(f"SUCCESS: 添加欄位 {column_name}")
                        except Exception as e:
                            print(f"ERROR: 添加欄位 {column_name} 失敗: {e}")
                    else:
                        print(f"INFO: 欄位 {column_name} 已存在")
                
                # 提交變更
                db.session.commit()
                print("SUCCESS: 資料庫結構修復完成")
                return True
                
            except Exception as e:
                print(f"ERROR: 修復過程中出錯: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"ERROR: 無法連接資料庫: {e}")
        return False

if __name__ == "__main__":
    print("=== 雲端資料庫結構修復工具 ===")
    success = fix_cloud_database()
    
    if success:
        print("\n🎉 修復完成！")
    else:
        print("\n❌ 修復失敗，請檢查錯誤訊息。")
