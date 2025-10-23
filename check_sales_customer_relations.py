#!/usr/bin/env python3
"""
檢查銷售記錄的客戶關聯
"""

import sqlite3
import os

def check_sales_customer_relations():
    """檢查銷售記錄的客戶關聯"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"錯誤: 資料庫文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("銷售記錄客戶關聯檢查")
        print("=" * 50)
        
        # 1. 檢查銷售記錄的客戶關聯
        print("1. 檢查銷售記錄的客戶關聯...")
        cursor.execute("""
            SELECT s.id, s.customer_id, s.twd_amount, s.rmb_amount, s.created_at,
                   c.name as customer_name
            FROM sales_records s
            LEFT JOIN customers c ON s.customer_id = c.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        print(f"   查詢到 {len(records)} 筆銷售記錄")
        
        no_customer_count = 0
        valid_customer_count = 0
        
        for record in records:
            sales_id, customer_id, twd_amount, rmb_amount, created_at, customer_name = record
            if customer_id is None or customer_name is None:
                no_customer_count += 1
                print(f"   [ERROR] 銷售記錄 {sales_id}: 沒有客戶關聯 (customer_id: {customer_id})")
            else:
                valid_customer_count += 1
                print(f"   [OK] 銷售記錄 {sales_id}: 客戶 {customer_name} (ID: {customer_id})")
        
        print(f"\n   統計:")
        print(f"   有效客戶關聯: {valid_customer_count}")
        print(f"   無客戶關聯: {no_customer_count}")
        
        # 2. 檢查客戶表
        print("\n2. 檢查客戶表...")
        cursor.execute("SELECT id, name FROM customers")
        customers = cursor.fetchall()
        print(f"   客戶總數: {len(customers)}")
        
        for customer in customers:
            print(f"   客戶 ID: {customer[0]}, 姓名: {customer[1]}")
        
        # 3. 檢查銷售記錄的RMB帳戶關聯
        print("\n3. 檢查銷售記錄的RMB帳戶關聯...")
        cursor.execute("""
            SELECT s.id, s.rmb_account_id, s.twd_amount, s.rmb_amount,
                   ca.name as rmb_account_name
            FROM sales_records s
            LEFT JOIN cash_accounts ca ON s.rmb_account_id = ca.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """)
        
        rmb_records = cursor.fetchall()
        no_rmb_account_count = 0
        valid_rmb_account_count = 0
        
        for record in rmb_records:
            sales_id, rmb_account_id, twd_amount, rmb_amount, rmb_account_name = record
            if rmb_account_id is None or rmb_account_name is None:
                no_rmb_account_count += 1
                print(f"   [ERROR] 銷售記錄 {sales_id}: 沒有RMB帳戶關聯 (rmb_account_id: {rmb_account_id})")
            else:
                valid_rmb_account_count += 1
                print(f"   [OK] 銷售記錄 {sales_id}: RMB帳戶 {rmb_account_name} (ID: {rmb_account_id})")
        
        print(f"\n   統計:")
        print(f"   有效RMB帳戶關聯: {valid_rmb_account_count}")
        print(f"   無RMB帳戶關聯: {no_rmb_account_count}")
        
        # 4. 檢查現金帳戶表
        print("\n4. 檢查現金帳戶表...")
        cursor.execute("SELECT id, name, currency FROM cash_accounts")
        accounts = cursor.fetchall()
        print(f"   現金帳戶總數: {len(accounts)}")
        
        for account in accounts:
            print(f"   帳戶 ID: {account[0]}, 名稱: {account[1]}, 幣別: {account[2]}")
        
        # 5. 檢查操作者關聯
        print("\n5. 檢查銷售記錄的操作者關聯...")
        cursor.execute("""
            SELECT s.id, s.operator_id, s.created_at,
                   u.username as operator_name
            FROM sales_records s
            LEFT JOIN user u ON s.operator_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """)
        
        operator_records = cursor.fetchall()
        no_operator_count = 0
        valid_operator_count = 0
        
        for record in operator_records:
            sales_id, operator_id, created_at, operator_name = record
            if operator_id is None or operator_name is None:
                no_operator_count += 1
                print(f"   [ERROR] 銷售記錄 {sales_id}: 沒有操作者關聯 (operator_id: {operator_id})")
            else:
                valid_operator_count += 1
                print(f"   [OK] 銷售記錄 {sales_id}: 操作者 {operator_name} (ID: {operator_id})")
        
        print(f"\n   統計:")
        print(f"   有效操作者關聯: {valid_operator_count}")
        print(f"   無操作者關聯: {no_operator_count}")
        
        # 6. 總結
        print("\n" + "=" * 50)
        print("問題診斷總結")
        print("=" * 50)
        
        if no_customer_count > 0:
            print(f"[ERROR] 發現 {no_customer_count} 筆銷售記錄沒有客戶關聯")
            print("這會導致現金管理API中的 'if s.customer:' 條件失敗")
            print("建議: 檢查銷售記錄創建時是否正確設置了 customer_id")
        
        if no_rmb_account_count > 0:
            print(f"[WARNING] 發現 {no_rmb_account_count} 筆銷售記錄沒有RMB帳戶關聯")
            print("這可能導致現金管理API中的處理邏輯問題")
        
        if no_operator_count > 0:
            print(f"[WARNING] 發現 {no_operator_count} 筆銷售記錄沒有操作者關聯")
            print("這可能導致現金管理API中的處理邏輯問題")
        
        if no_customer_count == 0 and no_rmb_account_count == 0 and no_operator_count == 0:
            print("[OK] 所有銷售記錄都有正確的關聯")
            print("問題可能在於現金管理API的其他處理邏輯")
        
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    check_sales_customer_relations()
