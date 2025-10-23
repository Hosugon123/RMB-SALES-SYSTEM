import sqlite3

# 連接正確的資料庫文件
conn = sqlite3.connect('instance/sales_system_v4.db')
cursor = conn.cursor()

# 檢查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"資料庫中的所有表: {tables}")

# 檢查是否有profit_transactions表
if 'profit_transactions' in tables:
    print("profit_transactions表存在")
    cursor.execute("SELECT COUNT(*) FROM profit_transactions")
    count = cursor.fetchone()[0]
    print(f"profit_transactions表記錄數: {count}")
else:
    print("profit_transactions表不存在！")

conn.close()
