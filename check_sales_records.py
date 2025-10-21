#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def check_sales_records():
    """檢查資料庫中的售出記錄"""
    db_path = 'instance/sales_system_v4.db'
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=== 檢查售出記錄 ===")
        print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 檢查SalesRecord表
        cursor.execute('''
            SELECT COUNT(*) FROM sales_records
        ''')
        sales_count = cursor.fetchone()[0]
        print(f"SalesRecord 總數: {sales_count}")
        
        if sales_count > 0:
            cursor.execute('''
                SELECT id, customer_id, rmb_amount, twd_amount, created_at
                FROM sales_records 
                ORDER BY created_at DESC
                LIMIT 5
            ''')
            sales_records = cursor.fetchall()
            
            print(f"最近的 {len(sales_records)} 筆售出記錄:")
            for record in sales_records:
                record_id, customer_id, rmb_amount, twd_amount, created_at = record
                print(f"  ID {record_id}: 客戶ID {customer_id}, RMB {rmb_amount}, TWD {twd_amount} ({created_at})")
        
        print()
        
        # 2. 檢查LedgerEntry中的PROFIT_EARNED記錄
        cursor.execute('''
            SELECT COUNT(*) FROM ledger_entries 
            WHERE entry_type = 'PROFIT_EARNED'
        ''')
        profit_earned_count = cursor.fetchone()[0]
        print(f"PROFIT_EARNED 記錄總數: {profit_earned_count}")
        
        if profit_earned_count > 0:
            cursor.execute('''
                SELECT id, amount, description, entry_date
                FROM ledger_entries 
                WHERE entry_type = 'PROFIT_EARNED'
                ORDER BY entry_date DESC
                LIMIT 5
            ''')
            profit_records = cursor.fetchall()
            
            print(f"最近的 {len(profit_records)} 筆利潤入庫記錄:")
            for record in profit_records:
                record_id, amount, description, entry_date = record
                print(f"  ID {record_id}: {amount} - {description} ({entry_date})")
        
        print()
        
        # 3. 檢查所有記錄類型
        cursor.execute('''
            SELECT entry_type, COUNT(*) as count
            FROM ledger_entries 
            GROUP BY entry_type
            ORDER BY count DESC
        ''')
        entry_types = cursor.fetchall()
        
        print("所有LedgerEntry記錄類型統計:")
        for entry_type, count in entry_types:
            print(f"  {entry_type}: {count} 筆")
        
        print()
        print("=== 分析結果 ===")
        if sales_count > 0 and profit_earned_count > 0:
            print("✅ 資料庫中同時存在售出記錄和利潤入庫記錄")
            print("   問題可能在於API查詢限制或排序邏輯")
        elif sales_count > 0 and profit_earned_count == 0:
            print("✅ 只有售出記錄，沒有利潤入庫記錄")
            print("   這是正常的，利潤入庫記錄可能在其他地方")
        elif sales_count == 0 and profit_earned_count > 0:
            print("⚠️ 只有利潤入庫記錄，沒有售出記錄")
            print("   這可能是問題所在")
        else:
            print("❌ 沒有任何記錄")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_sales_records()
