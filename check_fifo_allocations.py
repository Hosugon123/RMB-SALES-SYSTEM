import sqlite3

# 連接正確的資料庫文件
conn = sqlite3.connect('instance/sales_system_v4.db')
cursor = conn.cursor()

# 檢查FIFO分配記錄
cursor.execute("SELECT COUNT(*) FROM fifo_sales_allocations")
count = cursor.fetchone()[0]
print(f"FIFO分配記錄數: {count}")

# 檢查最近的分配記錄
cursor.execute("""
    SELECT fsa.id, fsa.sales_record_id, fsa.allocated_rmb, fsa.allocation_date
    FROM fifo_sales_allocations fsa
    ORDER BY fsa.id DESC
    LIMIT 5
""")
allocations = cursor.fetchall()
print("最近的5筆FIFO分配記錄:")
for alloc in allocations:
    print(f"  分配ID: {alloc[0]}, 銷售記錄ID: {alloc[1]}, 分配RMB: {alloc[2]}, 時間: {alloc[3]}")

# 檢查是否有ID 10的分配記錄
cursor.execute("SELECT * FROM fifo_sales_allocations WHERE sales_record_id = 10")
alloc_10 = cursor.fetchone()
if alloc_10:
    print(f"找到ID 10的FIFO分配記錄: {alloc_10}")
else:
    print("沒有找到ID 10的FIFO分配記錄")

conn.close()
