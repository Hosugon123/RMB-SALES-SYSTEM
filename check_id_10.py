import sqlite3

# 連接正確的資料庫文件
conn = sqlite3.connect('instance/sales_system_v4.db')
cursor = conn.cursor()

# 檢查ID 10是否存在
cursor.execute("SELECT * FROM sales_records WHERE id = 10")
record = cursor.fetchone()

if record:
    print(f"找到ID 10的記錄: {record}")
else:
    print("沒有找到ID 10的記錄")

# 檢查所有ID
cursor.execute("SELECT id FROM sales_records ORDER BY id")
ids = [row[0] for row in cursor.fetchall()]
print(f"所有SalesRecord ID: {ids}")

# 檢查是否有ID 10
if 10 in ids:
    print("ID 10確實存在於資料庫中")
else:
    print("ID 10不存在於資料庫中")

conn.close()
