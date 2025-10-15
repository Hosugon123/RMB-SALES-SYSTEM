#!/usr/bin/env python3
import sys
import os

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    
    with app.app_context():
        try:
            # 使用原始 SQL 添加欄位
            with db.engine.connect() as connection:
                # 檢查欄位是否存在並添加
                try:
                    connection.execute(db.text("ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT"))
                    print("✅ 添加 profit_before 欄位")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("ℹ️ profit_before 欄位已存在")
                    else:
                        print(f"⚠️ 添加 profit_before 欄位時發生錯誤: {e}")
                
                try:
                    connection.execute(db.text("ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT"))
                    print("✅ 添加 profit_after 欄位")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("ℹ️ profit_after 欄位已存在")
                    else:
                        print(f"⚠️ 添加 profit_after 欄位時發生錯誤: {e}")
                
                try:
                    connection.execute(db.text("ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT"))
                    print("✅ 添加 profit_change 欄位")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("ℹ️ profit_change 欄位已存在")
                    else:
                        print(f"⚠️ 添加 profit_change 欄位時發生錯誤: {e}")
                
                connection.commit()
                
            print("\n🎉 數據庫結構修復完成！")
            print("現在可以重新啟動應用程序並進行新的利潤提款測試。")
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")

except ImportError as e:
    print(f"❌ 無法導入 Flask 應用: {e}")
    print("請確保在正確的目錄中運行此腳本")
