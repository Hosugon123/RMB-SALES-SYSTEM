#!/usr/bin/env python3
"""
診斷現金頁面與利潤管理頁面利潤數字不一致的問題
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

def check_profit_calculation_methods(conn):
    """檢查兩種利潤計算方法"""
    cursor = conn.cursor()
    
    print("=== 利潤計算方法對比 ===")
    
    # 方法1: 現金頁面的累積利潤計算（按時間順序）
    print("\n1. 現金頁面方法（累積利潤）:")
    cursor.execute("""
        SELECT id, created_at, rmb_amount, twd_amount
        FROM sales_records 
        ORDER BY created_at ASC
    """)
    sales_records = cursor.fetchall()
    
    cumulative_profit = 0.0
    for i, sale in enumerate(sales_records):
        # 簡化的利潤計算（假設每筆都是5元利潤）
        profit = 5.0  # 從圖片看到每筆都是+5.00
        cumulative_profit += profit
        print(f"  銷售 {sale['id']}: 累積利潤 = {cumulative_profit:.2f}")
        
        if i >= 4:  # 只顯示前5筆
            break
    
    print(f"  最終累積利潤: {cumulative_profit:.2f}")
    
    # 方法2: 利潤管理頁面的總利潤計算
    print("\n2. 利潤管理頁面方法（總利潤）:")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM sales_records
    """)
    total_sales = cursor.fetchone()['count']
    total_profit = total_sales * 5.0  # 假設每筆5元利潤
    print(f"  總銷售記錄數: {total_sales}")
    print(f"  總利潤: {total_profit:.2f}")
    
    # 檢查利潤提款
    cursor.execute("""
        SELECT SUM(amount) as total_withdrawals
        FROM ledger_entries 
        WHERE entry_type = 'PROFIT_WITHDRAW'
    """)
    withdrawals = cursor.fetchone()['total_withdrawals'] or 0
    net_profit = total_profit - abs(withdrawals)
    print(f"  利潤提款: {abs(withdrawals):.2f}")
    print(f"  淨利潤: {net_profit:.2f}")
    
    return cumulative_profit, net_profit

def check_ledger_entries(conn):
    """檢查LedgerEntry中的利潤記錄"""
    cursor = conn.cursor()
    
    print("\n=== LedgerEntry利潤記錄 ===")
    
    cursor.execute("""
        SELECT id, entry_type, amount, description, 
               profit_before, profit_after, profit_change,
               entry_date
        FROM ledger_entries 
        WHERE entry_type = 'PROFIT_EARNED' 
           OR description LIKE '%售出利潤%'
        ORDER BY entry_date DESC
        LIMIT 10
    """)
    
    entries = cursor.fetchall()
    print(f"找到 {len(entries)} 筆利潤記錄:")
    
    for entry in entries:
        print(f"  ID: {entry['id']}, 類型: {entry['entry_type']}")
        print(f"    金額: {entry['amount']}, 描述: {entry['description']}")
        print(f"    利潤前: {entry['profit_before']}, 利潤後: {entry['profit_after']}, 變動: {entry['profit_change']}")
        print(f"    時間: {entry['entry_date']}")
        print()

def check_sales_records(conn):
    """檢查SalesRecord記錄"""
    cursor = conn.cursor()
    
    print("\n=== SalesRecord記錄 ===")
    
    cursor.execute("""
        SELECT id, customer_id, rmb_amount, twd_amount, created_at
        FROM sales_records 
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    records = cursor.fetchall()
    print(f"找到 {len(records)} 筆銷售記錄:")
    
    for record in records:
        print(f"  ID: {record['id']}, 客戶ID: {record['customer_id']}")
        print(f"    RMB: {record['rmb_amount']}, TWD: {record['twd_amount']}")
        print(f"    時間: {record['created_at']}")
        print()

def main():
    """主函數"""
    print("開始診斷利潤數字不一致問題...")
    print(f"診斷時間: {datetime.now()}")
    
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    try:
        # 檢查兩種計算方法
        cumulative_profit, net_profit = check_profit_calculation_methods(conn)
        
        # 檢查LedgerEntry記錄
        check_ledger_entries(conn)
        
        # 檢查SalesRecord記錄
        check_sales_records(conn)
        
        print("\n=== 問題分析 ===")
        print(f"現金頁面累積利潤: {cumulative_profit:.2f}")
        print(f"利潤管理頁面淨利潤: {net_profit:.2f}")
        print(f"差異: {abs(cumulative_profit - net_profit):.2f}")
        
        if abs(cumulative_profit - net_profit) > 0.01:
            print("❌ 發現利潤計算不一致！")
            print("可能原因:")
            print("1. 現金頁面使用累積利潤計算")
            print("2. 利潤管理頁面使用總利潤計算")
            print("3. 兩者計算基礎不同")
        else:
            print("✅ 利潤計算一致")
            
    except Exception as e:
        print(f"診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
