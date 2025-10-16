import sqlite3
import sys
import os

def fix_database():
    db_path = 'instance/sales_system.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查現有欄位...")
        cursor.execute("PRAGMA table_info(ledger_entries)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"現有欄位: {columns}")
        
        # 添加新欄位
        new_columns = ['profit_before', 'profit_after', 'profit_change']
        
        for column in new_columns:
            if column not in columns:
                print(f"➕ 添加欄位: {column}")
                cursor.execute(f"ALTER TABLE ledger_entries ADD COLUMN {column} FLOAT")
            else:
                print(f"✅ 欄位已存在: {column}")
        
        conn.commit()
        
        # 驗證
        cursor.execute("PRAGMA table_info(ledger_entries)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"更新後欄位: {updated_columns}")
        
        conn.close()
        print("✅ 數據庫修復完成！")
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False

if __name__ == "__main__":
    fix_database()


