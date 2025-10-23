import sqlite3

# 連接正確的資料庫文件
conn = sqlite3.connect('instance/sales_system_v4.db')
cursor = conn.cursor()

# 檢查SalesRecord表
cursor.execute("SELECT COUNT(*) FROM sales_records")
count = cursor.fetchone()[0]
print(f"SalesRecord表記錄數: {count}")

# 檢查最近的記錄
cursor.execute("SELECT id, customer_id, rmb_amount, created_at FROM sales_records ORDER BY id DESC LIMIT 5")
records = cursor.fetchall()
print("最近的5筆記錄:")
for record in records:
    print(f"  ID: {record[0]}, 客戶ID: {record[1]}, RMB: {record[2]}, 時間: {record[3]}")

conn.close()