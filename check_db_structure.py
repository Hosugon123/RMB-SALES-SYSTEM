import sqlite3

conn = sqlite3.connect('./instance/sales_system_v4.db')
cursor = conn.cursor()

print("=== 所有表格 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\n=== FIFO庫存表格結構 ===")
try:
    cursor.execute("PRAGMA table_info(fifo_inventory)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except:
    print("FIFO庫存表格不存在")

print("\n=== 買入記錄表格結構 ===")
try:
    cursor.execute("PRAGMA table_info(purchase_records)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except:
    print("買入記錄表格不存在")

print("\n=== 檢查FIFO庫存資料 ===")
try:
    cursor.execute("SELECT COUNT(*) FROM fifo_inventory")
    count = cursor.fetchone()[0]
    print(f"FIFO庫存記錄數: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM fifo_inventory LIMIT 3")
        records = cursor.fetchall()
        for i, record in enumerate(records):
            print(f"記錄 {i+1}: {record}")
except:
    print("無法查詢FIFO庫存")

conn.close()
