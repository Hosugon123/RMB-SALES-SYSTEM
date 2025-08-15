import sqlite3

try:
    conn = sqlite3.connect("instance/sales_system_v4.db")
    cursor = conn.cursor()
    
    # 檢查 cash_logs 表結構
    cursor.execute("PRAGMA table_info(cash_logs)")
    columns = cursor.fetchall()
    
    print("cash_logs 表結構:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()
    print("✅ 數據庫連接成功")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
