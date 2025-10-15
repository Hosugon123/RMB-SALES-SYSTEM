#!/usr/bin/env python3
"""
修復數據庫結構 - 手動添加利潤詳細欄位
"""
import sqlite3
import os

def fix_database_schema():
    """修復數據庫結構，添加利潤詳細欄位"""
    
    # 數據庫文件路徑
    db_path = 'instance/sales_system.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查現有欄位...")
        
        # 檢查表結構
        cursor.execute("PRAGMA table_info(ledger_entries)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 現有欄位: {columns}")
        
        # 添加新欄位
        new_columns = [
            ('profit_before', 'FLOAT'),
            ('profit_after', 'FLOAT'), 
            ('profit_change', 'FLOAT')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"➕ 添加欄位: {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE ledger_entries ADD COLUMN {column_name} {column_type}")
            else:
                print(f"✅ 欄位已存在: {column_name}")
        
        # 提交更改
        conn.commit()
        
        # 驗證更改
        cursor.execute("PRAGMA table_info(ledger_entries)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 更新後欄位: {updated_columns}")
        
        # 檢查新欄位是否成功添加
        success = all(col in updated_columns for col, _ in new_columns)
        
        if success:
            print("✅ 數據庫結構修復成功！")
        else:
            print("❌ 數據庫結構修復失敗！")
            
        conn.close()
        return success
        
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ 開始修復數據庫結構...")
    success = fix_database_schema()
    
    if success:
        print("\n🎉 修復完成！現在可以重新啟動應用程序了。")
    else:
        print("\n💥 修復失敗，請檢查錯誤信息。")
