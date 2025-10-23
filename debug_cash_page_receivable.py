#!/usr/bin/env python3
"""
診斷現金頁面售出記錄的客戶應收帳款餘額變化數據
"""

import sqlite3
import sys
from datetime import datetime

def connect_db():
    """連接資料庫"""
    try:
        conn = sqlite3.connect('instance/sales_system_v4.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"資料庫連接失敗: {e}")
        return None

def check_sales_records(conn):
    """檢查銷售記錄"""
    cursor = conn.cursor()
    
    print("=== 檢查銷售記錄 ===")
    
    # 檢查最新的銷售記錄
    cursor.execute("""
        SELECT s.id, s.customer_id, s.rmb_amount, s.twd_amount, s.created_at,
               c.name as customer_name, c.total_receivables_twd
        FROM sales_records s
        LEFT JOIN customers c ON s.customer_id = c.id
        ORDER BY s.created_at DESC
        LIMIT 5
    """)
    
    sales = cursor.fetchall()
    print(f"找到 {len(sales)} 筆最新的銷售記錄:")
    
    for sale in sales:
        print(f"\n銷售記錄 ID: {sale['id']}")
        print(f"  客戶ID: {sale['customer_id']}")
        print(f"  客戶名稱: {sale['customer_name']}")
        print(f"  RMB金額: {sale['rmb_amount']}")
        print(f"  TWD金額: {sale['twd_amount']}")
        print(f"  創建時間: {sale['created_at']}")
        print(f"  客戶總應收帳款: {sale['total_receivables_twd']}")
        
        # 計算該筆銷售之前的應收帳款餘額
        cursor.execute("""
            SELECT SUM(twd_amount) as previous_total
            FROM sales_records 
            WHERE customer_id = ? AND created_at < ?
        """, (sale['customer_id'], sale['created_at']))
        
        result = cursor.fetchone()
        previous_total = result['previous_total'] or 0
        current_total = previous_total + sale['twd_amount']
        
        print(f"  計算結果:")
        print(f"    變動前: {previous_total:.2f}")
        print(f"    變動: +{sale['twd_amount']:.2f}")
        print(f"    變動後: {current_total:.2f}")

def check_customers(conn):
    """檢查客戶數據"""
    cursor = conn.cursor()
    
    print("\n=== 檢查客戶數據 ===")
    
    cursor.execute("""
        SELECT id, name, total_receivables_twd
        FROM customers
        ORDER BY total_receivables_twd DESC
    """)
    
    customers = cursor.fetchall()
    print(f"找到 {len(customers)} 個客戶:")
    
    for customer in customers:
        print(f"  客戶ID: {customer['id']}, 名稱: {customer['name']}, 應收帳款: {customer['total_receivables_twd']:.2f}")

def test_api_data():
    """測試API數據（如果服務器運行中）"""
    try:
        import requests
        response = requests.get('http://localhost:5000/api/cash_management/transactions?page=1', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== API數據檢查 ===")
            
            if data.get('status') == 'success':
                transactions = data.get('data', {}).get('transactions', [])
                sales_records = [t for t in transactions if t.get('type') == '售出']
                
                print(f"API返回 {len(transactions)} 筆交易記錄")
                print(f"其中 {len(sales_records)} 筆售出記錄")
                
                for i, sale in enumerate(sales_records):
                    print(f"\n售出記錄 {i+1}:")
                    print(f"  描述: {sale.get('description', 'N/A')}")
                    print(f"  客戶應收帳款餘額變化: {sale.get('customer_receivable_balance', 'N/A')}")
                    
                    if sale.get('customer_receivable_balance'):
                        balance = sale['customer_receivable_balance']
                        print(f"    變動前: {balance.get('before', 'N/A')}")
                        print(f"    變動: {balance.get('change', 'N/A')}")
                        print(f"    變動後: {balance.get('after', 'N/A')}")
                        print(f"    描述: {balance.get('description', 'N/A')}")
            else:
                print(f"API返回錯誤: {data.get('message', 'Unknown error')}")
        else:
            print(f"API請求失敗: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"API測試失敗: {e}")

def main():
    """主函數"""
    print("開始診斷現金頁面售出記錄的客戶應收帳款餘額變化數據...")
    print(f"診斷時間: {datetime.now()}")
    
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    try:
        # 檢查銷售記錄
        check_sales_records(conn)
        
        # 檢查客戶數據
        check_customers(conn)
        
        # 測試API數據
        test_api_data()
        
    except Exception as e:
        print(f"診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
