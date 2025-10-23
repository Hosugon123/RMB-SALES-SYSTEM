import sqlite3

# 連接正確的資料庫文件
conn = sqlite3.connect('instance/sales_system_v4.db')
cursor = conn.cursor()

# 創建profit_transactions表
create_table_sql = """
CREATE TABLE IF NOT EXISTS profit_transactions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    balance_before FLOAT NOT NULL,
    balance_after FLOAT NOT NULL,
    related_transaction_id INTEGER,
    related_transaction_type VARCHAR(50),
    description VARCHAR(200),
    note TEXT,
    operator_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (account_id) REFERENCES cash_accounts (id),
    FOREIGN KEY (operator_id) REFERENCES user (id)
)
"""

try:
    cursor.execute(create_table_sql)
    conn.commit()
    print("profit_transactions表創建成功！")
    
    # 驗證表是否創建成功
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profit_transactions'")
    result = cursor.fetchone()
    if result:
        print("表創建驗證成功")
    else:
        print("表創建驗證失敗")
        
except Exception as e:
    print(f"創建表時發生錯誤: {e}")
finally:
    conn.close()
