import sqlite3

conn = sqlite3.connect('./instance/sales_system_v4.db')
cursor = conn.cursor()

print("=== 持有人列表 ===")
cursor.execute("SELECT id, name FROM holders")
holders = cursor.fetchall()
for holder in holders:
    print(f"ID: {holder[0]}, 名稱: {holder[1]}")

print("\n=== RMB帳戶列表 ===")
cursor.execute("SELECT id, name, currency, holder_id FROM cash_accounts WHERE currency='RMB'")
rmb_accounts = cursor.fetchall()
for account in rmb_accounts:
    print(f"ID: {account[0]}, 名稱: {account[1]}, 持有人ID: {account[3]}")

print("\n=== 所有帳戶列表 ===")
cursor.execute("""
    SELECT ca.id, ca.name, ca.currency, h.name as holder_name
    FROM cash_accounts ca
    LEFT JOIN holders h ON ca.holder_id = h.id
    ORDER BY h.name, ca.currency
""")
all_accounts = cursor.fetchall()
for account in all_accounts:
    acc_id, acc_name, currency, holder = account
    holder_display = holder if holder else "N/A"
    print(f"ID: {acc_id}, 持有人: {holder_display}, 帳戶: {acc_name}, 幣別: {currency}")

conn.close()
