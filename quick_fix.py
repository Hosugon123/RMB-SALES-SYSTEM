import sqlite3

# 連接到數據庫
conn = sqlite3.connect('instance/sales_system.db')
cursor = conn.cursor()

# 添加新欄位
try:
    cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT')
    print('Added profit_before column')
except:
    print('profit_before column already exists')

try:
    cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT')
    print('Added profit_after column')
except:
    print('profit_after column already exists')

try:
    cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT')
    print('Added profit_change column')
except:
    print('profit_change column already exists')

conn.commit()
conn.close()
print('Database schema fixed successfully!')
